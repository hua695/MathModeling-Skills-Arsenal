#!/usr/bin/env sh
set -eu

if [ "$#" -lt 1 ]; then
  echo "Usage: ./install.sh <agent-skill-parent-directory> [agent-label]" >&2
  exit 2
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET=$1
AGENT=${2:-generic}
python3 "$SCRIPT_DIR/scripts/install_agent_skill.py" --target "$TARGET" --agent "$AGENT"
