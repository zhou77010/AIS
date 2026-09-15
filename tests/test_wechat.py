"""Tests for the WeChat notification (Sprint A)."""

from __future__ import annotations

from communication.wechat import WeChatNotifier

_REPORT = "\n".join(["AIS | NVDA", "DECISION    ACCUMULATE"])


def test_send_without_a_webhook_logs_and_does_not_raise() -> None:
    WeChatNotifier(None).send(_REPORT)
