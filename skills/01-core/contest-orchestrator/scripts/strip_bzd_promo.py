#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/strip_bzd_promo.py — BZD 评审 HTML 推广块剥离工具（Phase 3 · 原创代码）

背景：bzd-review-paper 的 HTML 输出带 BZD 数模社推广段
      （"✨ 如需进一步详细的论文检查… BZD数模社 / QQ群 / 微信"），
      直接用作交付物时须剥离，但必须保留评审内容
      （最终得分 / 详细评分 / 评委式评价 / 分维度表 / 修改建议等）。

策略（两段式，防模板升级漏检）：
  ① 结构剥离：删除 <aside class="card service" ...>...</aside> 推广块
     （class 含 "service" 的 aside，属性顺序不限）
  ② 关键词兜底：若仍残留 推广关键词（BZD数模社 / QQ数模交流群 / 资料通知群 /
     微信（个性化定制）），从关键词位置向上回溯到最近的块级容器
     （aside/section/div/p/footer），整块删除。

用法：
    python strip_bzd_promo.py <input.html> [output.html]
    不传 output 时默认写 <input 同目录>/<stem>.stripped.html
    传 "-" 作为 output 则打印到 stdout。

验证示例：
    python strip_bzd_promo.py sample/bzd_reports/v_final_bzd_review.html
    → 断言输出无 "BZD数模社/QQ群/微信"，且保留 "最终得分/详细评分/评委"
"""
import re
import sys
from pathlib import Path

# 推广关键词（命中即视为推广残留）
PROMO_KEYWORDS = [
    'BZD数模社', 'QQ数模交流群', '资料通知群', '微信（个性化定制）',
    '如需进一步详细的论文检查',
]
# 评审保留关键词（用于断言评审内容未被误删）
REVIEW_KEYWORDS = ['最终得分', '详细评分', '评委']

# 块级容器开始标签（向上回溯用）
_BLOCK_START = re.compile(r'<(aside|section|div|p|footer)\b[^>]*>', re.I)


def _strip_service_asides(html: str) -> str:
    """① 结构剥离：删除 class 含 service 的 <aside> 块。"""
    pat = re.compile(r'<aside\b[^>]*class="[^"]*service[^"]*"[^>]*>.*?</aside>',
                     re.I | re.S)
    return pat.sub('', html)


def _strip_promo_containers(html: str) -> str:
    """② 关键词兜底：删除含推广关键词的最近块级容器。"""
    for kw in PROMO_KEYWORDS:
        while True:
            m = re.search(re.escape(kw), html)
            if not m:
                break
            # 向上回溯最近块级开始标签
            prefix = html[:m.start()]
            starts = list(_BLOCK_START.finditer(prefix))
            if not starts:
                html = html[:m.start()] + html[m.end():]
                continue
            tag = starts[-1]
            tag_name = tag.group(1)
            # 从该开始标签起，找第 1 个配对闭合标签（简单配对，块内不再嵌套同名块）
            rest = html[tag.start():]
            close = re.search(rf'</{tag_name}>', rest, re.I)
            if close:
                html = html[:tag.start()] + html[tag.start() + close.end():]
            else:
                html = html[:tag.start()] + html[m.end():]
    return html


def strip_bzd_promo(html: str) -> str:
    """剥离 BZD 推广段，保留评审内容。返回清理后的 HTML。"""
    out = _strip_service_asides(html)
    out = _strip_promo_containers(out)
    # 清理剥离后可能残留的空行/多余空白
    out = re.sub(r'\n{3,}', '\n\n', out)
    return out.strip()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    html = src.read_text(encoding='utf-8')
    out_html = strip_bzd_promo(html)

    out_path = None
    if len(sys.argv) >= 3:
        if sys.argv[2] == '-':
            sys.stdout.write(out_html)
            return
        out_path = Path(sys.argv[2])
    else:
        out_path = src.with_name(src.stem + '.stripped.html')
    out_path.write_text(out_html, encoding='utf-8')

    # 断言
    assert 'BZD数模社' not in out_html, '剥离失败：仍含 BZD数模社'
    assert 'QQ群' not in out_html and 'QQ数模交流群' not in out_html, '剥离失败：仍含 QQ 推广'
    assert '微信' not in out_html, '剥离失败：仍含 微信 推广'
    for kw in REVIEW_KEYWORDS:
        if kw in html and kw not in out_html:
            print(f'[warn] 输入含评审关键词 "{kw}" 但输出中缺失——请人工确认是否误删')
    removed = len(html) - len(out_html)
    print(f'OK: {src.name} → {out_path.name}（移除 {removed} 字符）')
    print(f'    推广字样: BZD数模社/QQ群/微信 = 0；评审内容保留')


if __name__ == '__main__':
    main()
