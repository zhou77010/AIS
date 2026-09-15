"""AIS Bark notification.

Sends one push notification to an iPhone through Bark. It is the simplest
synchronous implementation: one POST to the device key URL taken from the Bark
app. No domain, no IP whitelist, no group and no real-name check is required.
"""

from __future__ import annotations

import json
import urllib.request
from urllib.parse import quote, urlsplit

from config.logging_config import get_logger
from utils.constants import EnvVar
from utils.exceptions import AISException

_BASE_URL = "https://api.day.app"
_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "bark"
_CONTENT_TYPE = "application/json"
_SUCCESS_CODE = 200


def build_push_url(target: str) -> str:
    """Return the Bark push URL for a configured target.

    Only the device key is kept. The Bark app shows a sample URL whose path may
    carry sample text (often Chinese), and a URL must stay ASCII to be sent, so
    that text is dropped. A bare key is accepted as well.

    Args:
        target: Full Bark URL, or bare device key.

    Returns:
        The push URL built from the device key.
    """
    value = target.strip()
    if not value.startswith(("http://", "https://")):
        return f"{_BASE_URL}/{quote(value.split('/')[0])}"

    parts = urlsplit(value)
    key = parts.path.strip("/").split("/")[0]
    return f"{parts.scheme}://{parts.netloc}/{quote(key)}"


class BarkNotifier:
    """Sends a push notification through Bark."""

    def __init__(
        self,
        target: str | None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create the notifier for one Bark device.

        Args:
            target: Full Bark URL or bare device key, or None when not
                configured.
            timeout_seconds: Timeout of a single send request.
        """
        self._target = target
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger(_LOGGER_NAME)

    def send(self, title: str, content: str) -> None:
        """Send one notification.

        When no Bark target is configured the message is not sent and a clear
        warning is logged instead. When Bark answers with a non-success code the
        code and message are logged and raised, so a rejected push can never
        look like a delivered one.

        Args:
            title: Title of the notification.
            content: Body of the notification.

        Raises:
            AISException: When Bark rejects the request.
            urllib.error.URLError: When Bark cannot be reached.
        """
        if self._target is None:
            self._logger.warning(
                "no Bark URL configured (%s); message not sent",
                EnvVar.BARK_URL.value,
            )
            return

        payload = json.dumps({"title": title, "body": content})
        request = urllib.request.Request(
            build_push_url(self._target),
            data=payload.encode("utf-8"),
            headers={"Content-Type": _CONTENT_TYPE},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as reply:
            answer = json.loads(reply.read().decode("utf-8"))

        code = int(answer.get("code", -1))
        if code != _SUCCESS_CODE:
            message = (
                f"Bark rejected the request: code={code} "
                f"message={answer.get('message')!r}"
            )
            self._logger.error("%s", message)
            raise AISException(message)
        self._logger.info("message sent through Bark")
