---
name: calibrate
description: >-
  The learning loop: scan this conversation for your failures, misreads and the owner's corrections or new
  preferences, decide where each lesson belongs (your memory folder first, a skill, the vault rules, or nowhere), show
  a short numbered list of proposed changes, and apply only what the owner approves. Runs on demand and at the end of
  every session (skill `session-handoff`). Triggers: "כיול", "תעשה כיול", "מה למדת", "לולאת למידה", "תזכור את זה
  לפעם הבאה", "calibrate", "what did you learn", "remember this for next time".
---

# Calibrate (learning loop)

Your memory folder is the auto-memory directory named in your system prompt (section "Memory"): one file per
lesson + the index `MEMORY.md`, loaded into every session. That is where lessons about *how to work with the owner*
live. Facts about projects belong in the vault, not here (skill `second-brain` §4).

## Procedure
1. **Scan** the conversation since the last calibrate or handoff. Three lists, each item with a quote or a pointer:
   - failures: the owner found it before you, rework, a wrong instruction, a memory rule you broke;
   - misreads: "why?", the same ask twice, a plan the owner pushed back on;
   - refinements: a new preference or a sharper rule ("from now on…", "always…", "don't…").
   Nothing found is a valid result: say so in one line, no filler lessons.
2. **Place each lesson**, cheapest durable home first:
   - an existing memory file on the same topic (read `MEMORY.md`, grep the folder): update it;
   - a new memory file + one line in `MEMORY.md` (`- [Title](file.md) — hook`, one line);
   - a skill's `SKILL.md` (`~/.claude/skills/<name>/`) at the exact step where the mistake happened;
   - the vault rules (`<vault>/CLAUDE.md`) only for a rule about where things go in the vault;
   - nowhere: one-off context or already covered. Say which and why.
3. **Memory file shape**:
   ```markdown
   ---
   name: <short-kebab-slug>
   description: <one line, used to decide relevance later>
   metadata:
     type: user | feedback | project | reference
   ---
   <the rule in one or two sentences>
   **Why:** <what happened, with the date>
   **How to apply:** <when it kicks in and what to do>
   ```
   Prefer one sharp sentence with its reason over a wall of MUST/NEVER. Merge with an existing rule rather than
   stacking a near-duplicate. Convert relative dates ("yesterday") to absolute dates.
4. **Show the list** in the owner's language, numbered: `N. <file>` · before · after · why (one line each).
   Close with one short question: "לאשר את כולם, או רק חלק (מספרים)?" / "Approve all, or only some (numbers)?".
5. **Apply only the approved items**, in the same turn. Leave skipped items alone.
6. **Report**: files changed, top 3 lessons. When the session belongs to a project, save the list as
   `Projects/<Name>/YYYY-MM-DD-learning-loop-<topic>.md` (`type: learning`, template
   `_library/templates/learning-loop.md`) via skill `vault-save`.

## Keep it small
`MEMORY.md` stays under ~150 lines: when it grows, merge related lines and delete rules that turned out wrong.
