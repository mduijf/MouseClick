#!/usr/bin/env python3
"""Schrijf version.txt naar dist/ na een build."""

from pathlib import Path

from version import __version__, version_label

dist = Path(__file__).parent / "dist"
dist.mkdir(exist_ok=True)
(dist / "version.txt").write_text(f"{version_label()}\n", encoding="utf-8")
print(f"dist/version.txt -> {version_label()}")
