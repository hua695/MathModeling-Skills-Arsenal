# -*- coding: utf-8 -*-
"""追加 FD-660（自研·检索系统）元失败经验，并清掉之前 bash 引号坑写坏的 FD-522 空块"""
import os, re, argparse
from pathlib import Path

def main(argv=None):
    parser = argparse.ArgumentParser(description='追加检索系统失败经验；默认只预览。')
    parser.add_argument('--skill-root', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--apply', action='store_true', help='确认后写回 failure_database.md。')
    parser.add_argument('--dry-run', action='store_true', help='只预览变更（默认行为）。')
    args = parser.parse_args(argv)
    apply_changes = bool(args.apply and not args.dry_run)
    p = Path(args.skill_root) / 'failure_database.md'
    txt = open(p, encoding='utf-8').read()

# 1) 删掉写坏的空 FD-522（自研·检索系统）块
    txt = re.sub(r'## FD-522（自研·检索系统）\n\n```yaml\n(?:.|\n)*?```\n', '', txt)

# 2) 找下一个可用 ID
    nums = [int(m) for m in re.findall(r'^## FD-(\d+)', txt, re.M)]
    nid = max(nums) + 1

    entry = f'''

---

## FD-{nid}（自研·检索系统）

```yaml
failure_id: FD-{nid}
problem_type: 检索系统
method: ranking 的 reuse×freshness 加权排序
failure: 直接同题先例（低复用/略旧）被压出 TOP-12，被无关泛化条目（质检/响应面）占据
cause: reuse_factor(低复用=0.5)×freshness(2020年≈0.53) 乘积惩罚过重，压过了相似度
signal: n_matched=1433 但 TOP-12 全是 noise；relevant_in_pool 需手动补录
lesson: 检索排序必须给同题先例（source 含题名关键词）强 boost，不能让复用率×新鲜度主导；直接相关 > 高频
source: 2020国赛B穿越沙漠测试 | 经验驱动首次验证复盘 | 2026
confidence: 高
```
'''
    if apply_changes:
        open(p, 'w', encoding='utf-8').write(txt)
        with open(p, 'a', encoding='utf-8') as f:
            f.write(entry)
    print(f"{'已追加' if apply_changes else '预计追加'} FD-{nid}（自研·检索系统）")


if __name__ == '__main__':
    main()
