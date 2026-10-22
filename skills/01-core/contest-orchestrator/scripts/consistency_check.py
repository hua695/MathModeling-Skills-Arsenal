# -*- coding: utf-8 -*-
"""一致性检查：论文表 vs 结果JSON vs 布局CSV。占位实现，按需扩展。"""
import json, sys, csv, re, os


def extract_paper_numbers(paper_md):
    """从论文 md 提取数值（演示）。"""
    nums = re.findall(r'[\d,]+\.?\d*', open(paper_md, encoding='utf-8').read())
    return [n.replace(',', '') for n in nums if '.' in n or len(n) >= 4]


def load_json(path):
    return json.load(open(path, encoding='utf-8'))


def check_layout_bbox(csv_path, expected_wh):
    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    mx = my = 0
    for r in rows[1:]:
        try:
            x, y, w, h = float(r[1]), float(r[2]), float(r[3]), float(r[4])
            mx = max(mx, x + w); my = max(my, y + h)
        except Exception:
            pass
    ok = (round(mx) == expected_wh[0] and round(my) == expected_wh[1])
    print(f'布局 {csv_path}: bbox={mx:.0f}×{my:.0f} vs 论文 {expected_wh} {"✓" if ok else "✗"}')
    return ok


if __name__ == '__main__':
    # 用法: python consistency_check.py paper.md result.json layout.csv WxH
    if len(sys.argv) >= 5:
        paper, res_json, layout, wh = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
        W, H = map(int, wh.lower().split('x'))
        d = load_json(res_json)
        print(f'结果JSON {res_json}: 关键值 = {d}')
        check_layout_bbox(layout, (W, H))
    else:
        print(__doc__)
