# INSTALL.md: instructions for Claude Code

You are installing **second-brain** for a user with no technical background: an Obsidian vault that becomes the
long-term memory of their projects, plus the Claude Code skills, instructions and hook that make you use it.
Goal: the user does nothing except click "Allow" on permission prompts. You do everything else.

## Ground rules for this install

- Talk to the user in their language (Hebrew if they wrote in Hebrew), short and plain. No commands, no paths, no jargon.
- Never ask the user to open a terminal, type anything, or install anything themselves.
- The only click you may ask for: "אם מופיעה בקשת אישור, ללחוץ Allow / אישור".
- Do not use `git` (a fresh Mac pops an Xcode install window). Do not use `brew` or `sudo`.
- Do not read, move or rewrite notes that already exist in an Obsidian vault of theirs. The installer only adds missing files.
- Run the install script in **one** shell call. It is idempotent: running it again upgrades in place.

## What gets installed (all inside the user's home folder, no admin password)

| Piece | Where |
|---|---|
| Obsidian (official signed app, only if missing) | `/Applications/Obsidian.app` (or `~/Applications` if not writable) |
| Private Python (only if no usable python3 exists) | `~/.second-brain/uv/`, `~/.second-brain/python/` |
| The vault (notes) | `~/SecondBrain` by default: `CLAUDE.md` (vault rules), `Projects/Projects-MOC.md` (hub), `Projects/Getting-Started/`, `_library/templates/`, `_archive/`, `_attachments/`, `.obsidian/` settings |
| Tool `brain` (lint, audit, new project, hub, safe move) | `~/.second-brain/bin/brain` |
| Skills | `~/.claude/skills/second-brain`, `vault-save`, `session-handoff`, `calibrate`, `vault-tidy` |
| Instructions block (between `second-brain:start/end` markers) | `~/.claude/CLAUDE.md` |
| Stop hook (`brain lint --hook`, advisory) + vault access + `brain` allowed | `~/.claude/settings.json` (merged; other settings kept) |
| Vault registered so Obsidian opens it directly | `~/Library/Application Support/obsidian/obsidian.json` |

Nothing leaves the computer. No account, no sync, no community plugins.

## Steps

### 1. Get the folder

If this file is already on disk (you are reading it from a local folder), use that folder as `PKG` and skip to step 2.
Otherwise download it **without git**:

```bash
mkdir -p ~/.second-brain/src && cd ~/.second-brain/src \
 && curl -fsSL "<ZIP_URL>" -o pkg.zip && rm -rf pkg && mkdir pkg && unzip -q pkg.zip -d pkg && rm pkg.zip \
 && find pkg -name INSTALL.md | head -1
```

`<ZIP_URL>` is the link in the user's prompt (normally `https://github.com/yosefsl/second-brain-for-claude/archive/refs/heads/main.zip`).
`PKG` = the folder that contains this `INSTALL.md` (printed by the last command).

### 2. Choose the vault folder (decide yourself, do not ask)

- Default `~/SecondBrain`. Keep it **out of iCloud** (iCloud sync corrupts open vaults): never inside
  `~/Library/Mobile Documents`, and avoid `~/Documents` / `~/Desktop` when "Desktop & Documents in iCloud" is on.
- If the user already has an Obsidian vault and asked to use it, set `SB_VAULT` to it: existing notes stay untouched.
- `SB_RTL=1` if the user writes Hebrew or Arabic (notes read right-to-left), else `SB_RTL=0`.

### 3. Run the installer (macOS, one call, 1-4 minutes)

```bash
SB_VAULT="$HOME/SecondBrain" SB_RTL=1 bash "$PKG/scripts/install-mac.sh"
```

Success = the last line starts with `INSTALL_OK`. If not, read the output, fix, and run again (see Troubleshooting).
Do not stop and hand the error to the user. If Obsidian was open, the script closes it first (so its vault list is not
overwritten) and reopens it on the new vault at the end; tell the user that is expected.

Windows: see "Windows" below.

### 4. Verify (yourself, read-only)

```bash
~/.second-brain/bin/brain doctor        # every line OK, last line DOCTOR_OK
~/.second-brain/bin/brain lint --all    # brain lint: clean
```

Obsidian should now show the vault with the page "איך עובדים עם המוח השני". On first launch Obsidian may show its
own welcome/"what's new" window; telling the user to close it is fine.

### 5. Finish

Tell the user, short (Hebrew example):

> הכול מותקן. Obsidian פתוח עם המוח השני שלך, ומעכשיו אני שומר בו כל דבר שאנחנו עושים בפרויקטים.
> אפשר לבקש למשל: "תפתח פרויקט חדש בשם X", "תשמור את זה במוח השני", "מה המצב בפרויקט X?".
> כדי שאני אתחיל להשתמש בו, צריך לפתוח שיחה חדשה ב-Claude פעם אחת.

Skills and the instructions block load in a **new** Claude Code session.

## Windows

Run in PowerShell, one call: `powershell -ExecutionPolicy Bypass -File "$PKG\scripts\install-windows.ps1"`.
It installs Obsidian with `winget` (or the official installer from Obsidian's GitHub releases), a private Python via
`uv` when needed, and the same vault, skills, block and hook. Success = last line `INSTALL_OK`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `curl: (6) Could not resolve host` | No internet. Ask the user to check Wi-Fi, then rerun |
| GitHub API rate limit (`403` on `api.github.com`) | Rerun in a minute, or download `https://obsidian.md/download` → the macOS `.dmg` link, then rerun with the app in `/Applications` |
| `hdiutil: attach failed` | Rerun (partial download). If it repeats: `rm -rf ~/.second-brain/src` and start from step 1 |
| `uv` / Python download fails | Rerun; the script resumes |
| `DOCTOR_FAIL` on "vault registered in Obsidian" | Obsidian was open during install and overwrote its list: `osascript -e 'quit app "Obsidian"'`, rerun the script |
| Obsidian opens an empty "Open folder as vault" screen | Same as above; or `open "obsidian://open?path=<url-encoded vault path>"` |
| User wants a different vault folder later | Rerun with `SB_VAULT=<new path>`; move notes with Finder only while Obsidian is closed, then `brain audit` |

## Uninstall

`bash ~/.second-brain/uninstall.sh` removes the skills, the instructions block, the hook and the tool.
The vault (all notes) and Obsidian stay. To remove Obsidian: drag it to the Trash.
