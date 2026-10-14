# Second Brain for Claude Code (Obsidian)

An Obsidian vault that works as the long-term memory of your projects, shared by you (reading in Obsidian) and
Claude Code (reading and writing the files), plus the skills that make Claude use it every time.

**Install:** open Claude Code and paste the prompt from [PROMPT.md](PROMPT.md). Claude downloads Obsidian and sets
everything up; you only click "Allow" when asked. Details for Claude: [INSTALL.md](INSTALL.md).

## What you get
- A vault (`~/SecondBrain`) with one folder per project, a hub of all projects, templates, an archive.
- Claude reads a project's hub before working on it, and saves every deliverable there, linked, in the same turn.
- Two kinds of memory kept apart: the vault holds **facts about the work**; Claude's own memory holds
  **how to work with you** (your corrections and preferences), refined by a learning loop at the end of each session.
- Clean handoffs between sessions: one line to paste in the next conversation.
- A `brain` tool that keeps the vault tidy: lint, audit (broken links, orphans), safe moves that keep links working.

## Skills
| Skill | What it does | Say |
|---|---|---|
| `second-brain` | Read first, open projects, where things go, the two kinds of memory | "מה המצב בפרויקט X?", "פרויקט חדש" |
| `vault-save` | Save → link both ways → project table → hub → lint | "תשמור במוח השני" |
| `session-handoff` | Close a session, or move to a new one with a handoff note | "סיום סשן", "נמשיך בשיחה חדשה" |
| `calibrate` | Learning loop: lessons from the session into Claude's memory, with your OK | "כיול", "מה למדת?" |
| `vault-tidy` | Health report and safe fixes, archive finished projects | "תסדר את המוח השני" |

## Requirements
macOS 12+ (Windows: see INSTALL.md), Claude Code. No admin password, no Xcode, no Homebrew, no git.
Nothing leaves your computer; no account or sync is set up.

## Uninstall
`bash ~/.second-brain/uninstall.sh` (your notes stay).
