#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_math_behavior.py — 数学行为覆盖率 + Model Dump Syndrome（AB 验证 L0/L1 指标）

本脚本检查关键建模行为和模型堆砌风险，作为 `check_math_contract.py` 的补充诊断，不替代证明链和人工评审。

用法:
    python scripts/check_math_behavior.py <paper.md> --json   # 输出行为覆盖率 + MDS
    python scripts/check_math_behavior.py <paper.md>          # 人类可读

输出:
    behavior_coverage: {6 行为: 0/1} + coverage 率
    mds: {6 症状: 0/1} + mds_score（0-6，越低越好，=命中的 MDS 症状数）
"""
import json
import re
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ---- 数学行为（H1，6 项）----
# 1. 明确变量空间：符号定义/设…为…/决策变量
_RE_VAR = re.compile(r'(设[^。；\n]{0,40}(为|表示)|决策变量|变量空间|符号说明|记[^。；\n]{0,30}为)')
# 2. 定义目标函数：min/max/优化目标/目标函数
_RE_OBJ = re.compile(r'(目标函数|优化目标|min\s|max\s|极小化|极大化|最小化|最大化|使[^。；\n]{0,20}最小)')
# 3. 定义约束集合：s.t./约束/满足
_RE_CONS = re.compile(r'(s\.t\.|约束条件|约束为|满足[^。；\n]{0,20}(约束|条件|限制)|subject\s+to)')
# 4. 解释模型选择：因为…采用/选择…的原因/考虑到…采用/与…相比采用
_RE_SEL = re.compile(r'(考虑到[^。；\n]{0,40}(采用|选择|使用)|由于[^。；\n]{0,40}(采用|选择|使用)|与[^。；\n]{0,20}(相比|对比)[^。；\n]{0,20}(采用|选择|使用|更)|(选用|采用|选择)[^。；\n]{0,40}(原因|理由|因为))')
# 5. 设计验证方案：验证/检验/灵敏度/误差分析
_RE_VAL = re.compile(r'(验证|检验|灵敏度|误差分析|交叉验证|对比实验|退化|极限)')
# 6. 分析理论性质：复杂度/收敛性/可行性/误差界/稳定性
_RE_TH = re.compile(r'(复杂度|收敛性|可行性|误差界|稳定性|可辨识性|最优性|存在性)')

# ---- Model Dump Syndrome（H2，5 症状）----
# M1. 模型名堆积：同一句/相邻出现 ≥2 个算法名且无任一完整形式化
_MODEL_NAMES = [
    '遗传算法', '模拟退火', '粒子群', '蚁群', '神经网络', 'LSTM', 'GRU', 'Transformer',
    'ARIMA', 'XGBoost', 'GBDT', '随机森林', 'SVM', '支持向量机', 'K-means', 'K均值',
    'TOPSIS', 'AHP', '层次分析法', '熵权', 'NSGA', '差分进化', '灰狼', '麻雀', '鲸鱼',
    'BP神经网络', 'CNN', '卷积神经网络', '线性回归', '逻辑回归', '决策树', '朴素贝叶斯',
]
_RE_MODEL_DUMP = re.compile('|'.join(map(re.escape, _MODEL_NAMES)))
# M2. 无选择理由：出现模型名但附近无"因为/由于/考虑到/相比"等理由
_RE_JUSTIFY = re.compile(r'(因为|由于|考虑到|相比|对比|理由是|原因在于|之所以)')
# M3. 无数学对象：建模章节无符号定义（复用 _RE_VAR，反向）
# M4. 无参数解释：出现参数但无含义（"种群 500，迭代 1000"无参数语义）
_RE_PARAM = re.compile(r'(种群|迭代|学习率|正则化|权重|参数(?!数)|超参数)')
# M5. 无结果解释：有结果数字但无"因为/表明/说明/反映"等解释
_RE_RESULT_EXPLAIN = re.compile(r'(表明|说明|反映|意味着|体现了|证明了|由图.*可知|由表.*可知|这是因为)')
_RE_NUM = re.compile(r'(\d+(\.\d+)?%?|\d+\.\d+)')
# M6. 黑箱推导：用"易知/显然/经过复杂推导/不难看出/易得"等跳过关键推导步骤
_RE_BLACK_BOX = re.compile(r'(易知|易得|显然|不难看出|经过复杂推导|由此可得[^。]{0,10}(?:模型|结果|解)|直接得到|无需赘述|推导略|过程省略)', re.S)


def _strip_code(text):
    return re.sub(r'```.*?```', '', text, flags=re.S)


def check_math_behavior(paper_text):
    """返回行为覆盖率 + MDS。不抛异常，只测量不拦截。"""
    text = _strip_code(paper_text)
    # 取"模型建立与求解"段（无则全文）
    m = re.search(r'#+\s*[43]\.?\s*模型(建立|建立与求解)', text)
    body = m.group(0) + text[m.end():] if m else text
    # 截到结论前（避免结论/附录稀释）
    m2 = re.search(r'#+\s*[567]\.?\s*(模型检验|模型评价|结论|灵敏度)', body)
    if m2:
        body = body[:m2.start()]

    behavior = {
        '变量空间': bool(_RE_VAR.search(body)),
        '目标函数': bool(_RE_OBJ.search(body)),
        '约束集合': bool(_RE_CONS.search(body)),
        '模型选择解释': bool(_RE_SEL.search(body)),
        '验证方案': bool(_RE_VAL.search(body)),
        '理论性质': bool(_RE_TH.search(body)),
    }
    coverage = sum(behavior.values()) / len(behavior)

    # ---- MDS ----
    mds = {}
    # M1 模型名堆积：模型名出现 ≥3 次 且 无任一完整形式化（形式化 ≈ 有数学对象或目标函数）
    model_hits = len(_RE_MODEL_DUMP.findall(body))
    has_formal = behavior['变量空间'] and (behavior['目标函数'] or behavior['约束集合'])
    mds['模型名堆积'] = model_hits >= 3 and not has_formal
    # M2 无选择理由：有模型名 但 无理由词
    mds['无选择理由'] = model_hits >= 1 and not _RE_JUSTIFY.search(body)
    # M3 无数学对象
    mds['无数学对象'] = not behavior['变量空间']
    # M4 无参数解释：有参数词 但 无单位/含义词（简化：有参数词且无符号表）
    mds['无参数解释'] = bool(_RE_PARAM.search(body)) and not _RE_VAR.search(body)
    # M5 无结果解释：有数字 但 无解释词
    mds['无结果解释'] = bool(_RE_NUM.search(body)) and not _RE_RESULT_EXPLAIN.search(body)
    # M6 黑箱推导：用"易知/显然/经过复杂推导"等跳过关键步骤
    mds['黑箱推导'] = bool(_RE_BLACK_BOX.search(body))

    mds_score = sum(mds.values())  # 0-6，越低越好

    # ---- MDS-B（质量层，v4.0 定位修正：MDS-A 管保底、MDS-B 管质量；质量主指标仍是盲评，此为辅助）----
    # B1 公式-文字比（每千字公式数，过低=文字带过数学）
    zh_count = len(re.findall(r'[\u4e00-\u9fff]', body))
    formula_count = len(re.findall(r'\$\$[^$]+\$\$|\$[^$\n]+\$|\\\[.*?\\\]', body, re.S))
    formula_per_1k = formula_count / (zh_count / 1000 + 1e-9)
    # B2 每问公式数（按"问题/子问题"分段估算）
    q_marks = len(re.findall(r'#+\s*子问题|#+\s*[45]\.\d|问题[一二三四]', body))
    per_question = formula_count / (q_marks + 1e-9)
    # B3 推导链完整度（跨公式引用数 / 公式数）
    chain_hits = len(re.findall(r'式\s*\(\d+\)', body))
    chain_density = chain_hits / (formula_count + 1e-9)

    mds_b = {
        '公式数': formula_count,
        '每千字公式数': round(formula_per_1k, 2),
        '每问公式数': round(per_question, 2),
        '跨公式引用数': chain_hits,
        '引用密度': round(chain_density, 2),
    }

    return {
        'behavior_coverage': behavior,
        'coverage_rate': round(coverage, 3),
        'mds_a': mds,
        'mds_a_score': mds_score,
        'mds_b': mds_b,
        'measures': {
            'model_name_hits': model_hits,
            'has_formal_model': has_formal,
        },
    }


# ---- 非建模章节公式密度检查（防公式堆砌）----
# 非建模章节标题模式：摘要、问题分析、模型检验、模型评价、结论
_NON_MODELING_SECTIONS = [
    (r'\\begin\{abstract\}', r'\\end\{abstract\}', '摘要'),
    (r'#+\s*\d*\.?\s*问题分析', r'#+\s*\d*\.?\s*(模型假设|符号说明|模型建立|数据预处理)', '问题分析'),
    (r'#+\s*\d*\.?\s*模型检验', r'#+\s*\d*\.?\s*(模型评价|结论|参考文献|附录)', '模型检验'),
    (r'#+\s*\d*\.?\s*模型评价', r'#+\s*\d*\.?\s*(结论|参考文献|附录)', '模型评价与推广'),
    (r'#+\s*\d*\.?\s*结论', r'#+\s*\d*\.?\s*(参考文献|附录|$)', '结论'),
]
# TeX 环境下的章节匹配
_NON_MODELING_TEX = [
    (r'\\begin\{abstract\}', r'\\end\{abstract\}', '摘要'),
    (r'\\section\{[^}]*问题分析', r'\\section\{[^}]*(模型假设|符号说明|模型建立|数据预处理)', '问题分析'),
    (r'\\section\{[^}]*模型检验', r'\\section\{[^}]*(模型评价|结论|参考文献|附录)', '模型检验'),
    (r'\\section\{[^}]*模型评价', r'\\section\{[^}]*(结论|参考文献|附录)', '模型评价与推广'),
    (r'\\section\{[^}]*结论', r'(\\section\{[^}]*(参考文献|附录)|$)', '结论'),
]
_RE_FORMULA_INLINE = re.compile(r'\$[^$\n]+\$')
_RE_FORMULA_DISPLAY = re.compile(r'\$\$[^$]+\$\$|\\\[.*?\\\]|\\begin\{equation\}.*?\\end\{equation\}|\\begin\{align\}.*?\\end\{align\}|\\begin\{gather\}.*?\\end\{gather\}', re.S)


def check_non_modeling_formula_density(text, is_tex=False):
    """检查非建模章节公式密度，防止公式堆砌。
    摘要：公式数>0 即警告（禁公式红线）。
    其他非建模章节：每500字公式数>2 即警告。
    """
    patterns = _NON_MODELING_TEX if is_tex else _NON_MODELING_SECTIONS
    results = []
    for start_pat, end_pat, section_name in patterns:
        m_start = re.search(start_pat, text)
        if not m_start:
            continue
        rest = text[m_start.start():]
        m_end = re.search(end_pat, rest[len(m_start.group()):])
        section_text = rest[:m_end.start() + len(m_start.group())] if m_end else rest
        # 统计公式数
        inline_count = len(_RE_FORMULA_INLINE.findall(section_text))
        display_count = len(_RE_FORMULA_DISPLAY.findall(section_text))
        total_formulas = inline_count + display_count
        # 统计中文字数
        zh_count = len(re.findall(r'[\u4e00-\u9fff]', section_text))
        density = total_formulas / (zh_count / 500 + 1e-9)
        # 判定
        if section_name == '摘要':
            warning = total_formulas > 0
            threshold = '0（摘要禁公式）'
        else:
            warning = density > 2.0
            threshold = '≤2个/500字'
        results.append({
            'section': section_name,
            'formula_count': total_formulas,
            'inline_formulas': inline_count,
            'display_formulas': display_count,
            'zh_chars': zh_count,
            'formulas_per_500chars': round(density, 2),
            'threshold': threshold,
            'warning': warning,
        })
    return results


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        return 2
    path = sys.argv[1]
    as_json = '--json' in sys.argv[2:]
    try:
        with open(path, encoding='utf-8') as f:
            text = f.read()
    except OSError as e:
        print(f'读取失败: {e}', file=sys.stderr)
        return 2
    r = check_math_behavior(text)
    is_tex = path.endswith('.tex')
    non_modeling = check_non_modeling_formula_density(text, is_tex=is_tex)
    if as_json:
        r['non_modeling_formula_density'] = non_modeling
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        print(f'数学行为覆盖率: {r["coverage_rate"]:.0%}')
        for k, v in r['behavior_coverage'].items():
            print(f"  [{('✓' if v else '✗')}] {k}")
        print(f'MDS-A 保底: {r["mds_a_score"]}/5（越低越好）')
        for k, v in r['mds_a'].items():
            print(f"  [{('有' if v else '无')}] {k}")
        print(f'MDS-B 质量: {json.dumps(r["mds_b"], ensure_ascii=False)}')
        print('非建模章节公式密度:')
        for item in non_modeling:
            flag = '⚠️ 公式堆砌' if item['warning'] else '✓'
            print(f"  [{flag}] {item['section']}: {item['formula_count']}个公式, {item['formulas_per_500chars']}个/500字 (阈值:{item['threshold']})")
    return 0


if __name__ == '__main__':
    sys.exit(main())
