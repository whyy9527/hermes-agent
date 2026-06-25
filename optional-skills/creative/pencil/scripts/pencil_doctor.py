#!/usr/bin/env python3
"""Preflight for the Pencil CLI (this skill's lazy runtime dependency).

Checks `node` + `pencil` presence/version and `pencil status` auth, with
actionable hints. Exit 0 iff `pencil` is installed.

    python pencil_doctor.py [--json]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess


def _probe(argv, runner):
    """Run a short command, swallowing missing-binary/timeout into None."""
    try:
        return runner(argv, text=True, capture_output=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _out(proc):
    return (proc.stdout or "").strip() if proc else None


def _major(version):
    head = (version or "").lstrip("v").split(".", 1)[0]
    return int(head) if head.isdigit() else None


def check(*, which=shutil.which, runner=subprocess.run) -> dict:
    """Structured environment status. ``which``/``runner`` are injectable."""
    node, pencil = which("node"), which("pencil")
    node_ver = _out(_probe([node, "--version"], runner)) if node else None
    pencil_ver = _out(_probe([pencil, "version"], runner)) if pencil else None
    auth = _probe([pencil, "status"], runner) if pencil else None
    return {
        "node": {
            "present": bool(node),
            "version": node_ver,
            "ok": (_major(node_ver) or 0) >= 18,
        },
        "pencil": {"present": bool(pencil), "version": pencil_ver},
        "auth": {"checked": auth is not None, "ok": bool(auth and auth.returncode == 0)},
    }


def _summary(s: dict) -> str:
    n, p, a = s["node"], s["pencil"], s["auth"]
    lines = []

    if not n["present"]:
        lines.append("✗ node: not found — install Node.js (https://nodejs.org)")
    elif not n["ok"]:
        lines.append(
            f"⚠ node: {n['version']} — Pencil needs Node 18+ "
            "(newer builds need 22+; upgrade if you hit ERR_REQUIRE_ESM)"
        )
    else:
        lines.append(f"✓ node: {n['version']}")

    if not p["present"]:
        lines.append("✗ pencil: not found — `npm install -g @pencil.dev/cli`")
    else:
        lines.append(f"✓ pencil: {p['version'] or 'installed'}")

    if p["present"]:
        if not a["checked"]:
            lines.append("⚠ auth: could not run `pencil status`")
        elif a["ok"]:
            lines.append("✓ auth: authenticated")
        else:
            lines.append(
                "✗ auth: not authenticated — `pencil login` (or set "
                "PENCIL_CLI_KEY). REQUIRED for both modes: no offline mode, "
                "so even headless `pencil interactive` refuses to start."
            )

    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check the Pencil CLI environment.")
    ap.add_argument("--json", action="store_true", help="Emit JSON")
    args = ap.parse_args(argv)

    status = check()
    print(json.dumps(status, indent=2) if args.json else _summary(status))
    return 0 if status["pencil"]["present"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
