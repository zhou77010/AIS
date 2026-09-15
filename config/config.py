"""AIS configuration management.

All runtime configuration is read from environment variables and validated
here. Secrets, tokens, and file paths must never be hardcoded elsewhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from utils.constants import Environment, EnvVar, LogLevel
from utils.exceptions import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_ENVIRONMENT = Environment.DEVELOPMENT
DEFAULT_LOG_LEVEL = LogLevel.INFO
DEFAULT_LOG_DIR_NAME = "logs"
DEFAULT_LOG_FILE_NAME = "ais.log"


@dataclass(frozen=True)
class Config:
    """Validated runtime configuration for AIS."""

    environment: Environment
    log_level: LogLevel
    log_dir: Path
    log_file_name: str

    @property
    def log_file_path(self) -> Path:
        """Return the full path of the log file."""
        return self.log_dir / self.log_file_name

    @classmethod
    def from_environment(cls) -> Config:
        """Build the configuration from environment variables."""
        return cls(
            environment=_read_environment(),
            log_level=_read_log_level(),
            log_dir=_resolve_log_dir(),
            log_file_name=_read_value(EnvVar.LOG_FILE_NAME) or DEFAULT_LOG_FILE_NAME,
        )


def _resolve_log_dir() -> Path:
    """Return the log directory, resolving relative values against the root."""
    raw = _read_value(EnvVar.LOG_DIR)
    if raw is None:
        return PROJECT_ROOT / DEFAULT_LOG_DIR_NAME
    log_dir = Path(raw).expanduser()
    return log_dir if log_dir.is_absolute() else PROJECT_ROOT / log_dir


def _read_environment() -> Environment:
    """Return the configured runtime environment."""
    raw = _read_value(EnvVar.ENVIRONMENT)
    if raw is None:
        return DEFAULT_ENVIRONMENT
    try:
        return Environment(raw.lower())
    except ValueError as error:
        raise ConfigurationError(
            f"Invalid {EnvVar.ENVIRONMENT.value}={raw!r}: "
            f"expected one of {_allowed_values(Environment)}."
        ) from error


def _read_log_level() -> LogLevel:
    """Return the configured log level."""
    raw = _read_value(EnvVar.LOG_LEVEL)
    if raw is None:
        return DEFAULT_LOG_LEVEL
    try:
        return LogLevel(raw.upper())
    except ValueError as error:
        raise ConfigurationError(
            f"Invalid {EnvVar.LOG_LEVEL.value}={raw!r}: "
            f"expected one of {_allowed_values(LogLevel)}."
        ) from error


def _read_value(name: EnvVar) -> str | None:
    """Return a non-empty environment value, or None when unset or blank."""
    raw = os.environ.get(name.value)
    if raw is None:
        return None
    value = raw.strip()
    return value or None


def _allowed_values(enum_type: type[Enum]) -> str:
    """Return the comma separated values of an enum, for error messages."""
    return ", ".join(str(member.value) for member in enum_type)
