#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Iterator

IGNORED_DIRECTORY_NAMES = frozenset({
    ".git",
    "node_modules",
    "playwright-report",
    "test-results",
})


def is_ignored(path: Path) -> bool:
    """Return True for repository-local tool output that is never site source."""
    return any(part in IGNORED_DIRECTORY_NAMES for part in path.parts)


def iter_files(root: Path, pattern: str) -> Iterator[Path]:
    """Yield source-controlled candidates while excluding local tool artifacts."""
    for path in root.rglob(pattern):
        if path.is_file() and not is_ignored(path.relative_to(root)):
            yield path
