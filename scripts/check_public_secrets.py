#!/usr/bin/env python3
"""Fail CI if a Discord webhook credential is committed to the repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCORD_WEBHOOK = re.compile(
    rb"https://(?:canary\.)?(?:discord(?:app)?\.com)/api/webhooks/\d+/[A-Za-z0-9._-]+"
)
SKIP_DIRS = {".git", ".venv", "_site", "__pycache__"}
MAX_BYTES = 2_000_000


def main() -> int:
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            data = path.read_bytes()
        except OSError:
            continue
        if DISCORD_WEBHOOK.search(data):
            findings.append(path.relative_to(ROOT).as_posix())

    if findings:
        print("Committed Discord webhook credential detected:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1

    print("Secret scan passed: no Discord webhook credential found in repository files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
