---
name: session-handoff
description: >-
  End a Claude Code session cleanly. Two modes: CLOSE (nothing carries over: finish open items, run the learning loop,
  audit that everything landed in the second brain) and MOVE (continue in a new session: write a handoff note in the
  project folder with a one-line paste block, then the learning loop). Also RESUME from such a note when a message
  starts with "Read …handoff.md". Use when the context is filling up or the owner wants to stop or continue
  elsewhere. Triggers: "סיום סשן", "תסגור את הסשן", "נמשיך בשיחה חדשה", "נמשיך בסשן חדש", "תכין פרומפט להמשך",
  "close the session", "continue in a new session", "write the handoff", "resume from".
---

# Session handoff (close, move, resume)

Tool: `B=~/.second-brain/bin/brain`. Template: `<vault>/_library/templates/handoff.md`.

## 0. Pick the mode
| The owner says | Mode |
|---|---|
| "סיום סשן", "תסגור", "close the session" (no next session mentioned) | **Close** |
| "נמשיך בשיחה חדשה", "continue in a new session", or the context is nearly full | **Move** |

## Close
1. Finish every open item you can reach now. Only items that need the owner's yes or an outside party stay open;
   ask for that yes in the reply, one short question.
2. Learning loop: run skill `calibrate` on the whole session.
3. Documentation audit: walk the conversation; every decision, deliverable and status change must be in the vault
   (project README "Now"/"Decisions", notes saved via `vault-save`). Fix gaps. `$B lint` clean.
4. Reply: what was finished, what the audit fixed, the top 3 lessons, the open yes-questions. No handoff file.

## Move
1. Close the loop first: save deliverables (`vault-save`), update the README "Now".
2. Write `Projects/<Name>/YYYY-MM-DD-<topic>-handoff.md` (`type: handoff`, `status: ready-to-run`). If it replaces an
   older handoff, its first line says so with a link, and the old one gets `status: superseded`.
   Sections, in this order, in the owner's language:
   - **Paste in the new session**: ONE quoted line in the owner's language, starting with the path, e.g.
     `> קרא את Projects/Bakery-Website/2026-05-02-menu-handoff.md במוח השני והמשך את עמוד התפריט.`
   - **Read first**: the notes and memory files the next session needs, in order.
   - **What the owner needs to do**: per item, a direct link to the exact screen + at most 3 short lines.
   - **Claude's order of work**: numbered steps, each with how to know it is done.
   - **Exact state** (date and time): what is built, where, what is live, what is waiting on whom.
   - **Traps**: what went wrong this session and the fix, one line each.
   - **Do not**: actions that need the owner's explicit yes.
3. `$B docs <Name> --apply`, `$B moc --apply`, `$B lint --files <file>`.
4. Learning loop: skill `calibrate`.
5. Reply: top 3 lessons, the paste line in a code block, and the 1-3 things the owner must do first.

## Resume ("קרא את …handoff.md" / "Read …handoff.md")
1. `$B where`; read the handoff fully, then the notes it names, then the project README.
2. Re-check the "Exact state" against reality (files, links, anything live) before acting; note drift in the README.
3. Reply in the owner's language: what changed since the handoff, then start step 1 of Claude's order of work.
