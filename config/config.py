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
DEFAULT_TICKERS: tuple[str, ...] = ("AAPL",)
DEFAULT_ANALYSIS_INTERVAL_MINUTES = 30
# The curated catalyst calendar lives in the repository, because it holds events
# no connected source reports and a person maintains it.
DEFAULT_CALENDAR_RELATIVE_PATH = Path("data") / "calendar" / "events.json"
# The watchlist holds AIS's own statement about what to watch, so it lives with the
# configuration rather than with the data collected from the world.
DEFAULT_WATCHLIST_RELATIVE_PATH = Path("config") / "watchlist.json"


@dataclass(frozen=True)
class Config:
    """Validated runtime configuration for AIS."""

    environment: Environment
    log_level: LogLevel
    log_dir: Path
    log_file_name: str
    tickers: tuple[str, ...] = DEFAULT_TICKERS
    bark_url: str | None = None
    wechat_webhook_url: str | None = None
    wecom_corp_id: str | None = None
    wecom_app_secret: str | None = None
    wecom_agent_id: str | None = None
    serverchan_url: str | None = None
    pushplus_token: str | None = None
    analysis_interval_minutes: int = DEFAULT_ANALYSIS_INTERVAL_MINUTES
    catalyst_calendar_file: Path = PROJECT_ROOT / DEFAULT_CALENDAR_RELATIVE_PATH
    watchlist_file: Path = PROJECT_ROOT / DEFAULT_WATCHLIST_RELATIVE_PATH

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
            tickers=_read_tickers(),
            bark_url=_read_value(EnvVar.BARK_URL),
            wechat_webhook_url=_read_value(EnvVar.WECHAT_WEBHOOK_URL),
            wecom_corp_id=_read_value(EnvVar.WECOM_CORP_ID),
            wecom_app_secret=_read_value(EnvVar.WECOM_APP_SECRET),
            wecom_agent_id=_read_value(EnvVar.WECOM_AGENT_ID),
            serverchan_url=_read_value(EnvVar.SERVERCHAN_URL),
            pushplus_token=_read_value(EnvVar.PUSHPLUS_TOKEN),
            analysis_interval_minutes=_read_analysis_interval_minutes(),
            catalyst_calendar_file=_resolve_calendar_file(),
            watchlist_file=_resolve_watchlist_file(),
        )


def _resolve_watchlist_file() -> Path:
    """Return the watchlist, resolved against the root."""
    raw = _read_value(EnvVar.WATCHLIST)
    if raw is None:
        return PROJECT_ROOT / DEFAULT_WATCHLIST_RELATIVE_PATH
    path = Path(raw).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


def _resolve_calendar_file() -> Path:
    """Return the curated catalyst calendar, resolved against the root."""
    raw = _read_value(EnvVar.CATALYST_CALENDAR)
    if raw is None:
        return PROJECT_ROOT / DEFAULT_CALENDAR_RELATIVE_PATH
    path = Path(raw).expanduser()
    return path if path.is_absolute() else PROJECT_ROOT / path


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


def _read_tickers() -> tuple[str, ...]:
    """Return the symbols to analyse, in the order they should be analysed.

    The value is a comma separated list, so that watching several assets needs
    no second setting. Symbols are upper cased and duplicates are dropped while
    the given order is kept.

    Raises:
        ConfigurationError: When the variable is set but names no symbol.
    """
    name = EnvVar.TICKER.value
    raw = _read_value(EnvVar.TICKER)
    if raw is None:
        return DEFAULT_TICKERS
    tickers = tuple(
        dict.fromkeys(part.strip().upper() for part in raw.split(",") if part.strip())
    )
    if not tickers:
        raise ConfigurationError(
            f"Invalid {name}={raw!r}: expected at least one symbol."
        )
    return tickers


def _read_analysis_interval_minutes() -> int:
    """Return the analysis interval in minutes; zero means run once."""
    name = EnvVar.ANALYSIS_INTERVAL_MINUTES.value
    raw = _read_value(EnvVar.ANALYSIS_INTERVAL_MINUTES)
    if raw is None:
        return DEFAULT_ANALYSIS_INTERVAL_MINUTES
    try:
        interval = int(raw)
    except ValueError as error:
        raise ConfigurationError(
            f"Invalid {name}={raw!r}: expected a whole number of minutes."
        ) from error
    if interval < 0:
        raise ConfigurationError(
            f"Invalid {name}={raw!r}: expected zero or more minutes."
        )
    return interval


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
