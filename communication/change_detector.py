"""AIS recommendation change detection.

Suppresses a notification that would repeat a recommendation AIS has already
sent, so that an unchanged conclusion never becomes a stream of identical
messages.

The last fingerprint is written down, because a restart is not a reason to repeat a
conclusion: a process that comes back has still already told the reader what it thought,
and an unchanged recommendation re-sent after every restart is the message stream this
module exists to prevent. A fingerprint that cannot be read back is treated as absent,
and the first recommendation after that is sent — which is the honest answer when the
runtime genuinely does not know what it last said.
"""

from __future__ import annotations

from collections.abc import Mapping
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

    def snapshot(self) -> dict[str, object]:
        """Return every fingerprint held, in a form that can be written down."""
        return {
            symbol: {
                "decision_state": fingerprint.decision_state.value,
                "confidence": fingerprint.confidence,
                "evidence_references": list(fingerprint.evidence_references),
            }
            for symbol, fingerprint in self._last.items()
        }

    def restore(self, payload: Mapping[str, object]) -> int:
        """Fill the detector from a written payload and report how many it restored.

        A fingerprint that cannot be read is skipped, so a corrupt entry costs its own
        suppression and nothing else.

        Args:
            payload: What :meth:`snapshot` wrote, or an empty mapping.

        Returns:
            How many fingerprints were restored, for the log line that says so.
        """
        restored = 0
        for symbol, raw in payload.items():
            fingerprint = _as_fingerprint(symbol, raw)
            if fingerprint is None:
                continue
            self._last[symbol] = fingerprint
            restored += 1
        return restored

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


def _as_fingerprint(symbol: object, raw: object) -> RecommendationFingerprint | None:
    """Return the fingerprint a written payload holds, or None when it cannot be read.

    A fingerprint that is only half readable would suppress a message that was never
    sent, so anything unusable is reported as absent instead.
    """
    if not isinstance(symbol, str) or not isinstance(raw, Mapping):
        return None
    try:
        references = raw.get("evidence_references")
        return RecommendationFingerprint(
            symbol=symbol,
            decision_state=DecisionState(str(raw["decision_state"])),
            confidence=float(raw["confidence"]),
            evidence_references=(
                tuple(str(reference) for reference in references)
                if isinstance(references, (list, tuple))
                else ()
            ),
        )
    except (KeyError, TypeError, ValueError):
        return None
