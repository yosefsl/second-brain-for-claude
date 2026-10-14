#!/bin/bash
# Self-test of tools/brain.py on a throwaway vault. Usage: bash scripts/selftest.sh [python]
set -euo pipefail
PKG="$(cd "$(dirname "$0")/.." && pwd)"
PY="${1:-python3}"
T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT
export SB_HOME="$T/sb" SB_VAULT="$T/vault"
B() { "$PY" "$PKG/tools/brain.py" "$@"; }
fail() { echo "SELFTEST_FAIL: $1"; exit 1; }

HOME="$T/home" "$PY" "$PKG/tools/setup.py" install --pkg "$PKG" --vault "$SB_VAULT" --python "$PY" --rtl 1 >/dev/null
B moc --apply >/dev/null
B lint --all | grep -q "clean" || { B lint --all; fail "template not lint-clean"; }

B new-project "Bakery-Website" --title "אתר מאפייה" --summary "test" >/dev/null
[ -f "$SB_VAULT/Projects/Bakery-Website/README.md" ] || fail "new-project"
grep -q "Projects/Bakery-Website/README" "$SB_VAULT/Projects/Projects-MOC.md" || fail "moc line"

cat > "$SB_VAULT/Projects/Bakery-Website/2026-01-02-menu-research.md" <<'N'
---
title: "מחקר תפריט"
type: research
date: 2026-01-02
tags: [bakery-website, research]
up: "[[Projects/Bakery-Website/README]]"
related: []
---
See [[2026-01-03-plan]] and [[Projects/Getting-Started/README|guide]].
N
cat > "$SB_VAULT/Projects/Bakery-Website/2026-01-03-plan.md" <<'N'
---
title: "plan"
type: plan
date: 2026-01-03
tags: [bakery-website, plan]
up: "[[Projects/Bakery-Website/README]]"
---
Back to [[2026-01-02-menu-research|research]].
N
cat > "$SB_VAULT/Projects/Bakery-Website/bad.md" <<'N'
no frontmatter, link to [[does-not-exist]]
N
B lint --files "$SB_VAULT/Projects/Bakery-Website/2026-01-02-menu-research.md" | grep -q clean || fail "good note flagged"
B lint --files "$SB_VAULT/Projects/Bakery-Website/bad.md" | grep -q "no frontmatter" || fail "bad note not flagged"
B lint --files "$SB_VAULT/Projects/Bakery-Website/bad.md" --strict >/dev/null && fail "strict exit code"
B audit --json | "$PY" -c 'import json,sys; d=json.load(sys.stdin); assert any("does-not-exist" in x for x in d["broken"]), d' || fail "audit broken"
rm "$SB_VAULT/Projects/Bakery-Website/bad.md"

B docs Bakery-Website --apply >/dev/null
grep -q "2026-01-02-menu-research" "$SB_VAULT/Projects/Bakery-Website/README.md" || fail "docs table"

B move Projects/Bakery-Website/2026-01-03-plan.md Projects/Bakery-Website/plans/2026-01-03-plan.md >/dev/null
[ -f "$SB_VAULT/Projects/Bakery-Website/2026-01-03-plan.md" ] || fail "dry run moved the file"
B move Projects/Bakery-Website/2026-01-03-plan.md Projects/Bakery-Website/plans/2026-01-03-plan.md --apply >/dev/null
grep -q "\[\[Projects/Bakery-Website/plans/2026-01-03-plan\]\]" "$SB_VAULT/Projects/Bakery-Website/2026-01-02-menu-research.md" || fail "link rewrite"

sed -i.bak 's/^status: active/status: done/' "$SB_VAULT/Projects/Bakery-Website/README.md"; rm -f "$SB_VAULT/Projects/Bakery-Website/README.md.bak"
B move Projects/Bakery-Website _archive/Projects/Bakery-Website --apply >/dev/null
B moc --apply >/dev/null
grep -q "_archive/Projects/Bakery-Website/README" "$SB_VAULT/Projects/Projects-MOC.md" || fail "archive in moc"
grep -q "\[\[_archive/Projects/Bakery-Website/plans/2026-01-03-plan\]\]" "$SB_VAULT/_archive/Projects/Bakery-Website/2026-01-02-menu-research.md" || fail "folder move rewrite"
B audit --json | "$PY" -c 'import json,sys; d=json.load(sys.stdin); assert not d["broken"], d["broken"]' || fail "broken links after moves"

echo '{"stop_hook_active": false}' | B lint --hook --recent 600 >/dev/null || fail "hook exit code"
HOME="$T/home" "$PY" "$PKG/tools/setup.py" install --pkg "$PKG" --vault "$SB_VAULT" --python "$PY" --rtl 1 >/dev/null
[ "$(grep -c 'second-brain:start' "$T/home/.claude/CLAUDE.md")" = "1" ] || fail "block duplicated on reinstall"
[ "$(grep -c 'lint --hook' "$T/home/.claude/settings.json")" = "1" ] || fail "hook duplicated on reinstall"
HOME="$T/home" "$PY" "$PKG/tools/setup.py" uninstall >/dev/null
grep -q "brain\|$SB_VAULT" "$T/home/.claude/settings.json" && fail "uninstall left settings"
[ -d "$SB_VAULT/Projects" ] || fail "uninstall touched the vault"
echo "SELFTEST_OK"
