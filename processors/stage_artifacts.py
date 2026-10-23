"""Shared persistence/validation contract for canonical-derived stage MD pairs."""

import re
from pathlib import Path


def stage_paths(directory, stage):
    if not re.fullmatch(r"[A-Z][A-Z0-9_-]*", stage):
        raise ValueError("Use one explicit uppercase stage name")
    return tuple(
        Path(directory) / f"{stage}_{kind}.md" for kind in ("BACKTESTING", "ISSUES")
    )


def validate_stage_pairs(specifications):
    """Validate every executed stage against its fresh canonical-derived pair.

    Each specification is (directory, stage, expected_markdown_pair). Adapters
    validate counts/coverage before rendering; exact equality detects omissions,
    stale/resolved findings, missing files and nondeterministic output.
    """
    seen = set()
    for directory, stage, expected in specifications:
        if len(expected) != 2 or not all(isinstance(s, str) and s for s in expected):
            raise ValueError("Every stage requires both nonempty Markdown artifacts")
        for path, content in zip(stage_paths(directory, stage), expected):
            if path.resolve() in seen:
                raise ValueError("Stage artifact paths overlap")
            seen.add(path.resolve())
            if not path.is_file() or path.read_text(encoding="utf8") != content:
                raise ValueError(f"Missing or stale stage artifact: {path}")


def write_stage_pair(directory, stage, expected):
    if len(expected) != 2 or not all(isinstance(s, str) and s for s in expected):
        raise ValueError("Every stage requires both nonempty Markdown artifacts")
    paths = stage_paths(directory, stage)
    for path, content in zip(paths, expected):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf8", newline="\n")
    validate_stage_pairs([(directory, stage, expected)])
    return paths
