#!/usr/bin/env python3
"""Verhoog versienummer in version.py (standaard: patch, bijv. 1.0 -> 1.1)."""

import re
import sys
from pathlib import Path

VERSION_FILE = Path(__file__).parent / "version.py"
PARTS = ("major", "minor", "patch")


def read_version() -> tuple[int, int, int]:
    text = VERSION_FILE.read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"(\d+)\.(\d+)\.(\d+)"', text)
    if not match:
        raise SystemExit("Kon versie niet lezen uit version.py")
    return tuple(map(int, match.groups()))


def write_version(major: int, minor: int, patch: int) -> str:
    version = f"{major}.{minor}.{patch}"
    text = VERSION_FILE.read_text(encoding="utf-8")
    text = re.sub(r'__version__\s*=\s*"[^"]+"', f'__version__ = "{version}"', text)
    VERSION_FILE.write_text(text, encoding="utf-8")
    return version


def main() -> None:
    part = sys.argv[1] if len(sys.argv) > 1 else "patch"
    if part not in PARTS:
        raise SystemExit(f"Gebruik: bump_version.py [{'|'.join(PARTS)}]")

    major, minor, patch = read_version()
    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    version = write_version(major, minor, patch)
    print(f"Versie bijgewerkt naar V{version}")


if __name__ == "__main__":
    main()
