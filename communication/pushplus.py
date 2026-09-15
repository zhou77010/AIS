"""AIS PushPlus notification.

Sends one message to the personal WeChat of the account that owns the PushPlus
token. It is the simplest synchronous implementation: one POST to the PushPlus
send endpoint. No domain, no IP whitelist and no group is required.
"""

from __future__ import annotations

import json
import urllib.request

from config.logging_config import get_logger
from utils.constants import EnvVar
from utils.exceptions import AISException

_SEND_URL = "https://www.pushplus.plus/send/"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "pushplus"
_CONTENT_TYPE = "application/json"
_SUCCESS_CODES = (0, 200)


class PushPlusNotifier:
    """Sends a message through a PushPlus token."""

    def __init__(
        self,
        token: str | None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create the notifier for one PushPlus token.

        Args:
            token: PushPlus user token, or None when not configured.
            timeout_seconds: Timeout of a single send request.
        """
        self._token = token
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger(_LOGGER_NAME)

    def send(self, title: str, content: str) -> None:
        """Send one message.

        When no token is configured the message is not sent and a clear warning
        is logged instead. When PushPlus answers with an unexpected code the
        code and message are logged and raised, so a rejected request can never
        look like a delivered one.

        Args:
            title: Title of the message.
            content: Body of the message.

        Raises:
            AISException: When PushPlus rejects the request.
            urllib.error.URLError: When PushPlus cannot be reached.
        """
        if self._token is None:
            self._logger.warning(
                "no PushPlus token configured (%s); message not sent",
                EnvVar.PUSHPLUS_TOKEN.value,
            )
            return

        payload = json.dumps({"token": self._token, "title": title, "content": content})
        request = urllib.request.Request(
            _SEND_URL,
            data=payload.encode("utf-8"),
            headers={"Content-Type": _CONTENT_TYPE},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as reply:
            answer = json.loads(reply.read().decode("utf-8"))

        code = int(answer.get("code", -1))
        if code not in _SUCCESS_CODES:
            message = (
                f"PushPlus rejected the request: code={code} "
                f"msg={answer.get('msg')!r}"
            )
            self._logger.error("%s", message)
            raise AISException(message)
        self._logger.info("message sent through PushPlus")
