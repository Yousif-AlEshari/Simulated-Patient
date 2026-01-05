"""src.utils.env

Environment loading + lightweight validation.

Keep this tiny and dependency-light; the rest of the app can simply call:

    from src.utils.env import load_env
    load_env()

"""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv


def load_env(*, override: bool = False) -> None:
    """Load environment variables from a `.env` file if present."""
    load_dotenv(override=override)


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return v
