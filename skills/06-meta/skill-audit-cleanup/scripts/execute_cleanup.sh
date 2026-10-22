#!/usr/bin/env bash
# WorkBuddy skill cleanup - archive-based, fully reversible.
# No rm is ever called. All operations are directory moves + JSON edits with .bak.
# Usage:
#   bash execute_cleanup.sh              # dry-run preview
#   bash execute_cleanup.sh --tier1      # archive 5 duplicate/irrelevant skills + dist
#   bash execute_cleanup.sh --tier2      # move 6 low-frequency skills to cold storage
#   bash execute_cleanup.sh --tier3      # disable 3 plugins in settings.json
#   bash execute_cleanup.sh --tier5      # rewrite conflicting web-access description
#   bash execute_cleanup.sh --all        # tier1 + tier2 + tier3 + tier5
#   bash execute_cleanup.sh --rollback   # restore everything from archive + cold
#   bash execute_cleanup.sh --status     # show current layout

set -euo pipefail

SKILLS="/c/Users/USER/.workbuddy/skills"
ARCHIVE="/c/Users/USER/.workbuddy/skills_archive_2026-08-30"
COLD="/c/Users/USER/.workbuddy/skills_cold"
SETTINGS="/c/Users/USER/.workbuddy/settings.json"
PY="C:/Users/USER/.workbuddy/binaries/python/versions/3.13.12/python.exe"
STAMP="20260830"

# tier1: archive (remove from load path)
# NOTE 2026-08-30 user decision: figure-generation and self-improving-agent__skillhub
# are KEPT (duplicate groups left intact on purpose).
TIER1=(agent-browser-core browser-skill memory-setup__skillhub dist)
# tier2: cold storage (mount on demand)
# NOTE 2026-08-30 user decision: all math-modeling skills stay resident (never cold).
TIER2=(expert-behavior-calibration hongzhua-ruanzhu__skillhub)

move_out() {
  local name="$1" dest="$2" label="$3"
  if [ -d "$SKILLS/$name" ]; then
    mkdir -p "$dest"
    if [ -e "$dest/$name" ]; then
      echo "  [SKIP] $name already in $label"
    else
      mv "$SKILLS/$name" "$dest/$name"
      echo "  [MOVE] $name -> $label"
    fi
  else
    echo "  [MISS] $name not found in skills/"
  fi
}

move_in() {
  local name="$1" src="$2" label="$3"
  if [ -d "$src/$name" ] && [ ! -d "$SKILLS/$name" ]; then
    mv "$src/$name" "$SKILLS/$name"
    echo "  [RESTORE] $name <- $label"
  fi
}

do_tier1() {
  echo "== Tier 1: archive duplicate/irrelevant skills (-5 entries) =="
  for s in "${TIER1[@]}"; do move_out "$s" "$ARCHIVE" "archive"; done
}

do_tier2() {
  echo "== Tier 2: move low-frequency skills to cold storage (-6 entries) =="
  for s in "${TIER2[@]}"; do move_out "$s" "$COLD" "cold"; done
}

do_tier3() {
  echo "== Tier 3: disable plugins in settings.json (-17 entries) =="
  cp "$SETTINGS" "$SETTINGS.bak-$STAMP"
  echo "  [BACKUP] settings.json -> settings.json.bak-$STAMP"
  "$PY" - <<'PYEOF'
import json, io, os
p = r"C:\Users\USER\.workbuddy\settings.json"
d = json.load(io.open(p, encoding="utf-8"))
ep = d.setdefault("enabledPlugins", {})
targets = {
    "tencent-docx@workbuddy-builtin": False,
    "weixinpay@workbuddy-builtin": False,
    "tabbit@tabbit-browser": False,
}
for k, v in targets.items():
    old = ep.get(k, "(absent -> default true)")
    ep[k] = v
    print(f"  [SET] {k}: {old} -> {v}")
io.open(p, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2))
print("  [OK] settings.json written")
PYEOF
  echo "  >> Restart WorkBuddy for this to take effect."
}

