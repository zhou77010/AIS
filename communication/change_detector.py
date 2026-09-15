"""AIS recommendation change detection.

Suppresses a notification that would repeat a recommendation AIS has already
sent, so that an unchanged conclusion never becomes a stream of identical
messages.

The last fingerprint is held in memory only and is lost when the process stops.
That is the intended behaviour: a restarted process has not notified anyone, so
its first recommendation is sent again.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.decision_state import DecisionState
from models.recommendation import Recommendation


@dataclass(frozen=True)
class RecommendationFingerprint:
    """The comparable identity of a recommendation.

    The fingerprint holds the fields that make one recommendation a different
    recommendation from another. The prose fields are deliberately excluded:
    the thesis and the summary embed raw measurements, and those move on every
    retrieval, so a fingerprint built on them would never match and no
    notification would ever be suppressed.

    Attributes:
        symbol: Symbol the recommendation is about.
        decision_state: Decision the recommendation expresses.
        confidence: Confidence the recommendation carries.
        evidence_references: Identifiers of the evidence it rests on.
    """

    symbol: str
    decision_state: DecisionState
    confidence: float
    evidence_references: tuple[str, ...]

    @classmethod
    def of(
        cls, recommendation: Recommendation, symbol: str
    ) -> RecommendationFingerprint:
        """Build the fingerprint of one recommendation.

        Args:
            recommendation: Recommendation to fingerprint.
            symbol: Symbol the recommendation is about.

        Returns:
            Fingerprint of the recommendation.
        """
        return cls(
            symbol=symbol,
            decision_state=recommendation.decision_state,
            confidence=recommendation.confidence,
            evidence_references=recommendation.evidence_references,
        )

    def describe(self) -> str:
        """Return a compact one line description, fit for a log line."""
        return (
            f"{self.symbol} {self.decision_state.value} "
            f"confidence {self.confidence:.2f} "
            f"{len(self.evidence_references)} evidence reference(s)"
        )


class ChangeDetector:
    """Remembers the last recommendation fingerprint of every symbol it saw.

    One fingerprint is kept per symbol, because AIS watches several assets at
    once: a single slot would be overwritten by each asset in turn, so every
    cycle would look like a change and nothing would ever be suppressed.
    """

    def __init__(self) -> None:
        """Create a detector that has seen no recommendation yet."""
        self._last: dict[str, RecommendationFingerprint] = {}

    def last(self, symbol: str) -> RecommendationFingerprint | None:
        """Return the last fingerprint recorded for a symbol, or None.

        Args:
            symbol: Symbol to look up.

        Returns:
            The last fingerprint recorded for the symbol, or None when none is.
        """
        return self._last.get(symbol)

    def observe(self, fingerprint: RecommendationFingerprint) -> bool:
        """Record a fingerprint and report whether it differs from the last one.

        Args:
            fingerprint: Fingerprint of the recommendation just produced.

        Returns:
            True when the fingerprint differs from the last one recorded for the
            same symbol, which is also the case for the first one ever observed.
        """
        changed = fingerprint != self._last.get(fingerprint.symbol)
        self._last[fingerprint.symbol] = fingerprint
        return changed
