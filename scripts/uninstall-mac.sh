#!/bin/bash
# Removes the second-brain skills, instructions, hook and tool from Claude Code.
# The vault (your notes) and the Obsidian app are NOT touched.
set -euo pipefail
SB_HOME="${SB_HOME:-$HOME/.second-brain}"
PY="$("/usr/bin/env" sed -n 's/.*"python": "\(.*\)".*/\1/p' "$SB_HOME/config.json" 2>/dev/null | head -1)"
PKG_SETUP="$(cd "$(dirname "$0")" && pwd)/../tools/setup.py"
[ -f "$PKG_SETUP" ] || PKG_SETUP="$SB_HOME/setup.py"
"${PY:-python3}" "$PKG_SETUP" uninstall
rm -rf "$SB_HOME/bin"
echo "UNINSTALL_OK (vault kept: $(sed -n 's/.*"vault": "\(.*\)".*/\1/p' "$SB_HOME/config.json" 2>/dev/null))"
