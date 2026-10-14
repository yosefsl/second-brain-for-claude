#!/usr/bin/env python3
"""brain: housekeeping for an Obsidian second brain used by Claude Code.

Stdlib only (Python 3.9+). The vault path comes from $SB_VAULT or
~/.second-brain/config.json ({"vault": "...", "rtl": true}).

    brain where                         print the vault path
    brain doctor                        check vault, Obsidian, skills, hook
    brain lint [--recent MIN | --all | --files F...] [--hook] [--strict]
    brain audit                         broken / ambiguous links, orphans, missing `up`
    brain new-project NAME [--title T] [--summary S]
    brain docs PROJECT [--apply]        rebuild the README documents table
    brain moc [--apply]                 rebuild the auto block in Projects/Projects-MOC.md
    brain move SRC DST [--apply]        move a file/folder and rewrite every wikilink to it
    brain recent [--days N]             notes changed lately (for session start)

Every write command is a dry run unless --apply is given (new-project writes directly).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import sys
import time
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
CONFIG_FILE = Path(os.environ.get("SB_HOME", HOME / ".second-brain")) / "config.json"
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}
ALLOWED_TOP = {"Projects", "_library", "_archive", "_attachments", "CLAUDE.md", "AGENTS.md", "Home.md"}
TYPES = ["project", "note", "research", "plan", "meeting", "decision", "handoff", "prompt",
         "learning", "reference", "asset"]
DATED_TYPES = {"research", "plan", "meeting", "handoff", "prompt", "learning"}
DATE_PREFIX_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")
FM_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", re.DOTALL)
WIKILINK_RE = re.compile(r"(!?)\[\[([^\]\[|#]*)(#[^\]\[|]*)?(\|[^\]\[]*)?\]\]")
DOCS_START, DOCS_END = "<!-- docs:auto:start -->", "<!-- docs:auto:end -->"
MOC_START, MOC_END = "<!-- moc:auto:start -->", "<!-- moc:auto:end -->"


# ---------- config ----------

def load_config() -> dict:
    cfg = {}
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            cfg = {}
    if os.environ.get("SB_VAULT"):
        cfg["vault"] = os.environ["SB_VAULT"]
    return cfg


CFG = load_config()
VAULT = Path(os.path.expanduser(CFG.get("vault", str(HOME / "SecondBrain")))).resolve()
RTL = bool(CFG.get("rtl", False))


def rel(p: Path) -> str:
    return p.resolve().relative_to(VAULT).as_posix()


def iter_files(root: Path | None = None, suffix: str | None = ".md"):
    for dirpath, dirnames, filenames in os.walk(root or VAULT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for f in sorted(filenames):
            if suffix is None or f.endswith(suffix):
                yield Path(dirpath) / f


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def today() -> str:
    return dt.date.today().isoformat()


def slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return s or "misc"


# ---------- frontmatter (minimal YAML: scalars, inline and block lists) ----------

def split_fm(text: str):
    m = FM_RE.match(text)
    return (m.group(1), text[m.end():]) if m else (None, text)


def _unquote(s: str) -> str:
    s = s.strip()
    return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'" else s


def _split_list(inner: str):
    parts, cur, depth, q = [], "", 0, None
    for ch in inner:
        if q:
            cur += ch
            q = None if ch == q else q
        elif ch in "\"'":
            q = ch
            cur += ch
        elif ch == "[":
            depth += 1
            cur += ch
        elif ch == "]":
            depth -= 1
            cur += ch
        elif ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        parts.append(cur)
    return [_unquote(x) for x in parts]


def parse_fm(fm: str | None) -> dict:
    out: dict = {}
    if not fm:
        return out
    lines = fm.split("\n")
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z0-9_\-]+):\s*(.*)$", lines[i])
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val in ("", "|", ">"):
            items, j = [], i + 1
            while j < len(lines) and (lines[j][:1] in (" ", "\t") or not lines[j].strip()):
                s = lines[j].strip()
                if s.startswith("- "):
                    items.append(_unquote(s[2:]))
                j += 1
            out[key] = items
            i = j
            continue
        if val.startswith("[") and val.endswith("]"):
            out[key] = _split_list(val[1:-1]) if val[1:-1].strip() else []
        else:
            out[key] = _unquote(val)
        i += 1
    return out


# ---------- link index ----------

class Index:
    def __init__(self):
        self.by_path: dict[str, Path] = {}
        self.by_name: dict[str, list[str]] = defaultdict(list)
        for p in iter_files(suffix=None):
            r = rel(p)
            key = r[:-3] if r.endswith(".md") else r
            self.by_path[key.lower()] = p
            self.by_name[(p.stem if r.endswith(".md") else p.name).lower()].append(key)

    def key(self, low: str) -> str:
        r = rel(self.by_path[low])
        return r[:-3] if r.endswith(".md") else r

    def resolve(self, target: str, src: Path | None = None):
        """('ok', key) | ('ambiguous', [keys]) | ('broken', None), Obsidian-like."""
        t = target.strip().replace("\\", "/")
        t = t[2:] if t.startswith("./") else t
        if not t:
            return "ok", None
        cand = t[:-3] if t.lower().endswith(".md") else t
        low = cand.lower()
        if low in self.by_path:
            return "ok", self.key(low)
        if src is not None and src.parent.resolve() != VAULT:
            joined = os.path.normpath(rel(src.parent) + "/" + cand).replace("\\", "/").lower()
            if joined in self.by_path:
                return "ok", self.key(joined)
        hits = self.by_name.get(cand.rsplit("/", 1)[-1].lower(), [])
        if len(hits) == 1:
            return "ok", hits[0]
        if hits:
            suf = [h for h in hits if h.lower().endswith("/" + low)]
            return ("ok", suf[0]) if len(suf) == 1 else ("ambiguous", hits)
        return "broken", None


CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.DOTALL)


def links_in(text: str):
    """Wikilinks outside code blocks and inline code (examples in rules are not links)."""
    for m in WIKILINK_RE.finditer(CODE_RE.sub("", text)):
        yield m


# ---------- lint ----------

def lint_files(files, idx: Index | None, new_files: set):
    warns = []
    seen_top = set()
    for p in files:
        p = p.resolve()
        if not p.exists() or VAULT not in p.parents:
            continue
        r = rel(p)
        parts = r.split("/")
        if ".obsidian" in parts or p.name in ("CLAUDE.md", "AGENTS.md"):
            continue
        top = parts[0]
        if top not in ALLOWED_TOP and top not in seen_top:
            seen_top.add(top)
            warns.append(f"{r}: top-level `{top}` is not in the vault map (use Projects/<Name>/ instead)")
        if top == "_archive":
            if p in new_files and r != "_archive/README.md":
                warns.append(f"{r}: new file inside _archive/ (archive is read-only)")
            continue
        if top in ("_library", "_attachments"):
            continue
        fm_text, _ = split_fm(read(p))
        if fm_text is None:
            warns.append(f"{r}: no frontmatter")
            continue
        if p.name == "Projects-MOC.md":
            continue
        fm = parse_fm(fm_text)
        t = str(fm.get("type", ""))
        if not t:
            warns.append(f"{r}: missing `type`")
        elif t not in TYPES:
            warns.append(f"{r}: type `{t}` not in {TYPES}")
        up = fm.get("up")
        if not up:
            warns.append(f"{r}: missing `up` (the note is lost without a parent link)")
        elif idx is not None:
            m = re.search(r"\[\[([^\]|#]+)", str(up))
            if m and idx.resolve(m.group(1), p)[0] != "ok":
                warns.append(f"{r}: `up` does not resolve: {m.group(1)}")
        tags = fm.get("tags")
        if not isinstance(tags, list) or len(tags) != 2:
            warns.append(f"{r}: tags must be exactly [<project-slug>, <type>] (got {tags})")
        elif len(parts) > 2 and top == "Projects" and str(tags[0]) != slugify(parts[1]):
            warns.append(f"{r}: first tag `{tags[0]}` should be `{slugify(parts[1])}`")
        if p in new_files and t in DATED_TYPES and not DATE_PREFIX_RE.match(p.name):
            warns.append(f"{r}: `{t}` is a dated deliverable; name it YYYY-MM-DD-<slug>.md")
    return warns


def cmd_lint(a):
    if a.hook:
        try:
            if json.load(sys.stdin).get("stop_hook_active"):
                return 0
        except Exception:
            pass
    if not VAULT.exists():
        return 0 if a.hook else _die(f"vault not found: {VAULT}")
    if a.files:
        files = [Path(f).resolve() for f in a.files]
    elif a.all:
        files = list(iter_files())
    else:
        cutoff = time.time() - a.recent * 60
        files = [p for p in iter_files() if p.stat().st_mtime >= cutoff]
    if not files:
        if not a.hook:
            print("brain lint: nothing to check")
        return 0
    new_cut = time.time() - max(a.recent, 60) * 60
    new_files = {p.resolve() for p in files if _birth(p) >= new_cut}
    warns = lint_files(files, Index(), new_files)
    if warns:
        print(f"brain lint: {len(warns)} warning(s) in the second brain")
        for w in warns[:40]:
            print(" -", w)
        if len(warns) > 40:
            print(f" ... {len(warns) - 40} more")
        if a.hook:
            print("Fix these before ending the turn if you wrote these notes (skill: second-brain).")
    elif not a.hook:
        print("brain lint: clean")
    return 1 if a.strict and warns else 0


def _birth(p: Path) -> float:
    st = p.stat()
    return getattr(st, "st_birthtime", st.st_ctime)


# ---------- audit ----------

def cmd_audit(a):
    idx = Index()
    inbound: dict[str, int] = defaultdict(int)
    broken, ambiguous, no_up = [], [], []
    for p in iter_files():
        r = rel(p)
        if r.startswith("_archive/"):
            continue
        text = read(p)
        for m in links_in(text):
            target = m.group(2)
            if not target.strip():
                continue
            st, val = idx.resolve(target, p)
            if st == "ok" and val:
                inbound[val] += 1
            elif st == "broken":
                broken.append(f"{r} -> [[{target}]]")
            else:
                ambiguous.append(f"{r} -> [[{target}]] ({len(val)} matches)")
        fm = parse_fm(split_fm(text)[0])
        if r.startswith("Projects/") and r != "Projects/Projects-MOC.md" and not fm.get("up"):
            no_up.append(r)
    orphans = []
    for p in iter_files():
        r = rel(p)
        key = r[:-3]
        if r.startswith(("_archive/", "_library/")) or "/" not in r:
            continue
        if inbound.get(key, 0) == 0 and r != "Projects/Projects-MOC.md":
            orphans.append(r)
    report = {"vault": str(VAULT), "broken": broken, "ambiguous": ambiguous,
              "missing_up": no_up, "orphans_no_inbound_links": orphans}
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        for k, v in report.items():
            if k == "vault":
                print(f"vault: {v}")
                continue
            print(f"\n{k}: {len(v)}")
            for x in v[:50]:
                print("  -", x)
    return 0


# ---------- projects, README docs table, MOC ----------

def project_dir(name: str) -> Path:
    d = VAULT / "Projects" / name
    if not d.is_dir():
        hits = [x for x in (VAULT / "Projects").iterdir() if x.is_dir() and x.name.lower() == name.lower()]
        if not hits:
            _die(f"no project folder Projects/{name}")
        d = hits[0]
    return d


def cmd_new_project(a):
    name = re.sub(r"[^\w\-]+", "-", a.name.strip(), flags=re.UNICODE).strip("-")
    d = VAULT / "Projects" / name
    if (d / "README.md").exists():
        print(f"exists: {rel(d / 'README.md')}")
        return 0
    (d / "intake").mkdir(parents=True, exist_ok=True)
    title = a.title or a.name
    css = "\ncssclasses: [rtl]" if RTL else ""
    (d / "README.md").write_text(
        f"""---
