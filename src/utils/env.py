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

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_env(*, override: bool = False) -> None:
    """Load environment variables from a `.env` file if present."""
    logger.info("Loading environment variables from .env file")
    load_dotenv(override=override)
    logger.debug(f"Environment variables loaded (override={override})")


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.environ.get(name, default)
    logger.debug(f"get_env({name!r}) -> {type(value).__name__}")
    return value


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        logger.error(f"Missing required environment variable: {name}")
        raise RuntimeError(f"Missing required environment variable: {name}")
    logger.debug(f"require_env({name!r}) -> OK")
    return v
