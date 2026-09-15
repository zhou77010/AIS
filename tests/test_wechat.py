"""Tests for the WeChat notification (Sprint A)."""

from __future__ import annotations

from communication.wechat import WeChatNotifier, build_message
from models.decision_state import DecisionState
from models.recommendation import Recommendation


def _recommendation() -> Recommendation:
    return Recommendation(
        decision_state=DecisionState.ACCUMULATE,
        confidence=0.357,
        investment_thesis="Placeholder thesis.",
        evidence_references=("ev-1",),
    )


def test_build_message_uses_the_temporary_format() -> None:
    message = build_message(_recommendation(), "AAPL")

    assert message == (
        "--------------------------------\n"
        "AIS Recommendation\n"
        "Asset: AAPL\n"
        "Decision: accumulate\n"
        "Confidence: 0.36\n"
        "Investment Thesis:\n"
        "Placeholder thesis.\n"
        "--------------------------------"
    )


def test_send_without_a_webhook_logs_and_does_not_raise() -> None:
    WeChatNotifier(None).send(_recommendation(), "AAPL")
