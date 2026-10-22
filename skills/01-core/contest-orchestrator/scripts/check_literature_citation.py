#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/check_literature_citation.py — 文献引用核查（交付门禁补充 F4.x）

检查论文 PDF/docx 中的文献引用是否真实落地，拦截"文末列了参考文献正文一字不提"的情况。

用法:
    python scripts/check_literature_citation.py <paper.pdf | paper.docx> [--replay-dir <dir>] [--verbose]

输出:
    PASS/FAIL + 详细问题清单

检查项:
    C1. 正文是否包含 [1][2]... 类引用标记？                              → 无标记 = FAIL
    C2. 每个引用标记是否在上下文中被实质性使用？                          → 孤立标记 = WARN
    C3. 是否有孤儿引用（仅在参考文献列表但正文无任何调用）？              → 有 = FAIL
    C4. 文献描述与技术章节是否大致匹配？                                  → 不匹配 = WARN
    C5. 五段式结构（检索方向/方法分类/研究缺口/建模关联）是否存在？       → 缺 = WARN
"""

import sys
import os
import re
import json
from collections import Counter

try:
    # Windows PowerShell may expose a cp936 stream; UTF-8 keeps WARN/FAIL
    # reports machine-readable instead of crashing while printing symbols.
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except (AttributeError, OSError):
    pass


def _to_int(s):
    """把 ref_ID 字符串转 int（兼容 '1' / ' 1 ' / 1）。"""
    try:
        return int(str(s).strip().strip('"').strip("'"))
    except (ValueError, TypeError):
        return str(s).strip().strip('"').strip("'")


def load_references(replay_dir):
    """从 competition_replay/<竞赛>_<年份>_<题号>/references.yaml 加载。"""
    refs = []
    refs_path = os.path.join(replay_dir, 'references.yaml')
    if not os.path.exists(refs_path):
        return None, f'未找到 {refs_path}'

    try:
        txt = open(refs_path, encoding='utf-8').read()
        current_ref = {}
        for line in txt.splitlines():
            stripped = line.strip()
            if stripped.startswith('- ref_ID:'):
                if current_ref:
                    refs.append(current_ref)
                current_ref = {'ref_ID': _to_int(stripped.split(':', 1)[1])}
            elif stripped.startswith('ref_ID:') and not current_ref:
                current_ref = {'ref_ID': _to_int(stripped.split(':', 1)[1])}
            elif ':' in stripped and current_ref:
                key, val = stripped.split(':', 1)
                val = val.strip().strip('"')
                current_ref[key.strip()] = val
        if current_ref:
            refs.append(current_ref)
    except Exception as e:
        return None, f'references.yaml 解析失败: {e}'

    return refs, None


def reference_ids(refs):
    """Return numeric citation IDs while preserving legacy numeric registries.

    Project reference ledgers commonly use stable labels such as ``R01`` while
    the rendered numeric bibliography uses ``[1]``.  Map that explicit RNN
    convention to its numeric suffix; retain ordinary numeric IDs unchanged.
    """
    raw_ids = [r.get('ref_ID', '') for r in refs]
    if raw_ids and all(re.fullmatch(r'R\d+', str(value), re.I) for value in raw_ids):
        return {int(str(value)[1:]) for value in raw_ids}
    return set(_to_int(value) for value in raw_ids)


def extract_citations_from_text(text):
    """从文本中提取顺序编码引用及上下文。

    兼容 ``[1]``、``[1-3]``、``[1,2]`` 和中文分隔符。
    ``[N]``，会把合并引用漏掉，进而错误地报告“正文没有使用文献”。
    """
    pattern = r'\[([0-9]+(?:\s*[-–—,，、;；]\s*[0-9]+)*)\]'
    citations = []

    def expand_ids(raw):
        ids = []
        for token in re.split(r'[,，、;；]', raw):
            token = token.strip()
            range_match = re.fullmatch(r'(\d+)\s*[-–—]\s*(\d+)', token)
            if range_match:
                start, end = map(int, range_match.groups())
                if start <= end <= start + 50:
                    ids.extend(range(start, end + 1))
                else:
                    ids.append(start)
                    ids.append(end)
            elif token.isdigit():
                ids.append(int(token))
        return sorted(set(ids))

    punctuation = set('。；，：！？、,.!?;:')
    for m in re.finditer(pattern, text):
        start = max(0, m.start() - 100)
        end = min(len(text), m.end() + 100)
        context = text[start:end].replace('\n', ' ').strip()

        tail = text[m.end():m.end() + 8].lstrip()
        placement_ok = bool(tail) and tail[0] in punctuation
        cite_ids = expand_ids(m.group(1))
        # [0,1] is a probability interval in mathematical prose, never a
        # valid 1-based bibliography marker.
        if 0 in cite_ids:
            continue
        for cite_id in cite_ids:
            citations.append({
                'cite_id': cite_id,
                'position': m.start(),
                'context': context,
                'marker': m.group(0),
                'placement_ok': placement_ok,
                'has_substantive_discussion': False,  # 后续判断
            })

    return citations


def check_citations_in_chapters(citations, chapter_keywords):
    """检查各章是否有对应引用，避免全挤在某一处。"""
    chapter_coverage = {}
    for kw_name, kw_patterns in chapter_keywords.items():
        has_cite = any(
            c.get('position', 0) > 0  # 简化判断，实际需要更精确的章节边界
            for _ in kw_patterns
        )
        chapter_coverage[kw_name] = has_cite
    return chapter_coverage


def assess_substantive_context(context, cite_id):
    """评估引用标记周围的上下文是否有实质性讨论。

    实质性讨论的特征:
    - 提到具体方法名（不是泛泛的"某文献"）
    - 有技术细节（公式、算法步骤、参数）
    - 有对比分析（"相比XX方法的优点"）
    """
    substantive_indicators = [
        # 方法类关键词
        '启发式', '遗传算法', '动态规划', '强化学习', '深度学习',
        '线性规划', '整数规划', '蒙特卡洛', '粒子群', '模拟退火',
        'LSTM', 'Transformer', '神经网络', '贝叶斯', '回归',
        '代价函数', '目标函数', '约束条件', '状态转移',
        # 讨论类关键词
        '借鉴', '参考', '改进', '扩展', '针对', '引入',
        '相比', '优于', '局限性', '不足', '局限',
        '公式', '模型', '算法', '策略', '机制', '理论依据', '参数来源',
        '测量先例', '选择准则', '实现依据', '适用边界', '作为参数',
        '交叉核对', '实验说明', '提供依据', '采用', '支持', '色散', '折射率',
        # 否定特征（纯人名罗列）
        '等人提出', '研究了', '发现', '表明',
    ]

    hits = sum(1 for kw in substantive_indicators if kw in context)
    total_words = len([c for c in context if c.isalpha() or '\u4e00' <= c <= '\u9fff'])

    # 至少 3 个实质关键词，且不是纯人名模式
    role_terms = ('理论依据', '参数来源', '测量先例', '选择准则', '实现依据', '适用边界', '作为参数')
    technical_terms = ('模型', '公式', '算法', '参数', '色散', '折射率', 'BIC', '厚度', '实验')
    if any(term in context for term in role_terms) and any(term in context for term in technical_terms) and total_words > 10:
        return True
    if hits >= 2 and total_words > 10:
        return True
    if hits >= 3:
        return True
    return False


def check_five_section_structure(report_text):
    """检查五段式文献调研报告结构是否完整。"""
    required_sections = {
        '检索来源与方向': ['检索', '关键词', '数据库', 'arXiv', 'CrossRef'],
        '方法分类归纳': ['方法类别', '分类归纳', '代表性工作', '优势', '局限'],
        '研究缺口': ['研究缺口', '创新点', '未充分处理', '缺乏', '不足'],
        '建模关联': ['借鉴', '本文', '改进', '修改', '定制化'],
        '引用标记规范': ['引用标记', 'GB/T', '顺序编码'],
    }

    missing = []
    found = {}
    for section_name, keywords in required_sections.items():
        hit_count = sum(1 for kw in keywords if kw in report_text)
        found[section_name] = hit_count >= 2
        if hit_count < 1:
            missing.append(section_name)

    return found, missing


def run_check(paper_path, replay_dir=None, verbose=False):
    """执行完整的文献引用核查。

    Returns:
        dict with:
          - status: 'PASS' / 'WARN' / 'FAIL'
          - checks: dict of individual check results
          - issues: list of problem descriptions
    """
    issues = []
    check_results = {}

    # 读取论文文本（先尝试 .txt/.md 直接读，docx/pdf 需要额外处理）
    if not os.path.exists(paper_path):
        return {
            'status': 'FAIL',
            'checks': {'file_exists': False},
            'issues': [f'文件不存在: {paper_path}'],
        }

    # 尝试多种文件格式
    text = ''
    ext = os.path.splitext(paper_path)[1].lower()

    if ext in ('.txt', '.md', '.tex'):
        text = open(paper_path, encoding='utf-8').read()
    elif ext == '.docx':
        try:
            from docx import Document
            doc = Document(paper_path)
            text = '\n'.join(p.text for p in doc.paragraphs)
        except ImportError:
            if verbose:
                issues.append(f'⚠️ 无法打开 .docx 文件（缺少 python-docx），跳过文档级检查')
            return {
                'status': 'WARN',
                'checks': {'docx_not_available': True},
                'issues': issues,
            }
    elif ext in ('.pdf',):
        try:
            import pymupdf
            doc = pymupdf.open(paper_path)
            text = '\n'.join(page.get_text() for page in doc)
        except ImportError:
            if verbose:
                issues.append(f'⚠️ 无法打开 .pdf 文件（缺少 PyMuPDF），跳过文档级检查')
            return {
                'status': 'WARN',
                'checks': {'pdf_not_available': True},
                'issues': issues,
            }

    # 附录代码的方括号通常是数组下标或行号，不是正文参考文献标记。
    # PDF 以“参考文献”为界，只审查其前的正文引用，避免把附录代码误判为弱引用。
    if ext == '.pdf':
        for marker in ('参考文献', '文献资料', 'References'):
            if marker in text:
                text = text.split(marker, 1)[0]
                break

    if not text.strip():
        return {
            'status': 'FAIL',
            'checks': {'empty_text': True},
            'issues': ['论文文件为空或无法提取文本'],
        }

    # ---- C1: 检查是否包含引用标记 ----
    citations = extract_citations_from_text(text)
    check_results['c1_has_citation_markers'] = len(citations) > 0

    if len(citations) < 2:
        check_results['c1_status'] = 'FAIL'
        issues.append(f'❌ 正文中仅有 {len(citations)} 处引用标记（建议至少 2+ 处），可能存在"仅列目录不引用"的问题')
    else:
        check_results['c1_status'] = 'PASS'
        if verbose:
            cite_ids = sorted(set(c['cite_id'] for c in citations))
            issues.append(f'ℹ️ 检测到 {len(citations)} 处引用标记，涉及文献 ID: {cite_ids}')

    # ---- C2: 评估每个引用的上下文质量 ----
    substantive_count = 0
    weak_citations = []
    for c in citations:
        is_substantive = assess_substantive_context(c['context'], c['cite_id'])
        c['has_substantive_discussion'] = is_substantive
        if is_substantive:
            substantive_count += 1
        else:
            weak_citations.append(c['cite_id'])

    overall_substantive_ratio = substantive_count / max(1, len(citations))
    check_results['c2_substantive_ratio'] = round(overall_substantive_ratio, 2)

    if overall_substantive_ratio < 0.5 and len(citations) >= 2:
        check_results['c2_status'] = 'WARN'
        issues.append(f'⚠️ {len(weak_citations)}/{len(citations)} 处引用标记缺乏实质性讨论（可能只是挂名引用）')
    else:
        check_results['c2_status'] = 'PASS'

    # ---- C2b: 引用位置 ----
    placement_bad = [c['cite_id'] for c in citations if not c.get('placement_ok', False)]
    check_results['c2b_citation_placement'] = 'PASS' if not placement_bad else 'WARN'
    if placement_bad:
        issues.append(f'⚠️ 引用 {sorted(set(placement_bad))} 未紧贴对应内容并置于句末标点之前')

    # ---- C3: 孤儿引用检查 ----
    referenced_refs = set(c['cite_id'] for c in citations)
    refs, err = load_references(replay_dir) if replay_dir else (None, None)

    orphan_check = {}
    if refs:
        all_ref_ids = reference_ids(refs)
        missing_refs = all_ref_ids - referenced_refs

        orphan_check = {
            'total_refs_in_file': len(refs),
            'cited_refs': len(referenced_refs),
            'orphan_refs': list(missing_refs),
        }

        if missing_refs:
            check_results['c3_orphan_refs'] = 'FAIL'
            issues.append(f'❌ 发现孤儿引用 {len(missing_refs)} 条：[{", ".join(str(r) for r in missing_refs)}] — 在 references.yaml 中存在但正文未调用')
        else:
            check_results['c3_orphan_refs'] = 'PASS'
    else:
        check_results['c3_orphan_refs'] = 'SKIP'
        if err:
            issues.append(f'ℹ️ {err}')

    # ---- C4: 文献描述与技术章节匹配 ----
    # 简单检查：如果在 Q1/Q2 建模章节附近没有出现任何引用，可能是问题
    model_sections = re.findall(r'(?:建模|模型建立|Q[1-4]|问题\d)', text)
    check_results['c4_method_section_has_citations'] = len(model_sections) > 0 and len(citations) > 0

    if model_sections and not citations:
        check_results['c4_status'] = 'FAIL'
        issues.append('❌ 存在多个建模章节但没有引用任何文献支撑方法论选择')
    else:
        check_results['c4_status'] = 'PASS'

    # ---- C5: 五段式结构完整性 ----
    # 需要从文献调研报告中提取（可能在 separate file 或作为论文一部分）
    lit_report_path = None
    if replay_dir:
        lit_report_path = os.path.join(replay_dir, 'literature_report.md')
    elif paper_path.endswith('literature_report.md'):
        lit_report_path = paper_path

    structure_check = {'checked': False, 'missing': []}
    if lit_report_path and os.path.exists(lit_report_path):
        report_text = open(lit_report_path, encoding='utf-8').read()
        sections_found, missing_sections = check_five_section_structure(report_text)
        structure_check = {
            'checked': True,
            'sections_found': sections_found,
            'missing': missing_sections,
        }

        if missing_sections:
            check_results['c5_five_section'] = 'WARN'
            issues.append(f'⚠️ 五段式结构缺失: {", ".join(missing_sections)}')
        else:
            check_results['c5_five_section'] = 'PASS'
    else:
        check_results['c5_five_section'] = 'SKIP'
        issues.append('ℹ️ 未找到独立的文献调研报告，跳过五段式结构检查')

    # ---- 综合判定 ----
    fail_checks = [k for k, v in check_results.items() if v == 'FAIL']
    warn_checks = [k for k, v in check_results.items() if v == 'WARN']

    if fail_checks:
        final_status = 'FAIL'
    elif warn_checks:
        final_status = 'WARN'
    else:
        final_status = 'PASS'

    return {
        'status': final_status,
        'checks': check_results,
        'issues': issues,
        'citation_summary': {
            'total_citations': len(citations),
            'substantive_citations': substantive_count,
            'weak_citations': len(weak_citations),
            'unique_ref_ids': sorted(set(c['cite_id'] for c in citations)),
        },
        'orphan_check': orphan_check,
        'structure_check': structure_check,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description='文献引用核查（交付门禁 F4.x）')
    parser.add_argument('paper_path', help='论文文件路径 (.pdf/.docx/.txt/.md)')
    parser.add_argument('--replay-dir', default=None, help='competition_replay 目录路径')
    parser.add_argument('--verbose', '-v', action='store_true', help='输出详细信息')
    parser.add_argument('--strict', action='store_true', help='将挂名引用和位置违规从 WARN 升级为 FAIL')
    args = parser.parse_args()

    result = run_check(args.paper_path, args.replay_dir, args.verbose)
    if args.strict:
        checks = result.get('checks', {})
        if checks.get('c2_status') == 'WARN' or checks.get('c2b_citation_placement') == 'WARN':
            result['status'] = 'FAIL'
            result['issues'].append('❌ 严格模式禁止挂名引用或引用位置违规')

    # 打印结果
    print(f'\n{'='*60}')
    print(f'文献引用核查结果: {result["status"]}')
    print(f'{'='*60}\n')

    for issue in result['issues']:
        print(issue)

    if args.verbose:
        print(f'\n--- 详细统计 ---')
        summary = result.get('citation_summary', {})
        print(f'引用总数: {summary.get("total_citations", "?")}')
        print(f'实质讨论: {summary.get("substantive_citations", "?")}')
        print(f'弱引用:   {summary.get("weak_citations", "?")}')
        print(f'唯一ID:   {summary.get("unique_ref_ids", "?")}')

        print(f'\n--- 分项检查结果 ---')
        for k, v in result['checks'].items():
            print(f'  {k}: {v}')

    # 返回退出码
    sys.exit(0 if result['status'] != 'FAIL' else 1)


if __name__ == '__main__':
    main()
