---
name: second-brain
description: >-
  The owner's Obsidian second brain: the long-term memory of every project, shared between the owner (Obsidian) and
  Claude (files). Use at the start of any work on a project (read its hub first), when the owner asks what is going on
  in a project, opens a new project, refers to "the brain", "the vault", "Obsidian" or "my notes", or when you need to
  know where something belongs. Covers the vault map, the read-first routine, opening a project, the two kinds of
  memory (vault = facts about the work, Claude memory = how to work with the owner) and the `brain` tool.
  Triggers: "המוח השני", "בכספת", "באובסידיאן", "פרויקט חדש", "מה המצב בפרויקט", "מה עשינו ב", "תזכור ש",
  "second brain", "vault", "Obsidian", "new project", "what's the status of", "where did we leave".
---

# Second brain (Obsidian)

The vault path: run `~/.second-brain/bin/brain where`. The vault's own rules are in `<vault>/CLAUDE.md` — read it
once per session before writing anything there; it wins over this skill if they differ.

## 1. Read before you answer or build
When a request touches a project (by name, by client, by topic):
1. `brain where`, then open `<vault>/Projects/Projects-MOC.md` and find the project (match loosely; ask only if two fit).
2. Read the project's `README.md` (sections "Now", "Decisions", the documents table) and the newest 2-3 dated notes.
   `brain recent --days 14` shows what changed lately across the vault.
3. If a handoff note exists (`*-handoff.md`, `status: ready-to-run`), it is the latest state: read it fully.
4. Answer from the files, cite them as `Projects/<Name>/<file>`, and say what is missing instead of guessing.

## 2. Opening a project
`~/.second-brain/bin/brain new-project "<Folder-Name>" --title "<title in the owner's language>" --summary "<1-2 lines>"`
creates `Projects/<Folder-Name>/README.md` (+ `intake/`) and adds it to the hub. Folder names: Latin letters, words
joined by `-` (e.g. `Bakery-Website`). Then fill "Now" with the first steps. Never create a second folder for the same
project or a sibling folder for a new version (use `versions/<Vn>/` inside).

## 3. Writing into the vault
Every save follows skill `vault-save` (file, frontmatter, links, hub, lint) in the same turn, without asking
"should I save it?". Small facts the owner tells you ("the client's launch moved to May") go into the project
README ("Now" or "Decisions", with the date), not into a new note.

## 4. Two kinds of memory
| Kind | Lives in | Example |
|---|---|---|
| Facts about the work | the vault | "Launch moved to 3 May", the brief, the research, what was delivered |
| How to work with the owner | your own memory folder (the auto-memory directory in your system prompt) | "Always ask in one short question", "she prefers tables" |
Corrections from the owner about *how you work* go to memory via skill `calibrate`, never into the vault.
Facts about a project never go into memory: memory would go stale while the vault stays the source of truth.

## 5. Language and tone
Talk to the owner in their language, short and plain. Note bodies in the owner's language; commands, paths,
field names in English. When `rtl` is on in `~/.second-brain/config.json`, add `cssclasses: [rtl]` to new notes.

## 6. Never
- Never drive the Obsidian app with clicks to "check" something; read and write the files, Obsidian picks them up live.
- Never edit `.obsidian/` or write into `_archive/`. Never move notes by hand (use `brain move`, it keeps links).
- Never put passwords, API keys, tokens or other people's private data (ID numbers, card numbers) in a note.
