"""AIS shared constants.

This module is the single source of truth for values shared across modules.

Architecture, layers, and dependency rules are defined in
``docs/Architecture.md`` and must not be restated here.
"""

from __future__ import annotations

from enum import StrEnum

APP_NAME = "AIS"
APP_VERSION = "0.1.0"


class Environment(StrEnum):
    """Runtime environments AIS can run in."""

    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class LogLevel(StrEnum):
    """Logging levels supported by the project logging system."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class EnvVar(StrEnum):
    """Environment variables read by the configuration module."""

    ENVIRONMENT = "AIS_ENVIRONMENT"
    LOG_LEVEL = "AIS_LOG_LEVEL"
    LOG_DIR = "AIS_LOG_DIR"
    LOG_FILE_NAME = "AIS_LOG_FILE_NAME"
    TICKER = "AIS_TICKER"
    BARK_URL = "AIS_BARK_URL"
    WECHAT_WEBHOOK_URL = "AIS_WECHAT_WEBHOOK_URL"
    WECOM_CORP_ID = "AIS_WECOM_CORP_ID"
    WECOM_APP_SECRET = "AIS_WECOM_APP_SECRET"
    WECOM_AGENT_ID = "AIS_WECOM_AGENT_ID"
    SERVERCHAN_URL = "AIS_SERVERCHAN_URL"
    PUSHPLUS_TOKEN = "AIS_PUSHPLUS_TOKEN"
    ANALYSIS_INTERVAL_MINUTES = "AIS_ANALYSIS_INTERVAL_MINUTES"


class LoggerName(StrEnum):
    """Logger names used by the project logging system."""

    AIS = "ais"
    APPLICATION = "application"
