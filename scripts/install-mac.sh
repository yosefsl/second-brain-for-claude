#!/bin/bash
# Installs the Obsidian second brain for Claude Code on macOS, for the current user.
# No sudo, no Xcode, no Homebrew, no git. Safe to run again: it upgrades in place and never
# overwrites notes that already exist in the vault.
#
# Env (all optional):
#   SB_VAULT  vault folder            (default ~/SecondBrain; keep it out of iCloud)
#   SB_RTL    1 = notes read right-to-left (Hebrew/Arabic), 0 = left-to-right   (default 1)
#   SB_NO_OPEN=1        do not open Obsidian at the end
#   SB_NO_QUIT=1        do not close a running Obsidian (tests only: Obsidian may then drop the new vault from its list)
#   SB_SKIP_OBSIDIAN=1  do not download Obsidian (tests)
#   SB_OBSIDIAN_DMG=<path>  install Obsidian from a .dmg already on disk instead of downloading
#   SB_APPS=<dir>       where to put Obsidian.app (default /Applications, or ~/Applications)
set -euo pipefail

PKG="$(cd "$(dirname "$0")/.." && pwd)"
SB_HOME="${SB_HOME:-$HOME/.second-brain}"
VAULT="${SB_VAULT:-$HOME/SecondBrain}"
RTL="${SB_RTL:-1}"
export SB_HOME
step() { printf '\n==> %s\n' "$1"; }
mkdir -p "$SB_HOME"

# 1. A Python that does not trigger the Xcode tools dialog
step "1/4 Python"
PY=""; [ "${SB_FORCE_UV:-0}" = "1" ] && SKIP_SYS=1 || SKIP_SYS=0
py_ok() { "$1" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; }
[ "$SKIP_SYS" = "1" ] || for cand in "$(command -v python3 2>/dev/null || true)" /opt/homebrew/bin/python3 /usr/local/bin/python3; do
  [ -n "$cand" ] && [ -x "$cand" ] || continue
  if [ "$cand" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then continue; fi  # stub -> Xcode popup
  if py_ok "$cand"; then PY="$cand"; break; fi
done
if [ "$SKIP_SYS" = "0" ] && [ -z "$PY" ] && [ -x /usr/bin/python3 ] && xcode-select -p >/dev/null 2>&1 && py_ok /usr/bin/python3; then PY=/usr/bin/python3; fi
if [ -z "$PY" ]; then
  echo "no usable python3; installing a private copy with uv (inside $SB_HOME)"
  UV="$SB_HOME/uv/uv"
  export UV_PYTHON_INSTALL_DIR="$SB_HOME/python"
  for attempt in 1 2 3; do
    if [ ! -x "$UV" ]; then
      curl -LsSf --retry 3 https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="$SB_HOME/uv" UV_NO_MODIFY_PATH=1 INSTALLER_NO_MODIFY_PATH=1 sh >/dev/null || true
    fi
    [ -x "$UV" ] && "$UV" python install 3.12 && break
    echo "network hiccup, retrying ($attempt/3)"; sleep 5
  done
  PY="$("$UV" python find 3.12)"
fi
"$PY" --version
echo "python: $PY"

# 2. Obsidian (official signed build from Obsidian's GitHub releases)
step "2/4 Obsidian"
APP=""
if [ -n "${SB_APPS:-}" ]; then CANDS=("$SB_APPS/Obsidian.app"); else CANDS=(/Applications/Obsidian.app "$HOME/Applications/Obsidian.app"); fi
for a in "${CANDS[@]}"; do [ -d "$a" ] && APP="$a"; done
if [ -n "$APP" ]; then
  echo "already installed: $APP"
elif [ "${SB_SKIP_OBSIDIAN:-0}" = "1" ]; then
  echo "skipped (SB_SKIP_OBSIDIAN=1)"
else
  TMP="$(mktemp -d)"
  if [ -n "${SB_OBSIDIAN_DMG:-}" ]; then
    cp "$SB_OBSIDIAN_DMG" "$TMP/Obsidian.dmg"
  else
    URL="$(curl -fsSL https://api.github.com/repos/obsidianmd/obsidian-releases/releases/latest \
      | "$PY" -c 'import json,sys; a=[x["browser_download_url"] for x in json.load(sys.stdin)["assets"] if x["name"].endswith(".dmg")]; print(a[0])')"
    echo "downloading $URL (about 220 MB)"
    curl -fSL -C - --retry 3 --progress-bar "$URL" -o "$SB_HOME/Obsidian.dmg.part" && mv "$SB_HOME/Obsidian.dmg.part" "$TMP/Obsidian.dmg"
  fi
  hdiutil attach "$TMP/Obsidian.dmg" -nobrowse -readonly -quiet -mountpoint "$TMP/mnt"
  DEST="${SB_APPS:-/Applications}"
  [ -w "$DEST" ] || { DEST="$HOME/Applications"; mkdir -p "$DEST"; }
  ditto "$TMP/mnt/Obsidian.app" "$DEST/Obsidian.app"
  hdiutil detach "$TMP/mnt" -quiet || true
  rm -rf "$TMP"
  APP="$DEST/Obsidian.app"
  echo "installed: $APP"
fi

# 3. Vault + Claude Code config (skills, instructions, Stop hook, vault access, Obsidian registration)
step "3/4 Vault and Claude Code"
if [ "${SB_NO_QUIT:-0}" != "1" ] && pgrep -xq Obsidian; then
  # Obsidian rewrites its vault list on quit; close it so the new vault is not lost.
  osascript -e 'quit app "Obsidian"' >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do pgrep -xq Obsidian || break; sleep 1; done
fi
"$PY" "$PKG/tools/setup.py" install --pkg "$PKG" --vault "$VAULT" --python "$PY" --rtl "$RTL"
cp -f "$PKG/scripts/uninstall-mac.sh" "$SB_HOME/uninstall.sh"; cp -f "$PKG/tools/setup.py" "$SB_HOME/setup.py"; chmod +x "$SB_HOME/uninstall.sh"
"$SB_HOME/bin/brain" moc --apply >/dev/null

# 4. Open the vault and check everything
step "4/4 Check"
if [ "${SB_NO_OPEN:-0}" != "1" ] && [ -n "$APP" ]; then
  ENC="$("$PY" -c 'import sys,urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$VAULT")"
  open "obsidian://open?path=$ENC" || open -a "$APP"
fi
if "$SB_HOME/bin/brain" doctor; then
  echo "INSTALL_OK vault=$VAULT"
else
  [ "${SB_SKIP_OBSIDIAN:-0}" = "1" ] && echo "INSTALL_OK vault=$VAULT (Obsidian checks skipped)" || { echo "INSTALL_FAIL see the FAIL lines above"; exit 1; }
fi
