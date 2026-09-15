"""Tests for the WeChat notification (Sprint A)."""

from __future__ import annotations

from datetime import datetime

from communication.wechat import WeChatNotifier, build_message
from models.decision_state import DecisionState
from models.recommendation import Recommendation

_GENERATED_AT = datetime(2026, 9, 16, 9, 30, 0)
_DATA_SOURCE = "Live Market Data (Yahoo Finance; 4 of 5 metrics)"


def _recommendation() -> Recommendation:
    return Recommendation(
        decision_state=DecisionState.ACCUMULATE,
        confidence=0.357,
        investment_thesis="Placeholder thesis.",
        evidence_references=("ev-1",),
    )


def test_build_message_states_the_decision_the_time_and_the_data_source() -> None:
    message = build_message(
        _recommendation(),
        "AAPL",
        generated_at=_GENERATED_AT,
        data_source=_DATA_SOURCE,
    )

    assert message == (
        "--------------------------------\n"
        "AIS Recommendation\n"
        "Asset: AAPL\n"
        "Decision: accumulate\n"
        "Confidence: 0.36\n"
        f"Data: {_DATA_SOURCE}\n"
        "Generated: 2026-09-16 09:30:00\n"
        "Investment Thesis:\n"
        "Placeholder thesis.\n"
        "--------------------------------"
    )


def test_send_without_a_webhook_logs_and_does_not_raise() -> None:
    WeChatNotifier(None).send(
        _recommendation(),
        "AAPL",
        generated_at=_GENERATED_AT,
        data_source=_DATA_SOURCE,
    )
