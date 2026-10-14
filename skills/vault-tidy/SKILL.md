---
name: vault-tidy
description: >-
  Keep the Obsidian second brain healthy: find broken or ambiguous links, orphan notes, notes without a parent,
  files in the wrong place, and fix them safely (moves only through `brain move`, which rewrites every wikilink);
  archive finished projects. Use when the owner asks to tidy or organise the vault, when lint warnings pile up, or
  before and after any reorganisation. Triggers: "תסדר את המוח השני", "תסדר את הכספת", "יש קישורים שבורים?",
  "תעביר לארכיון", "הפרויקט הסתיים", "tidy the vault", "clean up the notes", "archive this project", "broken links".
---

# Vault tidy

Tool: `B=~/.second-brain/bin/brain`. Always: report → plan → owner's yes for anything that moves or deletes → apply.

## 1. Health report (read-only)
`$B audit` (or `--json`) lists: broken links, ambiguous links (two notes share a name), notes under `Projects/` with
no `up`, and orphans (no note links to them). `$B lint --all` lists place/frontmatter problems.
Summarise for the owner in a short table: problem · count · what you propose.

## 2. Fixes you may apply without asking
- Missing `up` / `type` / `tags` on notes inside a project: fill from the folder (`up: "[[Projects/<Name>/README]]"`).
- Orphans inside a project: `$B docs <Name> --apply` lists them in the README documents table.
- Ambiguous links: rewrite the link to the full path form `[[Projects/<Name>/<file>|label]]`.
- Broken links where the right target is obvious (one candidate): fix the link text.

## 3. Fixes that need the owner's yes
- Moving notes or folders: `$B move <src> <dst>` (dry run, shows every note whose links change) → show → yes →
  `$B move <src> <dst> --apply`. Never `mv` or Finder drag: Obsidian only fixes links for moves made inside the app.
- Archiving a finished project: set `status: done` in its README, then
  `$B move Projects/<Name> _archive/Projects/<Name> --apply`, then `$B moc --apply`.
- Deleting anything: never delete notes; archive instead. Empty folders may go.
- Merging two folders of the same project: move files one by one into the main folder with `$B move`.

## 4. After
`$B audit` and `$B lint --all` again; reply with before → after counts.