do_tier5() {
  echo "== Tier 5: rewrite web-access description (resolve routing conflict) =="
  local f="$SKILLS/web-access/SKILL.md"
  [ -f "$f" ] || { echo "  [MISS] web-access/SKILL.md not found"; return 0; }
  cp "$f" "$f.bak-$STAMP"
  echo "  [BACKUP] SKILL.md -> SKILL.md.bak-$STAMP"
  "$PY" - <<'PYEOF'
import io, re
p = r"C:\Users\USER\.workbuddy\skills\web-access\SKILL.md"
old = "所有联网操作必须通过此 skill 处理，包括：搜索、网页抓取、登录后操作、网络交互等。 触发场景：用户要求搜索信息、查看网页内容、访问需要登录的网站、操作网页界面、抓取社交媒体内容（小红书、微博、推特等）、读取动态渲染页面、以及任何需要真实浏览器环境的网络任务。"
new = "搜索与网页内容抓取（静态页面、API 响应、公开网页、文档站点）。触发场景：搜索信息、抓取页面正文、批量读取公开网页。需要真实浏览器交互、登录态操作、点击跳转流程时改用 agent-browser 技能，不要用本技能。"
t = io.open(p, encoding="utf-8").read()
if old in t:
    io.open(p, "w", encoding="utf-8").write(t.replace(old, new))
    print("  [OK] description rewritten")
else:
    print("  [WARN] exact pattern not found; manual edit required")
PYEOF
}

do_rollback() {
  echo "== Rollback: restore from archive + cold =="
  for s in "${TIER1[@]}"; do move_in "$s" "$ARCHIVE" "archive"; done
  for s in "${TIER2[@]}"; do move_in "$s" "$COLD" "cold"; done
  if [ -f "$SETTINGS.bak-$STAMP" ]; then
    cp "$SETTINGS.bak-$STAMP" "$SETTINGS"
    echo "  [RESTORE] settings.json from backup"
  fi
  local f="$SKILLS/web-access/SKILL.md"
  if [ -f "$f.bak-$STAMP" ]; then
    mv "$f.bak-$STAMP" "$f"
    echo "  [RESTORE] web-access/SKILL.md from backup"
  fi
}

do_status() {
  echo "== Active skills in ~/.workbuddy/skills =="
  ls -1 "$SKILLS" 2>/dev/null | grep -v '^\.' || true
  echo
  echo "== Cold storage (~/.workbuddy/skills_cold) =="
  ls -1 "$COLD" 2>/dev/null || echo "  (empty)"
  echo
  echo "== Archive (~/.workbuddy/skills_archive_2026-08-30) =="
  ls -1 "$ARCHIVE" 2>/dev/null || echo "  (empty)"
}

preview() {
  echo "DRY-RUN preview. Nothing will be changed."
  echo
  echo "-- Tier 1 archive (5 skills + dist) --"
  printf '   %s\n' "${TIER1[@]}"
  echo "-- Tier 2 cold storage (6 skills) --"
  printf '   %s\n' "${TIER2[@]}"
  echo "-- Tier 3 disable plugins (3) --"
  echo "   tencent-docx@workbuddy-builtin (13 entries)"
  echo "   weixinpay@workbuddy-builtin    (3 entries)"
  echo "   tabbit@tabbit-browser          (1 entry)"
  echo "-- Tier 5 rewrite --"
  echo "   web-access/SKILL.md description"
  echo
  echo "Run with --all to execute, or pick individual tiers."
}

case "${1:---preview}" in
  --tier1) do_tier1 ;;
  --tier2) do_tier2 ;;
  --tier3) do_tier3 ;;
  --tier5) do_tier5 ;;
  --all)   do_tier1; do_tier2; do_tier3; do_tier5 ;;
  --rollback) do_rollback ;;
  --status) do_status ;;
  *) preview ;;
esac
