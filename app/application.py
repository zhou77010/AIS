"""AIS Application.

Main application lifecycle: configuration, logging, and startup.
"""

from __future__ import annotations

from config.config import Config
from config.logging_config import configure_logging, get_logger
from utils.constants import APP_NAME, APP_VERSION, LoggerName


class Application:
    """AIS application."""

    def __init__(self) -> None:
        """Load the runtime configuration from the environment."""
        self._config = Config.from_environment()

    def run(self) -> None:
        """Start AIS."""
        configure_logging(self._config)
        logger = get_logger(LoggerName.APPLICATION.value)
        logger.info(
            "%s %s started (environment=%s, log_file=%s)",
            APP_NAME,
            APP_VERSION,
            self._config.environment.value,
            self._config.log_file_path,
        )
