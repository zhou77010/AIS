"""Runnable demonstration of the WeChat notification.

Run with: ``python -m communication.demo``.

Sends one dummy recommendation. No analysis pipeline is involved: the only goal
is verifying that WeChat receives the message.
"""

from __future__ import annotations

from communication.wechat import WeChatNotifier, build_message
from config.config import Config
from config.logging_config import configure_logging, get_logger
from models.decision_state import DecisionState
from models.recommendation import Recommendation

_DEMO_SYMBOL = "DEMO"


def main() -> None:
    """Send one dummy recommendation."""
    config = Config.from_environment()
    configure_logging(config)
    logger = get_logger("communication.demo")

    recommendation = Recommendation(
        decision_state=DecisionState.WATCH,
        confidence=0.42,
        investment_thesis="Dummy thesis used to verify the WeChat notification.",
        evidence_references=("demo.evidence",),
    )

    logger.info("message to send:")
    for line in build_message(recommendation, _DEMO_SYMBOL).splitlines():
        logger.info("%s", line)

    WeChatNotifier(config.wechat_webhook_url).send(recommendation, _DEMO_SYMBOL)


if __name__ == "__main__":
    main()
