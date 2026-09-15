"""AIS WeChat notification.

Sends one already rendered report to a WeChat group robot webhook. It is
deliberately the simplest synchronous implementation: one POST, no retries, no
queue.

The notifier transports the message it is given and never composes one: the
Communication layer must not create or reinterpret the content it delivers, and
every channel must carry the same report.
"""

from __future__ import annotations

import json
import urllib.request

from config.logging_config import get_logger
from utils.constants import EnvVar
from utils.exceptions import AISException

_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "wechat"
_CONTENT_TYPE = "application/json"


class WeChatNotifier:
    """Sends a rendered report to a WeChat webhook."""

    def __init__(
        self,
        webhook_url: str | None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Create the notifier for one webhook.

        Args:
            webhook_url: Webhook URL of the WeChat group robot, or None when no
                webhook is configured.
            timeout_seconds: Timeout of a single send request.
        """
        self._webhook_url = webhook_url
        self._timeout_seconds = timeout_seconds
        self._logger = get_logger(_LOGGER_NAME)

    def send(self, content: str) -> None:
        """Send one rendered report.

        When no webhook is configured the message is not sent and a clear
        warning is logged instead. When the webhook answers with an error code
        the code and message are logged and raised, so a rejected message can
        never look like a delivered one.

        Args:
            content: Report text to send.

        Raises:
            AISException: When the webhook rejects the message.
            urllib.error.URLError: When the webhook cannot be reached.
        """
        if self._webhook_url is None:
            self._logger.warning(
                "no WeChat webhook configured (%s); message not sent",
                EnvVar.WECHAT_WEBHOOK_URL.value,
            )
            return

        payload = json.dumps({"msgtype": "text", "text": {"content": content}})
        request = urllib.request.Request(
            self._webhook_url,
            data=payload.encode("utf-8"),
            headers={"Content-Type": _CONTENT_TYPE},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as reply:
            answer = json.loads(reply.read().decode("utf-8"))

        errcode = int(answer.get("errcode", -1))
        if errcode != 0:
            message = (
                f"WeChat webhook rejected the message: errcode={errcode} "
                f"errmsg={answer.get('errmsg')!r}"
            )
            self._logger.error("%s", message)
            raise AISException(message)
        self._logger.info("report sent to WeChat")
