"""
logging_config.py
~~~~~~~~~~~~~~~~~
Configures structured file + console logging for the trading bot.
"""

import logging
import logging.handlers
import os
from pathlib import Path


LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Set up root logger with:
      - RotatingFileHandler  → logs/trading_bot.log  (full DEBUG detail)
      - StreamHandler        → console               (INFO and above)

    Returns the 'trading_bot' logger.
    """
    LOG_DIR.mkdir(exist_ok=True)

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger("trading_bot")
    root.setLevel(logging.DEBUG)

    if root.handlers:
        return root

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(fmt)

    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return root


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'trading_bot' hierarchy."""
    return logging.getLogger(f"trading_bot.{name}")
