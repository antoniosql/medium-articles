"""Lightweight logging utilities.

This file exists mainly to show where shared operational helpers would live.
"""

from __future__ import annotations

import logging



def get_logger(name: str) -> logging.Logger:
    """Create or retrieve a logger with a simple standard format."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    return logging.getLogger(name)
