"""
Structured logging configuration using loguru.
"""

import sys
from loguru import logger

# Remove default handler
logger.remove()

# Console handler — pretty format for development
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# File handler — JSON-style for production
logger.add(
    "logs/hikmah_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} — {message}",
    enqueue=True,
)

__all__ = ["logger"]
