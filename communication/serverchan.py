"""AIS ServerChan notification.

Sends one message to the personal WeChat of the account that owns the ServerChan
send key. It is the simplest synchronous implementation: one POST to the API URL
copied from the ServerChan send key page. No domain, no IP whitelist and no group
is required.
"""

from __future__ import annotations

import json
import urllib.request

from config.logging_config import get_logger
from utils.constants import EnvVar
from utils.exceptions import AISException

_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "serverchan"
_CONTENT_TYPE = "application/json"


class ServerChanNotifier:
    """Sends a message through a ServerChan API URL."""

    def __init__(
        self,
        api_url: str | None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create the notifier for one ServerChan API URL.

        Args:
            api_url: Full ServerChan send URL, or None when not configured.
            timeout_seconds: Timeout of a single send request.
        """
        self._api_url = api_url
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger(_LOGGER_NAME)

    def send(self, title: str, content: str) -> None:
        """Send one message.

        When no API URL is configured the message is not sent and a clear
        warning is logged instead. When ServerChan answers with a non-zero code
        the code and message are logged and raised, so a rejected message can
        never look like a delivered one.

        Args:
            title: Title of the message.
            content: Body of the message, markdown is supported by the app.

        Raises:
            AISException: When ServerChan rejects the message.
            urllib.error.URLError: When ServerChan cannot be reached.
        """
        if self._api_url is None:
            self._logger.warning(
                "no ServerChan URL configured (%s); message not sent",
                EnvVar.SERVERCHAN_URL.value,
            )
            return

        payload = json.dumps({"title": title, "desp": content})
        request = urllib.request.Request(
            self._api_url,
            data=payload.encode("utf-8"),
            headers={"Content-Type": _CONTENT_TYPE},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as reply:
            answer = json.loads(reply.read().decode("utf-8"))

        code = int(answer.get("code", 0))
        if code != 0:
            message = (
                f"ServerChan rejected the message: code={code} "
                f"message={answer.get('message')!r}"
            )
            self._logger.error("%s", message)
            raise AISException(message)
        self._logger.info("message sent through ServerChan")
