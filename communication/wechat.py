"""AIS WeChat notification.

Sends one Recommendation to a WeChat group robot webhook. It is deliberately
the simplest synchronous implementation: one POST, no retries, no queue.
"""

from __future__ import annotations

import json
import urllib.request
from datetime import datetime

from config.logging_config import get_logger
from models.recommendation import Recommendation
from utils.constants import EnvVar
from utils.exceptions import AISException

_SEPARATOR = "-" * 32
_DEFAULT_TIMEOUT_SECONDS = 10.0
_LOGGER_NAME = "wechat"
_CONTENT_TYPE = "application/json"
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_message(
    recommendation: Recommendation,
    symbol: str,
    *,
    generated_at: datetime,
    data_source: str,
) -> str:
    """Build the text message for one recommendation.

    The message states which market data the recommendation was built on, so a
    result computed from placeholder evidence can never be mistaken for one
    computed from live data.

    Args:
        recommendation: Recommendation to render.
        symbol: Symbol of the asset the recommendation is about.
        generated_at: Moment the recommendation was produced.
        data_source: Label describing the market data the run used.

    Returns:
        Message text.
    """
    return "\n".join(
        [
            _SEPARATOR,
            "AIS Recommendation",
            f"Asset: {symbol}",
            f"Decision: {recommendation.decision_state.value}",
            f"Confidence: {recommendation.confidence:.2f}",
            f"Data: {data_source}",
            f"Generated: {generated_at.strftime(_TIMESTAMP_FORMAT)}",
            "Investment Thesis:",
            recommendation.investment_thesis,
            _SEPARATOR,
        ]
    )


class WeChatNotifier:
    """Sends a recommendation message to a WeChat webhook."""

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

    def send(
        self,
        recommendation: Recommendation,
        symbol: str,
        *,
        generated_at: datetime,
        data_source: str,
    ) -> None:
        """Send one recommendation message.

        When no webhook is configured the message is not sent and a clear
        warning is logged instead. When the webhook answers with an error code
        the code and message are logged and raised, so a rejected message can
        never look like a delivered one.

        Args:
            recommendation: Recommendation to send.
            symbol: Symbol of the asset the recommendation is about.
            generated_at: Moment the recommendation was produced.
            data_source: Label describing the market data the run used.

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

        content = build_message(
            recommendation,
            symbol,
            generated_at=generated_at,
            data_source=data_source,
        )
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
        self._logger.info("recommendation for %s sent to WeChat", symbol)
