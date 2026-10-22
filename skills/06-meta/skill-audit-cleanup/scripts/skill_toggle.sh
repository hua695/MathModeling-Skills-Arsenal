#!/usr/bin/env bash
# Mount / unmount cold-storage skills.
# Usage:
#   bash skill_toggle.sh on  <skill-name>
#   bash skill_toggle.sh off <skill-name>
#   bash skill_toggle.sh status
#   bash skill_toggle.sh list

set -euo pipefail

SKILLS="/c/Users/USER/.workbuddy/skills"
COLD="/c/Users/USER/.workbuddy/skills_cold"

mount_on() {
  local n="$1"
  if [ ! -d "$COLD/$n" ]; then
    echo "[ERR] '$n' not in cold storage. Available:"; ls -1 "$COLD" 2>/dev/null; exit 1
  fi
  if [ -d "$SKILLS/$n" ]; then
    echo "[SKIP] '$n' already active"; exit 0
  fi
  mv "$COLD/$n" "$SKILLS/$n"
  echo "[ON] $n mounted -> restart not required, new session picks it up"
}

mount_off() {
  local n="$1"
  if [ ! -d "$SKILLS/$n" ]; then
    echo "[SKIP] '$n' is not active"; exit 0
  fi
  mkdir -p "$COLD"
  mv "$SKILLS/$n" "$COLD/$n"
  echo "[OFF] $n unmounted -> cold storage"
}

show_status() {
  echo "== Active (registered) =="
  ls -1 "$SKILLS" 2>/dev/null | grep -v '^\.' || true
  echo
  echo "== Cold (not registered) =="
  ls -1 "$COLD" 2>/dev/null || echo "  (empty)"
}

case "${1:-status}" in
  on)  [ -n "${2:-}" ] || { echo "usage: $0 on <skill-name>"; exit 1; }; mount_on "$2" ;;
  off) [ -n "${2:-}" ] || { echo "usage: $0 off <skill-name>"; exit 1; }; mount_off "$2" ;;
  status|list) show_status ;;
  *) echo "usage: $0 {on|off|status} [skill-name]"; exit 1 ;;
esac
