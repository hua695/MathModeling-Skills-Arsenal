#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
memory/blueprint_retrieval.py — Math Blueprint 检索层

Problem Fingerprint → 匹配 blueprint（problem_type 为主键，子类型/关键词为辅）
→ 输出 match_confidence + 注入骨架（可裁剪 steps）

执行约束：按 problem_type 强制检索；低置信度只作为参考；同题型按 fingerprint 选择变体；注入的是可裁剪的建议骨架，不是填空模板。

用法:
    from memory.blueprint_retrieval import retrieve_blueprint
    bp = retrieve_blueprint({'primary': '优化', 'keywords': ['调度', '时间窗'],
                             'sub_type': '调度'})
"""
import os
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

try:
    import yaml
except ImportError:
    yaml = None

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP_DIR = os.path.join(SKILL, 'memory', 'math_blueprints')

# 检索参数
CONFIDENCE_INJECT = 0.5     # ≥0.5 强制注入；<0.5 仅"参考"
CONFIDENCE_REFERENCE = 0.2  # ≥0.2 给参考；<0.2 不推荐

# problem_type 主键别名（fingerprint.primary → blueprint_id）
_TYPE_ALIAS = {
    '优化': 'MB-001', '规划': 'MB-001', '组合优化': 'MB-001',
    '整数规划': 'MB-001', '运筹': 'MB-001',
    '机理': 'MB-002', '物理': 'MB-002', '微分方程': 'MB-002',
    '偏微分方程': 'MB-002', '物理机理': 'MB-002', '传热': 'MB-002',
    '预测': 'MB-003', '时序': 'MB-003', '回归': 'MB-003',
    '时间序列': 'MB-003', '机器学习': 'MB-003', '统计预测': 'MB-003',
    '聚类': 'MB-004', '分组': 'MB-004', '聚类分组': 'MB-004',
    '关联': 'MB-005', '因果': 'MB-005', '关联因果': 'MB-005', '相关分析': 'MB-005',
    '博弈': 'MB-006', '策略': 'MB-006', '博弈策略': 'MB-006', '均衡': 'MB-006',
    '几何': 'MB-007', '运动学': 'MB-007', '几何运动': 'MB-007', '运动': 'MB-007',
    '生态': 'MB-008', '生态系统': 'MB-008', '动态系统': 'MB-008', '种群': 'MB-008',
}

# fingerprint 细节 → 加分（用于 variant 匹配与置信度微调）
_KEYWORDS_BONUS = {
    # MB-001 优化
    '调度': 0.15, '时间窗': 0.10, '排样': 0.10, '选址': 0.10, '路径': 0.10,
    '分配': 0.08, '0-1': 0.10, '整数': 0.10, '多目标': 0.08, '容量': 0.08,
    # MB-002 机理
    '温度': 0.12, '传热': 0.12, '守恒': 0.12, '扩散': 0.12, '方程': 0.10,
    '稳态': 0.08, '仿真': 0.06,
    # MB-003 预测
    '时序': 0.12, '时间序列': 0.12, '趋势': 0.10, '周期': 0.10, '滞后': 0.10,
    'RMSE': 0.08, 'ARIMA': 0.10, 'LSTM': 0.10, '平滑': 0.08,
    # MB-004 聚类
    '簇': 0.10, '轮廓系数': 0.12, 'K-Means': 0.10, 'DBSCAN': 0.12, '相似度': 0.08,
    # MB-005 关联因果
    '相关系数': 0.12, '偏相关': 0.12, '互信息': 0.10, '格兰杰': 0.12, '显著性': 0.08,
    # MB-006 博弈
    '纳什': 0.12, 'Nash': 0.12, '收益矩阵': 0.12, '均衡': 0.10, '混合策略': 0.10,
    # MB-007 几何运动
    '螺线': 0.12, '曲率': 0.10, '坐标变换': 0.10, '反射': 0.10, '覆盖宽度': 0.10,
    # MB-008 生态动态
    '承载力': 0.12, '种群': 0.10, 'Lotka': 0.12, '平衡点': 0.10, '稳定性': 0.08,
}

# 蓝图内置 step 标记（用于注入时标注可裁剪性）——读取时若 YAML 缺失自动补
STEP_MARKERS = {
    'required': '必选',
    'optional': '可选',
    'alternative': '替代',
}


def _load_blueprint(path):
    """读取单条 blueprint YAML；yaml 不可用时返回 None"""
    if yaml is None:
        return None
    try:
        with open(path, encoding='utf-8') as f:
            return yaml.safe_load(f)
    except OSError as e:
        print(f'[blueprint_retrieval] 读取失败 {path}: {e}', file=sys.stderr)
        return None
    except yaml.YAMLError as e:
        print(f'[blueprint_retrieval] YAML 解析失败 {path}: {e}', file=sys.stderr)
        return None


def _load_all():
    """加载 math_blueprints/ 下所有 *.yaml，按 blueprint_id 索引"""
    bps = {}
    if not os.path.isdir(BP_DIR):
        return bps
    for fn in sorted(os.listdir(BP_DIR)):
        if fn.endswith('.yaml') and fn.startswith('MB-'):
            bp = _load_blueprint(os.path.join(BP_DIR, fn))
            if bp and bp.get('blueprint_id'):
                bps[bp['blueprint_id']] = bp
    return bps


def _score(fingerprint, bp):
    """蓝图匹配分：主键命中为基分，关键词/子类型命中叠加（0~1.2 量级）"""
    primary = (fingerprint.get('primary') or '').lower()
    bp_type = (bp.get('problem_type') or '').lower()
    score = 0.0

    # 主键：fingerprint.primary 别名命中蓝图 problem_type
    alias_hit = None
    for k, v in _TYPE_ALIAS.items():
        if k.lower() == primary:
            alias_hit = v
            break
    if alias_hit == bp.get('blueprint_id'):
        score += 0.7
    elif primary and primary in bp_type:
        score += 0.6

    # 子类型：fingerprint.sub_type 与 blueprint variants 匹配
    sub = (fingerprint.get('sub_type') or '').lower()
    variants = bp.get('variants') or []
    if sub:
        for v in variants:
            if sub in (v.get('trigger') or {}).get('sub_type', '').lower() or \
               sub in str(v.get('name', '')).lower():
                score += 0.2
                break

    # 关键词加分（仅当关键词命中蓝图文本才加分；bonus 表用于题型特征词微调）
    kws = [k.lower() for k in (fingerprint.get('keywords') or [])]
    text = (bp.get('summary') or '') + ' ' + (bp.get('problem_type') or '')
    text = text.lower()
    for kw in kws:
        if not kw:
            continue
        if kw in text:
            score += 0.1
            bonus = _KEYWORDS_BONUS.get(kw)
            if bonus:
                score += bonus
    return min(score, 1.2)


def _confidence_of(score):
    """把原始分映射到 0~1 置信度（评审：0.5 为注入线）"""
    return max(0.0, min(1.0, score / 1.2))


def retrieve_blueprint(fingerprint, top=1):
    """按 fingerprint 检索 blueprint。

    返回:
        {
          'matched': bool,          # 是否命中（≥CONFIDENCE_INJECT）
          'blueprint_id': str|None,
          'match_confidence': float,
          'mode': 'inject' | 'reference' | 'none',
          'blueprint': dict|None,   # 完整蓝图（注入用）
          'candidates': [ {blueprint_id, match_confidence}, ... ],
        }
    """
    bps = _load_all()
    if not bps:
        return {'matched': False, 'blueprint_id': None, 'match_confidence': 0.0,
                'mode': 'none', 'blueprint': None, 'candidates': [],
                'note': 'math_blueprints 目录为空或 yaml 不可用'}

    scored = []
    for bp_id, bp in bps.items():
        s = _score(fingerprint, bp)
        scored.append((bp_id, s, bp))
    scored.sort(key=lambda t: -t[1])

    top_id, top_score, top_bp = scored[0]
    conf = _confidence_of(top_score)
    if conf >= CONFIDENCE_INJECT:
        mode = 'inject'
    elif conf >= CONFIDENCE_REFERENCE:
        mode = 'reference'
    else:
        mode = 'none'

    candidates = [
        {'blueprint_id': i, 'match_confidence': round(_confidence_of(s), 3)}
        for i, s, _ in scored[:top]
    ]
    return {
        'matched': mode == 'inject',
        'blueprint_id': top_id if mode != 'none' else None,
        'match_confidence': round(conf, 3),
        'mode': mode,
        'blueprint': top_bp if mode == 'inject' else None,
        'candidates': candidates,
    }


def format_skeleton(bp, level='L1', alternatives=None):
    """把蓝图 steps 格式化为注入文本（含可裁剪标记，供 solving 阶段使用）。

    输出是"建议目录"而非"填空模板"——模型按 fingerprint 增删 step。

    level:
      L1（默认，高能力/正常场景）: 只含核心 steps（required=True）+ 关键符号，不限制验证角度
      L2（退化/低能力场景）: 完整 steps（含 optional）+ 详细推导提示 + anti-anchor 检查
    alternatives（多蓝图竞争）: 可选，其他可行路线提示（如物理机理/信号处理/优化反演）
    """
    if not bp:
        return ''
    steps = bp.get('steps', [])
    if level == 'L1':
        steps = [s for s in steps if s.get('required', True)]
    lines = [
        f"【数学推理脚手架 {bp.get('blueprint_id')}·{level}】{bp.get('problem_type', '')}",
        f"数学化核心矛盾：{bp.get('summary', '')}",
        '',
        "建议建模目录（required=必选；optional=可选；alternative=多选一）：",
    ]
    for s in steps:
        mark = '必选' if s.get('required', True) else '可选'
        alt = ''
        if s.get('alternative'):
            alt = f"（替代：{' / '.join(s['alternative'])}）"
        lines.append(f"  - [{mark}{alt}] Step{s.get('step', '?')} {s.get('name', '')}: {s.get('template', '')}")
    lines.append('')
    lines.append('现实→数学映射（abstraction_map）：')
    am = bp.get('abstraction_map', {})
    for key in ('objects', 'relationships', 'decision'):
        for item in am.get(key, []):
            lines.append(f"  - {key}：{item}")
    lines.append('')
    lines.append('模型选择逻辑（为什么选这个模型；仅参考，具体模型名以 FD/SD 库检索为准，蓝图不锁定）：')
    for rule in bp.get('selection_logic', []):
        lines.append(f"  - if {rule.get('if', {})} → {rule.get('choose', '')}：{rule.get('because', '')}")
    if alternatives:
        lines.append('')
        lines.append('备选路线（可选择一条或组合使用）：')
        for alt in alternatives:
            lines.append(f"  - 路线：{alt}")
    lines.append('')
    lines.append('理论性质 checklist（required 项缺则需说明理由）：')
    for tc in bp.get('theory_checks', []):
        if level == 'L1' and not tc.get('required', True):
            continue
        lines.append(f"  - [{('必选' if tc.get('required', True) else '可选')}] {tc.get('name', '')}：{tc.get('note', '')}")
    lines.append('')
    lines.append('可读性约束：')
    for rg in bp.get('readability_guard', []):
        lines.append(f"  - {rg}")
    if level == 'L2':
        lines.append('')
        lines.append('【反锚检查：防止过度套用蓝图】')
        lines.append('  - 对上述每个公式做量纲检查（每项单位一致）与退化极限验证（参数→0/∞/对称应复现已知结果）')
        lines.append('  - 指出该蓝图在此题上可能失效的三个条件（如：折射率色散显著时 F 判据需修正）')
        lines.append('  - 检查公式口径一致性：公式中符号的定义与后续数值/表格使用必须同口径（如强度 vs 幅度）')
        lines.append('  - 至少一处显式写出“将式(X)代入式(Y)得”，表达公式间推导关系')
        lines.append('    显式表达公式间推导关系，禁止全部公式只作孤立定义或关系说明')
    return '\n'.join(lines)


# ---- 自检 ----
if __name__ == '__main__':
    import sys
    fp = {
        'primary': sys.argv[1] if len(sys.argv) > 1 else '优化',
        'keywords': sys.argv[2:] or ['调度', '时间窗'],
    }
    r = retrieve_blueprint(fp)
    print(f"mode={r['mode']} blueprint={r['blueprint_id']} conf={r['match_confidence']}")
    for c in r['candidates']:
        print(f"  candidate {c}")
    if r['mode'] == 'inject':
        print()
        print(format_skeleton(r['blueprint']))
