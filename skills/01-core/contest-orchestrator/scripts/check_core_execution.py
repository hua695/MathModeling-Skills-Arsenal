#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_core_execution.py — 核心功能执行自检(core/core_functions.md)
用法: python scripts/check_core_execution.py <replay目录> [--phase A|B|C|D|E|F|G]
      replay 目录默认 = <工作区>/practical test/<竞赛>_<年份>_<题号>/
检查 CF1-CF10 的强制产物, 任一缺失/FAIL -> 交付不合格。
CF8 academic-writing: 扫描论文 tex 是否残留 AI 套路词。
"""
import glob
import json
import os
import re
import sys
from pathlib import Path

from check_modeling_contract import expand_inputs

AI_PATTERNS = [
    '值得注意的是', '综上所述', '总而言之', '层层递进', '逻辑闭环', '全面超越', '至关重要',
    '必不可少', '不可或缺', '一站式', '深入浅出', '迈向', '赋能', '抓手', '打通',
    '为.*提供了(?:依据|基础)', '显著提升了', '有效提升了', '显著提高了', '有效提高了',
    '凸显了', '彰显了', '奠定了', '具有重要意义', '研究表明',
    '值得深入探讨', '未来研究方向', '从理论上来讲', '基于以上分析',
]
# AI 高频副词组 — 连续出现 ≥2 个视为强指纹
ADVERB_GROUP = [
    '显著地', '有效地', '合理地', '相应地', '进一步地', '适当地',
    '充分地', '全面地', '系统地', '深入地', '科学地', '客观地',
]

# 检查项 → 阶段映射（配合 --phase 阶段 checkpoint：每阶段完成时只查本阶段产物）
PHASE_MAP = {
    'CF1 problem_graph': 'A', 'CF2 experience_usage': 'A', 'A2 符号表': 'A',
    'A5 模型假设': 'A', 'A1.5 数据审计': 'A',
    'B2 文献池': 'B', 'B2 文献调研报告（五段式）': 'B', 'B2 引用映射表': 'B',
    'B3 风险探针': 'B', 'CF3 baseline 落盘': 'B',
    'C2 出图': 'C', 'C2 流程图工具': 'C', 'C1.5 灵敏度': 'C', 'CF4 结果 JSON': 'C',
    'D0 论文大纲': 'D', 'D1 附录骨架': 'D', 'CF8 academic-writing(AI词扫描)': 'D',
    'E3 评审产物': 'E',
    'CF5-CF7 核对脚本存在': 'F',
    'CF9 决策日志': 'G', 'CF9 快照': 'G', '执行留痕日志': 'G',
}


def appendix_requirements(root: Path, paper_dir: Path) -> tuple[bool, bool]:
    """Return (code_required, evidence_required) for the current project.

    A capability-driven appendix plan is authoritative.  Legacy contracts are
    still accepted.  With no manifest we retain the historical conservative
    requirement so incomplete projects do not silently pass the checkpoint.
    """
    candidates = [root / name for name in (
        'appendix_plan.yaml', 'appendix_plan.yml', 'appendix_plan.json',
        'appendix_contract.yaml', 'appendix_contract.yml', 'appendix_contract.json')]
    candidates += [paper_dir / path.name for path in candidates]
    manifest = next((path for path in candidates if path.exists()), None)
    if manifest is None:
        return True, True
    try:
        raw = manifest.read_text(encoding='utf-8', errors='replace')
        if manifest.suffix.lower() == '.json':
            data = json.loads(raw)
        else:
            import yaml
            data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            return True, True
        source = data.get('source_inputs') if isinstance(data.get('source_inputs'), dict) else data
        modules = data.get('appendix_modules', data.get('modules', [])) or []
        kinds = {str(item.get('kind', '')).lower() for item in modules
                 if isinstance(item, dict) and item.get('required', False)}
        capabilities = {str(cap).lower() for item in data.get('subproblems', []) or []
                        if isinstance(item, dict) for cap in (item.get('capabilities', []) or [])}
        code_caps = {'code', 'numerical_fitting', 'numerical_simulation', 'machine_learning', 'optimization_solver'}
        explicit = source.get('program_used') if isinstance(source.get('program_used'), bool) else None
        code_required = explicit if explicit is not None else bool(kinds & {'code', 'source_code'} or capabilities & code_caps)
        evidence_required = bool(modules) or bool(source.get('long_derivation_files')) or bool(source.get('raw_data_files'))
        return bool(code_required), bool(evidence_required)
    except Exception:
        return True, True


def check(replay_dir, phase=None):
    r = {}
    root = Path(replay_dir).resolve()
    planning = root / '01_需求与规划' if (root / '01_需求与规划').is_dir() else root
    output = root / '05_输出与交付' if (root / '05_输出与交付').is_dir() else root
    paper_dir = root / '03_文档' / 'paper' if (root / '03_文档' / 'paper').is_dir() else (
        root / 'paper' if (root / 'paper').is_dir() else root)

    def first_existing(*paths):
        return next((path for path in paths if path.exists()), paths[0] if paths else root)

    def planning_file(name):
        return first_existing(planning / name, root / name)

    def output_file(name):
        return first_existing(output / name, root / name)

    def valid_json_file(path, require_mapping=False):
        try:
            with open(path, encoding='utf-8') as handle:
                value = json.load(handle)
            if value in (None, {}, []):
                return False
            return not require_mapping or isinstance(value, dict)
        except (OSError, ValueError, TypeError):
            return False

    # Standard project layout stores evidence under 01_需求与规划 and
    # numerical outputs under 05_输出与交付. Legacy flat replay layouts remain supported.
    result_candidates = [output / 'results', output, root / 'results']
    result_candidates.extend(path for path in root.glob('results*') if path.is_dir())
    res_dir = next((path for path in result_candidates if path.is_dir()), None)

    r['CF1 problem_graph'] = 'PASS' if planning_file('problem_graph.md').exists() else 'FAIL(缺 problem_graph.md)'
    r['CF2 experience_usage'] = 'PASS' if planning_file('experience_usage.yaml').exists() else 'FAIL(缺 experience_usage.yaml)'
    r['A2 符号表'] = 'PASS' if planning_file('symbol_table.md').exists() else 'FAIL(缺 symbol_table.md)'
    r['A5 模型假设'] = 'PASS' if planning_file('model_assumptions.md').exists() else 'FAIL(缺 model_assumptions.md)'
    r['A1.5 数据审计'] = 'PASS' if planning_file('data_audit.md').exists() else 'WARN(缺 data_audit.md；无附件题目可忽略)'
    r['B2 文献池'] = 'PASS' if planning_file('references.yaml').exists() else 'FAIL(缺 references.yaml)'
    r['B2 文献调研报告（五段式）'] = 'PASS' if planning_file('literature_report.md').exists() else 'FAIL(缺 literature_report.md；五段式报告未生成)'
    r['B2 引用映射表'] = 'PASS' if planning_file('citation_map.json').exists() else 'WARN(缺 citation_map.json；写作阶段不会按章节对照引用)'
    r['B3 风险探针'] = 'PASS' if planning_file('risk_probe_summary.md').exists() else 'FAIL(缺 risk_probe_summary.md)'
    figure_dir = first_existing(output / 'figures', res_dir / 'figures' if res_dir else root / 'figures', root / 'figures')
    image_count = len(list(figure_dir.glob('*.png'))) if figure_dir.is_dir() else 0
    r['C2 出图'] = 'PASS' if res_dir and image_count else 'FAIL(缺 figures/ 或图像文件)'
    # C2 图表来源锁：每类图表必须使用唯一的专用路由。
    fr = output_file('figure_registry.json')
    if fr.exists():
        try:
            reg = json.load(open(fr, encoding='utf-8'))
        except Exception:
            reg = None
        bad = []
        if isinstance(reg, dict):
            entries = reg.get('figures', reg)
            registry_status = str(reg.get('status', '')).strip().lower()
            if registry_status.startswith('blocked') or registry_status in {'stale', 'invalid'}:
                bad.append(f'registry(status={registry_status})')
            if isinstance(entries, list):
                if not entries:
                    bad.append('registry(figures empty)')
                entries = {str(item.get('id', i)): item for i, item in enumerate(entries) if isinstance(item, dict)}
            for fig, meta in (entries.items() if isinstance(entries, dict) else []):
                if not isinstance(meta, dict):
                    continue
                qa_status = str(meta.get('qa_status', '')).strip().lower()
                if qa_status in {'blocked', 'stale', 'invalid', 'fail'}:
                    bad.append(f'{fig}(qa_status={qa_status})')
                t = str(meta.get('type', meta.get('kind', ''))).lower()
                name = str(fig).lower()
                is_diag = ('flow' in name or 'diagram' in name or 'schematic' in name
                           or 'flowchart' in t or 'diagram' in t or 'schematic' in t)
                generator = str(meta.get('generator', meta.get('generated_by', ''))).strip().lower()
                kind = str(meta.get('type', meta.get('kind', ''))).lower()
                if kind in {'data', 'chart', 'plot'}:
                    if (generator != 'modelviz'
                            or meta.get('semantic_qa') != 'scipilot-figure-skill'
                            or meta.get('decision_author') != 'scipilot-figure-skill'
                            or not meta.get('decision_card')):
                        bad.append(f'{fig}(数据图必须由 SciPilot 决策，再由 ModelViz 生成并经 SciPilot 质检)')
                elif kind in {'flow', 'flowchart'} or is_diag and kind != 'schematic':
                    if generator != 'tech-route-maker':
                        bad.append(f'{fig}(流程图 generator={generator or "missing"})')
                elif kind == 'schematic':
                    if generator != 'tikz-scientific-figures':
                        bad.append(f'{fig}(示意图 generator={generator or "missing"})')
                elif kind == 'drawio':
                    if generator != 'drawio-diagram' or meta.get('user_requested') is not True:
                        bad.append(f'{fig}(Draw.io 必须显式请求)')
        if bad:
            r['C2 流程图工具'] = f'FAIL(图表来源不符合 v4.7 路由: {bad})'
        else:
            r['C2 流程图工具'] = 'PASS(数据图=scipilot 决策→modelviz→scipilot；流程/路线=tech-route-maker；示意图=tikz-scientific-figures；Draw.io=显式请求)'
    else:
        r['C2 流程图工具'] = 'FAIL(缺 figure_registry.json；无法核验图表来源)'
    sensitivity = first_existing(res_dir / 'sensitivity_result.json' if res_dir else root / 'missing',
                                 output / 'sensitivity_results.json')
    r['C1.5 灵敏度'] = 'PASS' if valid_json_file(sensitivity, require_mapping=True) else 'FAIL(缺失或无效 sensitivity_result.json)'
    r['D0 论文大纲'] = 'PASS' if planning_file('paper_outline.md').exists() else 'FAIL(缺 paper_outline.md)'
    critic_dir = first_existing(output / 'critic_report', root / 'critic_report')
    r['E3 评审产物'] = 'PASS' if (output_file('review_questions.md').exists() or output_file('review_suggestion.md').exists()
                                  or list(critic_dir.glob('*_summary.md'))) else 'FAIL(缺 reviewer 评审产物)'
    r['CF3 baseline 落盘'] = 'PASS' if res_dir else 'FAIL(缺 results 目录)'
    result_files = list(res_dir.glob('q*_results.json')) if res_dir else []
    bad_results = [path.name for path in result_files if not valid_json_file(path, require_mapping=True)]
    r['CF4 结果 JSON'] = ('PASS' if result_files and not bad_results else
                          f'FAIL(缺失或无效 q*_results.json: {bad_results or "none"})')
    r['CF5-CF7 核对脚本存在'] = 'PASS' if os.path.exists(os.path.join(os.path.dirname(__file__), 'check_paper_hard_requirements.py')) and os.path.exists(os.path.join(os.path.dirname(__file__), 'docx_pipeline.py')) else 'FAIL'
    r['CF9 决策日志'] = 'PASS' if output_file('decision_log.md').exists() else 'FAIL(缺 decision_log.md)'
    r['CF9 快照'] = 'PASS' if output_file('snapshot.md').exists() else 'FAIL(缺 snapshot.md)'

    # 执行留痕: core_execution_log.md 必须存在(CF1-CF10 逐项记录)
    r['执行留痕日志'] = 'PASS' if output_file('core_execution_log.md').exists() else 'FAIL(缺 core_execution_log.md, 各功能未留痕)'

    # CF8 academic-writing: 扫描最新版论文 tex(AI 套路词)——兼容根目录 paper.tex 与 paper/paper.tex 两种布局
    # 加入 AI 高频副词组检测和 aigc_risk_checklist.json 补充词单
    _acl_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'aigc_risk_checklist.json')
    extra_patterns = []
    if os.path.exists(_acl_path):
        try:
            acl = json.load(open(_acl_path, encoding='utf-8'))
            for _pat in acl.get('banned_phrases', {}).get('absolute', []):
                if _pat not in AI_PATTERNS:
                    extra_patterns.append(_pat)
            for _pat in acl.get('banned_phrases', {}).get('high_risk', []):
                if _pat not in AI_PATTERNS:
                    extra_patterns.append(_pat)
            for _pat in acl.get('banned_patterns', []):
                if _pat not in AI_PATTERNS:
                    extra_patterns.append(_pat)
        except Exception:
            pass
    all_patterns = AI_PATTERNS + extra_patterns

    tex_cands = [str(path) for path in paper_dir.glob('paper*.tex')]
    tex = None
    if tex_cands:
        tex_cands.sort(key=os.path.getmtime, reverse=True)
        tex_path = Path(tex_cands[0])
        tex = expand_inputs(tex_path.read_text(encoding='utf-8', errors='replace'), tex_path.parent)
    if tex is None:
        r['CF8 academic-writing(AI词扫描)'] = 'FAIL(未找到 paper.tex)'
    else:
        hits = []
        for pat in all_patterns:
            for m in re.finditer(pat, tex):
                hits.append(pat)

        # ADVERB GROUP 检测：连续出现 ≥2 个 AI 高频副词 → WARN
        adv_count = sum(1 for adv in ADVERB_GROUP if adv in tex)
        adv_warn = f'⚠️ AI 高频副词连续出现 {adv_count} 次 (ADVERB_GROUP={ADVERB_GROUP})' if adv_count >= 2 else ''

        if hits or adv_count >= 2:
            hit_desc = set(hits[:5])  # 只显示前5个避免太长
            detail = f'残留 AI 套路词: {hit_desc}'
            if adv_warn:
                detail += f'; {adv_warn}'
            r['CF8 academic-writing(AI词扫描)'] = f'FAIL({detail})'
        else:
            r['CF8 academic-writing(AI词扫描)'] = 'PASS(无残留)'

    # D1 附录骨架：按项目 appendix_plan/appendix_contract 条件启用代码和
    # 证据检查；不再把“代码节+结果节”硬套到纯解析/手算题。
    tex_text = tex if tex else ''
    if not tex_text:
        r['D1 附录骨架'] = 'FAIL(未找到 paper.tex，无法查附录骨架)'
    else:
        appendix = tex_text.split('\\appendix', 1)[1] if '\\appendix' in tex_text else ''
        has_code = bool(appendix) and any(m in appendix for m in ['\\inputminted', '\\begin{minted}', '\\lstinputlisting', '\\lstlisting', '\\begin{lstlisting}'])
        has_results = bool(appendix) and any(m in appendix for m in [
            '结果汇总', '数据验证', '代表性中间结果', '中间结果', 'D.1', 'D.2', '灵敏度', 'sensitivity'
        ])
        has_derivation = bool(appendix) and any(m in appendix for m in ['推导', '证明', '公式', 'derivation'])
        code_required, evidence_required = appendix_requirements(root, paper_dir)
        missing = []
        if code_required and not has_code:
            missing.append('核心代码节(inputminted/minted)')
        if evidence_required and not (has_results or has_derivation or has_code):
            missing.append('推导/结果/数据证据节')
        if missing:
            r['D1 附录骨架'] = 'FAIL(附录缺: ' + '+'.join(missing) + ')'
        else:
            mode = '代码+证据' if code_required else '按能力证据（无代码强制）'
            r['D1 附录骨架'] = f'PASS({mode})'

    shown = [(k, v) for k, v in r.items() if phase is None or PHASE_MAP.get(k) == phase]

    print(f'=== Core Functions Check: {replay_dir}' + (f' [阶段 {phase}]' if phase else '') + ' ===')
    all_ok = True
    for k, v in shown:
        ok = str(v).startswith('PASS')
        all_ok = all_ok and ok
        print(f"  {'PASS' if ok else 'FAIL'} {k}: {v}")
    print(f'===== 核心功能执行: {"PASS" if all_ok else "FAIL(缺项需补做)"} =====')
    return all_ok

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='核心功能执行自检（支持按阶段 checkpoint）')
    ap.add_argument('replay', nargs='?', default='.', help='replay 目录')
    ap.add_argument('--phase', default=None, choices=['A', 'B', 'C', 'D', 'E', 'F', 'G', None],
                    help='只查某阶段产物（阶段 checkpoint 用）；缺省全查')
    args = ap.parse_args()
    sys.exit(0 if check(args.replay, args.phase) else 1)
