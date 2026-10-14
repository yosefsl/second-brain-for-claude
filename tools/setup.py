#!/usr/bin/env python3
"""Second-brain installer, step 'configure' (stdlib only). Called by scripts/install-*.

    setup.py install --pkg PKG --vault VAULT --python PY [--rtl 0|1]
    setup.py uninstall            (removes Claude config only; never touches the vault)

Idempotent: vault template files are copied only when missing; skills, the CLAUDE.md block,
the Stop hook and permissions are replaced in place.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import secrets
import shutil
import sys
import time
from pathlib import Path

HOME = Path.home()
SB_HOME = Path(os.environ.get("SB_HOME", HOME / ".second-brain"))
CLAUDE = HOME / ".claude"
SKILLS = ["second-brain", "vault-save", "session-handoff", "calibrate", "vault-tidy"]
BLOCK_RE = re.compile(r"<!-- second-brain:start.*?<!-- second-brain:end -->\n?", re.DOTALL)
IS_WIN = platform.system() == "Windows"


def say(msg: str):
    print(f"   {msg}")


def brain_cmd() -> str:
    return str(SB_HOME / "bin" / ("brain.cmd" if IS_WIN else "brain"))


def copy_vault(pkg: Path, vault: Path, rtl: bool):
    src = pkg / "vault-template"
    today = dt.date.today().isoformat()
    rtl_line = "\ncssclasses: [rtl]" if rtl else ""
    made = 0
    for p in sorted(src.rglob("*")):
        if p.is_dir():
            continue
        r = p.relative_to(src)
        dst = vault / r
        if dst.exists():
            continue
        if r.parts[0] == ".obsidian" and r.name == "appearance.json" and not rtl:
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        text = p.read_text(encoding="utf-8")
        text = text.replace("{{DATE}}", today).replace("{{RTL_LINE}}", rtl_line)
        dst.write_text(text, encoding="utf-8")
        made += 1
    (vault / "_attachments").mkdir(parents=True, exist_ok=True)
    say(f"vault: {vault} ({made} new file(s), existing notes untouched)")


def write_config(vault: Path, rtl: bool, python: str):
    SB_HOME.mkdir(parents=True, exist_ok=True)
    cfg_path = SB_HOME / "config.json"
    cfg = {}
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text())
        except Exception:
            cfg = {}
    cfg.update({"vault": str(vault), "rtl": rtl, "python": python, "installed": dt.datetime.now().isoformat(timespec="seconds")})
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    say(f"config: {cfg_path}")


def install_tools(pkg: Path, python: str):
    (SB_HOME / "bin").mkdir(parents=True, exist_ok=True)
    shutil.copy2(pkg / "tools" / "brain.py", SB_HOME / "bin" / "brain.py")
    if IS_WIN:
        (SB_HOME / "bin" / "brain.cmd").write_text(f'@"{python}" "%~dp0brain.py" %*\r\n', encoding="utf-8")
    else:
        w = SB_HOME / "bin" / "brain"
        w.write_text(f'#!/bin/sh\nexec "{python}" "$(dirname "$0")/brain.py" "$@"\n', encoding="utf-8")
        w.chmod(0o755)
    say(f"tool: {brain_cmd()}")


def register_obsidian(vault: Path):
    if IS_WIN:
        base = Path(os.environ.get("APPDATA", HOME / "AppData/Roaming")) / "obsidian"
    elif platform.system() == "Darwin":
        base = HOME / "Library" / "Application Support" / "obsidian"
    else:
        base = HOME / ".config" / "obsidian"
    base.mkdir(parents=True, exist_ok=True)
    f = base / "obsidian.json"
    data = {}
    if f.exists():
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            shutil.copy2(f, f.with_suffix(".json.bak"))
            data = {}
    vaults = data.setdefault("vaults", {})
    for v in vaults.values():
        v.pop("open", None)
    vid = next((k for k, v in vaults.items() if Path(v.get("path", "")).resolve() == vault.resolve()), None)
    vid = vid or secrets.token_hex(8)
    vaults[vid] = {"path": str(vault), "ts": int(time.time() * 1000), "open": True}
    f.write_text(json.dumps(data), encoding="utf-8")
    say(f"Obsidian: vault registered ({f})")


def install_skills(pkg: Path):
    for s in SKILLS:
        d = CLAUDE / "skills" / s
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pkg / "skills" / s / "SKILL.md", d / "SKILL.md")
    say(f"skills: {', '.join(SKILLS)} -> {CLAUDE / 'skills'}")


def write_block(pkg: Path, vault: Path):
    block = (pkg / "claude" / "global-block.md").read_text(encoding="utf-8").replace("{{VAULT}}", str(vault))
    f = CLAUDE / "CLAUDE.md"
    text = f.read_text(encoding="utf-8") if f.exists() else ""
    text = BLOCK_RE.sub("", text).rstrip()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text((text + "\n\n" if text else "") + block, encoding="utf-8")
    say(f"instructions: {f}")


def _load_settings():
    f = CLAUDE / "settings.json"
    if f.exists():
        try:
            return f, json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            shutil.copy2(f, f.with_suffix(".json.bak"))
            say("settings.json was not valid JSON; backed up to settings.json.bak")
    return f, {}


def _ours(text: str) -> bool:
    return ".second-brain" in text or brain_cmd() in text or ("brain" in text and "lint --hook" in text)


def _strip_ours(settings: dict):
    hooks = settings.get("hooks", {})
    for ev in list(hooks):
        groups = []
        for g in hooks[ev]:
            g["hooks"] = [h for h in g.get("hooks", []) if not _ours(h.get("command", ""))]
            if g["hooks"]:
                groups.append(g)
        if groups:
            hooks[ev] = groups
        else:
            del hooks[ev]
    if not hooks:
        settings.pop("hooks", None)
    perms = settings.get("permissions", {})
    if "allow" in perms:
        perms["allow"] = [r for r in perms["allow"] if not _ours(r)]
    return settings


def write_settings(vault: Path):
    f, s = _load_settings()
    s = _strip_ours(s)
    cmd = f'"{brain_cmd()}" lint --hook'
    s.setdefault("hooks", {}).setdefault("Stop", []).append(
        {"matcher": "", "hooks": [{"type": "command", "command": cmd, "timeout": 20}]})
    perms = s.setdefault("permissions", {})
    dirs = perms.setdefault("additionalDirectories", [])
    if str(vault) not in dirs:
        dirs.append(str(vault))
    allow = perms.setdefault("allow", [])
    for rule in (f"Bash({brain_cmd()}:*)", f"Bash(~/.second-brain/bin/brain:*)"):
        if rule not in allow:
            allow.append(rule)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say(f"settings: Stop hook + vault access ({f})")


def cmd_install(a):
    pkg, vault = Path(a.pkg).resolve(), Path(os.path.expanduser(a.vault)).resolve()
    rtl = a.rtl == "1"
    vault.mkdir(parents=True, exist_ok=True)
    copy_vault(pkg, vault, rtl)
    write_config(vault, rtl, a.python)
    install_tools(pkg, a.python)
    install_skills(pkg)
    write_block(pkg, vault)
    write_settings(vault)
    register_obsidian(vault)


def cmd_uninstall(a):
    for s in SKILLS:
        shutil.rmtree(CLAUDE / "skills" / s, ignore_errors=True)
    f = CLAUDE / "CLAUDE.md"
    if f.exists():
        f.write_text(BLOCK_RE.sub("", f.read_text(encoding="utf-8")).rstrip() + "\n", encoding="utf-8")
    f, s = _load_settings()
    if s:
        s = _strip_ours(s)
        f.write_text(json.dumps(s, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    say("Claude config removed; the vault and ~/.second-brain/config.json were kept")


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("install")
    p.add_argument("--pkg", required=True)
    p.add_argument("--vault", required=True)
    p.add_argument("--python", required=True)
    p.add_argument("--rtl", default="1")
    p.set_defaults(f=cmd_install)
    sp.add_parser("uninstall").set_defaults(f=cmd_uninstall)
    a = ap.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
