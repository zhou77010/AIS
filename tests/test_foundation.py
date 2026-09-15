"""Tests for the AIS foundation skeleton."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from config.config import PROJECT_ROOT, Config
from config.logging_config import configure_logging, get_logger
from utils.constants import Environment, EnvVar, LoggerName, LogLevel
from utils.exceptions import (
    AISException,
    ConfigurationError,
    DataError,
    EngineError,
    ValidationError,
)


@pytest.fixture
def ais_logger() -> Iterator[logging.Logger]:
    """Yield the AIS logger and detach every handler afterwards."""
    logger = logging.getLogger(LoggerName.AIS.value)
    yield logger
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def clear_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove every AIS environment variable from the test environment."""
    for variable in EnvVar:
        monkeypatch.delenv(variable.value, raising=False)


def test_config_uses_defaults_when_environment_is_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_environment(monkeypatch)

    config = Config.from_environment()

    assert config.environment is Environment.DEVELOPMENT
    assert config.log_level is LogLevel.INFO
    assert config.log_dir == PROJECT_ROOT / "logs"
    assert config.log_file_name == "ais.log"


def test_config_reads_environment_variables(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.ENVIRONMENT.value, "production")
    monkeypatch.setenv(EnvVar.LOG_LEVEL.value, "debug")
    monkeypatch.setenv(EnvVar.LOG_DIR.value, str(tmp_path))
    monkeypatch.setenv(EnvVar.LOG_FILE_NAME.value, "custom.log")

    config = Config.from_environment()

    assert config.environment is Environment.PRODUCTION
    assert config.log_level is LogLevel.DEBUG
    assert config.log_dir == tmp_path
    assert config.log_file_path == tmp_path / "custom.log"


def test_config_resolves_relative_log_dir_against_project_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.LOG_DIR.value, "var/logs")

    config = Config.from_environment()

    assert config.log_dir == PROJECT_ROOT / "var" / "logs"


def test_invalid_environment_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.ENVIRONMENT.value, "staging")

    with pytest.raises(ConfigurationError):
        Config.from_environment()


def test_config_defaults_to_one_ticker(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_environment(monkeypatch)

    assert Config.from_environment().tickers == ("AAPL",)


def test_config_reads_several_tickers(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.TICKER.value, " aapl, RKLB ,aapl,baba ")

    assert Config.from_environment().tickers == ("AAPL", "RKLB", "BABA")


def test_config_rejects_a_ticker_list_without_symbols(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.TICKER.value, " , ")

    with pytest.raises(ConfigurationError):
        Config.from_environment()


def test_invalid_log_level_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_environment(monkeypatch)
    monkeypatch.setenv(EnvVar.LOG_LEVEL.value, "verbose")

    with pytest.raises(ConfigurationError):
        Config.from_environment()


def test_logging_writes_to_console_and_file(
    tmp_path: Path, ais_logger: logging.Logger
) -> None:
    config = Config(
        environment=Environment.TEST,
        log_level=LogLevel.INFO,
        log_dir=tmp_path,
        log_file_name="ais.log",
    )

    configure_logging(config)
    configure_logging(config)
    get_logger(LoggerName.APPLICATION.value).info("logging works")

    handler_types = {type(handler) for handler in ais_logger.handlers}
    assert len(ais_logger.handlers) == 2
    assert logging.StreamHandler in handler_types
    assert logging.FileHandler in handler_types
    assert "logging works" in config.log_file_path.read_text(encoding="utf-8")


def test_every_ais_error_derives_from_ais_exception() -> None:
    assert issubclass(AISException, Exception)
    for error in (ConfigurationError, DataError, ValidationError, EngineError):
        assert issubclass(error, AISException)
