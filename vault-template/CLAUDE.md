# CLAUDE.md: rules of this second brain (for every agent: Claude Code, Codex, Cursor)

This Obsidian vault is the owner's **second brain**: the long-term memory of all projects, shared by the owner
(who reads it in Obsidian) and every AI agent (who reads and writes the files). It is not an archive dump.
Every deliverable made for a project is saved here, linked, and reachable from the projects hub.
Write note bodies in the owner's language; keep commands, paths and field names in English.

## 1. Where things go
| What | Where | File name | Required |
|---|---|---|---|
| Project | `Projects/<Name>/` | `README.md` = the project hub | a line in `Projects/Projects-MOC.md` (`brain moc --apply`) |
| Document, research, plan, meeting notes, handoff | the project folder | `YYYY-MM-DD-<slug>.md` | full frontmatter (§2) + a row in the README documents table (`brain docs <Name> --apply`) |
| Raw input (transcripts, screenshots, pasted messages, exports) | `Projects/<Name>/intake/` | `YYYY-MM-DD-<slug>.<ext>` | linked from the note that uses it |
| Versions of one deliverable | `Projects/<Name>/versions/<Vn>/` | | never sibling folders like `<Name>-v2` |
| Reusable know-how, templates, checklists | `_library/` | | |
| Images and files embedded in notes | `_attachments/` | | |
| Finished or dormant projects | `_archive/Projects/<Name>/` | | read-only; move with `brain move` |

Allowed top level: `Projects/`, `_library/`, `_archive/`, `_attachments/`, `CLAUDE.md`, `AGENTS.md`, `Home.md`.
Do not create other top-level folders. A new project = one folder in `Projects/` (`brain new-project <Name>`).

## 2. Frontmatter of every note
```yaml
---
title: "Title in the owner's language"
type: note | research | plan | meeting | decision | handoff | prompt | learning | reference | asset | project
date: YYYY-MM-DD
tags: [<project-slug>, <type>]        # exactly two: the project folder slug + the type
up: "[[Projects/<Name>/README]]"      # the parent; a note without `up` is lost
related: ["[[...]]"]                  # notes this one mentions; add the link back on the other note too
---
```
Dated deliverables (`research`, `plan`, `meeting`, `handoff`, `prompt`, `learning`) start with `YYYY-MM-DD-`.
Living files (`README.md`, specs that keep changing) have no date in the name. Never rename existing files to fit.
Cross-project links use the full path: `[[Projects/<Name>/<file>|label]]`.

## 3. Two kinds of memory (do not mix them)
- **This vault = facts about the work**: what each project is, decisions, documents, status, what was delivered.
- **Claude Code memory (the agent's own memory folder) = how to work with the owner**: preferences,
  corrections, lessons. Learning-loop rules go there (skill `calibrate`), never into the vault.

## 4. Closing any turn that created or changed notes
1. File in the right place, full frontmatter. 2. `up` + `related`, and the link back from the parent / README.
3. `brain docs <Name> --apply` and `brain moc --apply`. 4. Project README "Now" section reflects reality.
5. `brain lint` is clean for the files you touched (it also runs on its own when a Claude Code turn ends).

## 5. Do not touch
`.obsidian/` (Obsidian's own settings), `_archive/` contents (read-only), files the owner wrote by hand
(add to them, do not rewrite them) unless asked. No passwords, API keys or tokens in any note.

## 6. Tools (`brain`, installed with the package)
`brain where` · `brain doctor` · `brain lint [--all]` · `brain audit` · `brain new-project` · `brain docs` ·
`brain moc` · `brain move SRC DST [--apply]` (the only safe way to move notes: it rewrites every wikilink) ·
`brain recent`. Write commands are dry runs until `--apply`.
