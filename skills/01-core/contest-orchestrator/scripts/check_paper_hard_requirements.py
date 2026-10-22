#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_paper_hard_requirements.py — 论文硬性要求清单自动核对(core/paper_hard_requirements.md)
用法: python scripts/check_paper_hard_requirements.py <paper.pdf>
返回每项 PASS/FAIL, 供 Paper-Critic 交付前核对(H 节第②③步)。
核对项: 项目 profile 启用的篇幅、图表来源与解读、关键词、摘要总评、附录顺序、代码范围和字体族。
"""
import argparse
import json
import re
import sys
from pathlib import Path


DEFAULT_PROFILE = {
    # 不凭经验给所有赛事施加正文最低页数；赛事官方规则或项目 profile
    # 可以显式覆盖 min/max。默认仍保留防止异常超长的上限。
    'body_pages': {'min': None, 'max': 30},
    'body_includes_abstract': True,
    'body_includes_references': True,
    # 图表数量不设全局门槛。质量、来源、正文引导文字仍由视觉与图表
    # 注册表门禁检查；若某竞赛官方 profile 明确规定数量，可在项目
    # profile JSON 中显式提供 min/max。
    'figures': {'min': None, 'max': None},
    'appendix_sequence': ['支撑材料文件清单', '关键计算代码片段', '关键推导补充', '代表性中间结果', '工具使用说明'],
    'font_check': True,
}


def has_reference_heading(text: str) -> bool:
    """Recognize a standalone bibliography heading anywhere on a PDF page.

    A long table can legitimately precede a bibliography heading on the same
    page. Restricting the search to the first lines undercounts body pages;
    requiring a complete standalone line still avoids ordinary prose mentions.
    """
    markers = ('参考文献', '文献资料', 'References', 'REFERENCES')
    return any(
        re.search(r"(?:^|\n)\s*" + re.escape(marker) + r"\s*(?:\n|$)", text)
        for marker in markers
    )


def has_appendix_heading(text: str) -> bool:
    """Recognize the first short appendix heading on a PDF page."""
    return any(
        line.strip().startswith("附录") and len(line.strip()) <= 24
        for line in text.splitlines()
    )


def body_page_count(
    texts: list[str],
    include_references: bool = True,
    include_abstract: bool = True,
) -> int:
    """Count body pages, optionally through references and after the abstract."""
    appendix_page = next(
        (index + 1 for index, text in enumerate(texts) if has_appendix_heading(text)),
        None,
    )
    paper_end = appendix_page - 1 if appendix_page else len(texts)
    body_start = 1
    if not include_abstract:
        keyword_page = next(
            (index + 1 for index, text in enumerate(texts[:paper_end]) if '关键词' in text),
            None,
        )
        body_start = keyword_page + 1 if keyword_page else 2
    if body_start > paper_end:
        return 0
    if include_references:
        return paper_end - body_start + 1
    reference_page = next(
        (index + 1 for index, text in enumerate(texts[:paper_end])
         if has_reference_heading(text)),
        None,
    )
    end = reference_page - 1 if reference_page else paper_end
    return max(0, end - body_start + 1)


def load_profile(path: str | None) -> dict:
    profile = {key: value.copy() if isinstance(value, dict) else (list(value) if isinstance(value, list) else value)
               for key, value in DEFAULT_PROFILE.items()}
    if not path:
        return profile
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise ValueError('profile must be a JSON object')
    for key in ('body_pages', 'figures'):
        if key in payload:
            if payload[key] is None:
                profile[key] = {'min': None, 'max': None}
            else:
                profile[key].update(payload[key])
    for key in ('appendix_sequence', 'font_check', 'body_includes_abstract', 'body_includes_references'):
        if key in payload:
            profile[key] = payload[key]
    paper = payload.get('paper') or {}
    if isinstance(paper, dict):
        if 'body_max_pages' in paper:
            profile['body_pages']['max'] = paper['body_max_pages']
        if 'body_includes_abstract' in paper:
            profile['body_includes_abstract'] = paper['body_includes_abstract']
        if 'body_includes_references' in paper:
            profile['body_includes_references'] = paper['body_includes_references']
    regional = payload.get('regional_advisory') or {}
    if isinstance(regional, dict) and 'submission_total_max_pages' in regional:
        profile['whole_paper_max_pages'] = regional['submission_total_max_pages']
    return profile

def main(path, profile_path=None):
    profile = load_profile(profile_path)
    try:
        import pymupdf
    except ImportError:
        return [], ["未安装 pymupdf，无法执行 PDF 硬性要求检查"]
    doc = pymupdf.open(path)
    n = len(doc)
    texts = [doc[i].get_text() for i in range(n)]
    full = ''.join(texts)
    full_c = full.replace('\n', '').replace(' ', '')
    r = {}

    # 1. 正文页数：按 profile 决定是否计入摘要和参考文献，附录不计。
    body = body_page_count(
        texts,
        profile.get('body_includes_references', True),
        profile.get('body_includes_abstract', True),
    )
    body_min = profile['body_pages'].get('min')
    body_max = profile['body_pages'].get('max')
    body_ok = (body_min is None or body >= body_min) and (body_max is None or body <= body_max)
    min_label = body_min if body_min is not None else '不限'
    max_label = body_max if body_max is not None else '不限'
    abstract_label = '含摘要' if profile.get('body_includes_abstract', True) else '不含摘要'
    reference_label = '含参考文献' if profile.get('body_includes_references', True) else '不含参考文献'
    r[f'正文{min_label}-{max_label}页（{abstract_label}，{reference_label}）'] = f'PASS({body})' if body_ok else f'FAIL({body})'

    whole_limit = profile.get('whole_paper_max_pages')
    if whole_limit is not None:
        r[f'提交文件总页数≤{whole_limit}页'] = f'PASS({n})' if n <= whole_limit else f'FAIL({n})'

    # 2. 图表数量不做全局硬门禁。仍统计图号，便于项目 profile 或
    # 审计报告使用；只有 profile 显式给出 min/max 时才执行数量判定。
    # 兼容国赛中文图题的无冒号样式“图 1 标题”。
    fig_nums = set()
    for t in texts:
        for m in re.finditer(r'图\s*(\d+)(?:\s*[:：]|\s+)', t):
            fig_nums.add(int(m.group(1)))
    fig_min = profile['figures'].get('min')
    fig_max = profile['figures'].get('max')
    if fig_min is None and fig_max is None:
        r['图表数量（按论证需要）'] = f'INFO({len(fig_nums)}，未配置全局数量门槛)'
    else:
        fig_ok = (fig_min is None or len(fig_nums) >= fig_min) and (fig_max is None or len(fig_nums) <= fig_max)
        r[f'图数{fig_min if fig_min is not None else 0}-{fig_max if fig_max is not None else "不限"}'] = f'PASS({len(fig_nums)})' if fig_ok else f'FAIL({len(fig_nums)})'

    # 3. 关键词独立行 + 词条(文本层无法查粗体; 通用判定: 关键词页存在且含>=4个词条/分号)
    kw_page = next((i for i, t in enumerate(texts) if '关键词' in t), None)
    if kw_page is not None:
        kwtext = texts[kw_page].replace('\u037e', '\uff1b')  # U+037E -> ；
        kw_ok = (kwtext.count('\uff1b') >= 3 or kwtext.count('、') >= 3)  # 4个词条需3个分隔符
    else:
        kw_ok = False
    r['关键词独立行+词条'] = f'PASS(第{kw_page + 1}页)' if kw_ok else 'FAIL'

    # 4. 摘要总评段：必须出现在“关键词”之前的摘要末段，不能用正文中
    # 任意位置的“综上”误通过。要求末段同时包含总结性标记和结果/判定信息。
    abstract_before_keywords = full_c.split('关键词', 1)[0]
    abstract_tail = abstract_before_keywords[-420:]
    summary_markers = ('综合以上', '最终结论', '总体结论', '总体而言', '由此可见', '综合来看')
    result_markers = ('厚度', '模型', '结果', '判定', '可靠性')
    abs_ok = (any(marker in abstract_tail for marker in summary_markers)
              and any(marker in abstract_tail for marker in result_markers))
    r['摘要总评段'] = 'PASS' if abs_ok else 'FAIL(摘要末段缺少独立总结段)'

    # 5. 每问小结段(动态: 题目有N问则要求N个小结; 本卷3问, 出现"问题四"才要求第四小结)
    sums = ['问题一小结', '问题二小结', '问题三小结']
    if '问题四' in full_c:
        sums.append('问题四小结')
    miss = [s for s in sums if s not in full_c]
    r['每问小结'] = 'PASS' if not miss else f'FAIL(缺{miss})'

    # 6. 附录顺序: A清单 -> B源码 -> C推导 -> D表格/验证 -> E AI说明
    app = full_c[full_c.find('附录'):]
    seq = profile['appendix_sequence']
    pos = [app.find(s) for s in seq]
    order_ok = all(p >= 0 for p in pos) and pos == sorted(pos)
    r['附录顺序'] = 'PASS' if order_ok else f'FAIL({dict(zip(seq, pos))})'

    # 7. 核心代码在附录(代码特征: def / import; full_c 已去空格)
    #    注: 2026-08-15 用户裁定——附录放核心代码, 完整代码在附件 zip
    code_ok = ('def' in app) and ('import' in app or '完整可运行源码位于支撑材料压缩包' in app)
    r['核心代码在附录'] = 'PASS' if code_ok else 'FAIL'

    # 8. 字体族: 正文宋体+西文TNR, 标题黑体, 代码Consolas(扫描全文, 含回退名)
    fonts = set()
    for i in range(n):
        d = doc[i].get_text('dict')
        for b in d['blocks']:
            for l in b.get('lines', []):
                for s in l['spans']:
                    fonts.add(s['font'])
    fstr = '|'.join(fonts)
    fonts_ok = (('SimSun' in fstr or '宋体' in fstr or 'FandolSong' in fstr or 'Song' in fstr)
                and ('Times' in fstr or 'CMR' in fstr or 'TNR' in fstr)
                and ('SimHei' in fstr or '黑体' in fstr or 'FandolHei' in fstr or 'Hei' in fstr)
                and ('Consolas' in fstr or 'consol' in fstr.lower() or 'Mono' in fstr))
    r['字体族(宋体/TNR/黑体/Consolas)'] = (f'PASS({sorted(fonts)[:6]})' if fonts_ok else f'FAIL({sorted(fonts)[:6]})') if profile['font_check'] else 'PASS(项目格式档案未强制字体族)'

    # 9. 摘要"摘要"二字存在(居中需人工/视觉, 文本层仅查存在)
    r['摘要二字存在'] = 'PASS' if '摘要' in texts[0] else 'FAIL'

    print(f'=== Paper Hard Requirements: {path} ===')
    all_ok = True
    for k, v in r.items():
        ok = str(v).startswith(('PASS', 'INFO'))
        all_ok = all_ok and ok
        print(f"  {'PASS' if ok else 'FAIL'} {k}: {v}")
    print(f'===== 硬性要求清单: {"PASS" if all_ok else "FAIL"} =====')
    return all_ok

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', nargs='?', default='paper.pdf')
    parser.add_argument('--profile', default=None, help='project-specific official formatting profile (JSON)')
    args = parser.parse_args()
    sys.exit(0 if main(args.path, args.profile) else 1)
