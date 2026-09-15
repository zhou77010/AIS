"""AIS logging system configuration.

Configures the console and file handlers used by every AIS module.
Only the standard library ``logging`` package is used.
"""

from __future__ import annotations

import logging
from pathlib import Path

from config.config import Config
from utils.constants import LoggerName

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(config: Config) -> None:
    """Configure console and file logging for the AIS logger hierarchy.

    Calling this function again replaces the handlers installed before.
    """
    config.log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    logger = logging.getLogger(LoggerName.AIS.value)
    _remove_handlers(logger)
    logger.setLevel(config.log_level.value)
    logger.addHandler(_console_handler(formatter))
    logger.addHandler(_file_handler(formatter, config.log_file_path))
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a logger inside the AIS logger hierarchy."""
    return logging.getLogger(f"{LoggerName.AIS.value}.{name}")


def _console_handler(formatter: logging.Formatter) -> logging.Handler:
    """Return the handler that writes log records to the console."""
    handler: logging.Handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    return handler


def _file_handler(formatter: logging.Formatter, path: Path) -> logging.Handler:
    """Return the handler that writes log records to the log file."""
    handler: logging.Handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(formatter)
    return handler


def _remove_handlers(logger: logging.Logger) -> None:
    """Close and remove every handler already attached to the logger."""
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