title: "{title}"
type: project
status: active
date: {today()}
updated: {today()}
tags: [{slugify(name)}, project]
up: "[[Projects/Projects-MOC]]"
related: []{css}
---

# {title}

{a.summary or "_One or two lines: what this project is and who it is for._"}

## Now
-

## Decisions
-

## Documents
{DOCS_START}
{DOCS_END}
""", encoding="utf-8")
    print(f"created: {rel(d / 'README.md')}")
    _write_moc(apply=True, quiet=True)
    return 0


def _docs_rows(d: Path) -> list[str]:
    rows = []
    for p in sorted(d.rglob("*.md"), reverse=True):
        if p.name == "README.md" and p.parent == d:
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        fm = parse_fm(split_fm(read(p))[0])
        key = rel(p)[:-3]
        title = str(fm.get("title") or p.stem).replace("|", "/")
        rows.append(f"| {fm.get('date', '')} | [[{key}\\|{title}]] | {fm.get('type', '')} |")
    rows.sort(reverse=True)
    return ["| date | document | type |", "|---|---|---|"] + rows


def cmd_docs(a):
    d = project_dir(a.project)
    readme = d / "README.md"
    text = read(readme)
    block = "\n".join([DOCS_START] + _docs_rows(d) + [DOCS_END])
    if DOCS_START in text and DOCS_END in text:
        new = re.sub(re.escape(DOCS_START) + r".*?" + re.escape(DOCS_END), lambda _: block, text, flags=re.DOTALL)
    else:
        new = text.rstrip() + "\n\n## Documents\n" + block + "\n"
    new = re.sub(r"^updated: .*$", f"updated: {today()}", new, count=1, flags=re.MULTILINE)
    if a.apply:
        readme.write_text(new, encoding="utf-8")
        print(f"updated: {rel(readme)}")
    else:
        print(block)
    return 0


def _write_moc(apply: bool, quiet: bool = False):
    moc = VAULT / "Projects" / "Projects-MOC.md"
    lines = ["### Active"]
    archived = []
    for d in sorted((VAULT / "Projects").iterdir()):
        r = d / "README.md"
        if not d.is_dir() or not r.exists():
            continue
        fm = parse_fm(split_fm(read(r))[0])
        line = f"- [[Projects/{d.name}/README|{fm.get('title') or d.name}]] · {fm.get('status', 'active')} · {fm.get('updated') or fm.get('date', '')}"
        (archived if str(fm.get("status", "")).lower() in ("done", "archived", "paused") else lines).append(line)
    arch_root = VAULT / "_archive" / "Projects"
    if arch_root.exists():
        for d in sorted(arch_root.iterdir()):
            if d.is_dir():
                archived.append(f"- [[_archive/Projects/{d.name}/README|{d.name}]] · archived")
    if archived:
        lines += ["", "### Paused / done / archived"] + archived
    block = "\n".join([MOC_START] + lines + [MOC_END])
    text = read(moc) if moc.exists() else "---\ntitle: Projects\ntype: reference\n---\n\n# Projects\n\n"
    if MOC_START in text:
        new = re.sub(re.escape(MOC_START) + r".*?" + re.escape(MOC_END), lambda _: block, text, flags=re.DOTALL)
    else:
        new = text.rstrip() + "\n\n" + block + "\n"
    if apply:
        moc.parent.mkdir(parents=True, exist_ok=True)
        moc.write_text(new, encoding="utf-8")
        if not quiet:
            print(f"updated: {rel(moc)}")
    else:
        print(block)


def cmd_moc(a):
    _write_moc(a.apply)
    return 0


# ---------- move with link rewrite ----------

def cmd_move(a):
    src = (VAULT / a.src).resolve() if not os.path.isabs(a.src) else Path(a.src).resolve()
    dst = (VAULT / a.dst).resolve() if not os.path.isabs(a.dst) else Path(a.dst).resolve()
    if not src.exists():
        _die(f"not found: {src}")
    if dst.exists():
        _die(f"target exists: {dst}")
    if VAULT not in dst.parents:
        _die("target must be inside the vault")
    idx = Index()

    def key_of(p: Path) -> str:
        r = rel(p)
        return r[:-3] if r.endswith(".md") else r

    def strip_md(s: str) -> str:
        return s[:-3] if s.endswith(".md") else s

    dst_rel = dst.relative_to(VAULT).as_posix()
    if src.is_dir():
        moved = {key_of(p): strip_md(dst_rel + "/" + p.relative_to(src).as_posix())
                 for p in iter_files(src, suffix=None)}
    else:
        moved = {key_of(src): strip_md(dst_rel)}
    edits = []
    for p in iter_files():
        text = read(p)

        def sub(m):
            st, key = idx.resolve(m.group(2), p)
            if st != "ok" or key not in moved:
                return m.group(0)
            return f"{m.group(1)}[[{moved[key]}{m.group(3) or ''}{m.group(4) or ''}]]"

        new = WIKILINK_RE.sub(sub, text)
        if new != text:
            edits.append((p, new))
    print(f"move {rel(src)} -> {rel(dst)}: {len(moved)} file(s), links rewritten in {len(edits)} note(s)")
    for p, _ in edits[:30]:
        print("  ~", rel(p))
    if not a.apply:
        print("dry run; add --apply")
        return 0
    for p, new in edits:
        p.write_text(new, encoding="utf-8")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    print("applied")
    return 0


# ---------- recent, where, doctor ----------

def cmd_recent(a):
    cutoff = time.time() - a.days * 86400
    rows = sorted(((p.stat().st_mtime, rel(p)) for p in iter_files()
                   if p.stat().st_mtime >= cutoff and not rel(p).startswith("_archive/")), reverse=True)
    for t, r in rows[:a.limit]:
        print(dt.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M"), r)
    return 0


def cmd_where(a):
    print(VAULT)
    return 0


def cmd_doctor(a):
    checks = []

    def ok(name, cond, hint=""):
        checks.append((name, bool(cond), hint))

    ok("vault folder", VAULT.is_dir(), str(VAULT))
    ok("vault rules (CLAUDE.md)", (VAULT / "CLAUDE.md").exists())
    ok("projects hub", (VAULT / "Projects" / "Projects-MOC.md").exists())
    apps = [Path("/Applications/Obsidian.app"), HOME / "Applications" / "Obsidian.app",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Obsidian" / "Obsidian.exe"]
    ok("Obsidian app", any(p.exists() for p in apps))
    reg = [HOME / "Library/Application Support/obsidian/obsidian.json",
           Path(os.environ.get("APPDATA", "")) / "obsidian" / "obsidian.json"]
    registered = False
    for r in reg:
        if r.is_file():
            try:
                vs = json.loads(r.read_text()).get("vaults", {})
                registered = any(Path(v.get("path", "")).resolve() == VAULT for v in vs.values())
            except Exception:
                pass
    ok("vault registered in Obsidian", registered)
    skills = HOME / ".claude" / "skills"
    for s in ("second-brain", "vault-save", "session-handoff", "calibrate", "vault-tidy"):
        ok(f"skill {s}", (skills / s / "SKILL.md").exists())
    gl = HOME / ".claude" / "CLAUDE.md"
    ok("global CLAUDE.md block", gl.exists() and "second-brain:start" in read(gl))
    st = HOME / ".claude" / "settings.json"
    ok("Stop hook (brain lint)", st.exists() and "brain" in read(st) and "--hook" in read(st))
    bad = [c for c in checks if not c[1]]
    for name, good, hint in checks:
        print(f"{'OK  ' if good else 'FAIL'} {name}{('  ' + hint) if hint else ''}")
    print("DOCTOR_OK" if not bad else f"DOCTOR_FAIL {len(bad)}")
    return 0 if not bad else 1


def _die(msg: str):
    print(f"brain: {msg}", file=sys.stderr)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(prog="brain", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("where").set_defaults(f=cmd_where)
    sp.add_parser("doctor").set_defaults(f=cmd_doctor)
    p = sp.add_parser("lint")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true")
    g.add_argument("--files", nargs="+")
    p.add_argument("--recent", type=int, default=180, help="minutes (default 180)")
    p.add_argument("--hook", action="store_true")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(f=cmd_lint)
    p = sp.add_parser("audit")
    p.add_argument("--json", action="store_true")
    p.set_defaults(f=cmd_audit)
    p = sp.add_parser("new-project")
    p.add_argument("name")
    p.add_argument("--title")
    p.add_argument("--summary")
    p.set_defaults(f=cmd_new_project)
    p = sp.add_parser("docs")
    p.add_argument("project")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(f=cmd_docs)
    p = sp.add_parser("moc")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(f=cmd_moc)
    p = sp.add_parser("move")
    p.add_argument("src")
    p.add_argument("dst")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(f=cmd_move)
    p = sp.add_parser("recent")
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(f=cmd_recent)
    a = ap.parse_args()
    try:
        return a.f(a) or 0
    except SystemExit:
        raise
    except Exception as e:
        print(f"brain {a.cmd}: error {e}", file=sys.stderr)
        return 0 if getattr(a, "hook", False) else 2


if __name__ == "__main__":
    sys.exit(main())
