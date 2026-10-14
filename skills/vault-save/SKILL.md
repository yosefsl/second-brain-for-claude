---
name: vault-save
description: >-
  Save any deliverable (report, plan, research, meeting summary, brief, decision, a copy of an artifact or page) into
  the Obsidian second brain correctly in one pass: dated file in the right project, full frontmatter, `up` +
  `related` links both ways, the project README documents table, the projects hub, then lint. Do it in the same turn
  the deliverable is made, never offered as optional. Triggers: "תשמור", "תשמור במוח השני", "תשמור בכספת",
  "זה שמור?", "תקשר את זה", "תוסיף לפרויקט", "save it", "save to the vault", "is this saved?", "link it".
---

# Save → link → hub → lint

Tool: `B=~/.second-brain/bin/brain`; vault: `$($B where)`. Rules: `<vault>/CLAUDE.md`.

## 1. Pick the place
- Which project? From the conversation; if none fits and the work will continue, open one (skill `second-brain` §2).
  One-off with no project: ask once, in one short question, which project it belongs to.
- Path: `Projects/<Name>/YYYY-MM-DD-<kebab-slug>.md`. Raw inputs (screenshots, transcripts, exports) →
  `Projects/<Name>/intake/YYYY-MM-DD-<slug>.<ext>`, linked from the note that uses them.
- Before writing, check the folder (`ls`): update an existing note on the same topic instead of making a near-copy.

## 2. Write the file
```yaml
---
title: "<title in the owner's language>"
type: research | plan | meeting | decision | note | handoff | prompt | reference | asset
date: YYYY-MM-DD
tags: [<project-folder-slug>, <type>]     # slug = folder name lowercased, non-letters -> "-"
up: "[[Projects/<Name>/README]]"
related: ["[[Projects/<Name>/<sibling-note>]]"]
---
```
Add `cssclasses: [rtl]` when `rtl` is true in `~/.second-brain/config.json`. Body: a one-line summary at the top,
then the content. The full deliverable, not a summary of it. An HTML page or artifact: save the `.html` next to the
`.md` with the same name, and put the readable content (tables, text) in the `.md`.

## 3. Link both ways (same turn, no question)
1. Every note you mention goes into `related`, and that note gets this one in its `related` too.
2. `$B docs <Name> --apply` rebuilds the README documents table; then update the README "Now" section by hand
   if the deliverable changes what is next, and set `updated:` to today.
3. `$B moc --apply` refreshes the projects hub.

## 4. Check
`$B lint --files <the files you wrote>` → `brain lint: clean`. Fix every warning you caused.
Reply with the vault path(s) of what you saved (`Projects/<Name>/<file>.md`).

## Optional: version history
If the vault is a git repository (`git -C "$($B where)" rev-parse` succeeds), commit only your files:
`git -C <vault> add -- <files> && git -C <vault> commit -m "<what>"`. Never push anywhere the owner did not set up.
