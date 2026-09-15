"""Contract for notification channels.

A notification channel is any outbound communication channel, for example
WeChat, Email, Discord, or Telegram. This module defines the interface only
and holds no implementation.
"""

from __future__ import annotations

from typing import Protocol


class NotificationChannel(Protocol):
    """Contract for any outbound communication channel."""

    def send(self, recipient: str, content: str) -> None:
        """Send a message to a recipient.

        Args:
            recipient: Identifier of the message recipient.
            content: Body of the message.

        Returns:
            None.
        """
