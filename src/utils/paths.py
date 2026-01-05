"""src.utils.paths

Central place for resolving important project paths.

Why:
- Avoid scattered `Path(__file__).parent/...` assumptions.
- Make repo restructuring safer.

All functions return absolute Paths.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def project_root() -> Path:
    """Return the repository root folder (the parent of `src/`)."""
    # .../src/utils/paths.py -> parents: [utils, src, <root>]
    return Path(__file__).resolve().parents[2]


def rubrics_dir() -> Path:
    return project_root() / "rubrics"


def default_rubric_path(filename: str = "psychiatry_intake.json") -> Path:
    return rubrics_dir() / filename


def resolve_rubric_path(rubric_path: Optional[str] = None) -> Path:
    """Resolve a rubric path.

    - If `rubric_path` is None/empty: returns the default rubric path.
    - If `rubric_path` is relative: resolve it relative to repo root.
    - If absolute: use it as-is.
    """
    if not rubric_path:
        return default_rubric_path()

    p = Path(rubric_path)
    if p.is_absolute():
        return p

    return project_root() / p
