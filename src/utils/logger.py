"""src.utils.logger

Minimal logger setup used across the app.

You can replace this module with your own structured logging later.
"""

from __future__ import annotations

import logging


def get_logger(name: str = "app") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Avoid duplicate handlers in Streamlit reruns.
        handler = logging.StreamHandler()
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
