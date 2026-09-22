"""Expressing a Decision outward: the Recommendation.

A Recommendation is not a second judgement. It is the **same semantic object** as the
Decision, under the name its consumers use, and it holds exactly what the Decision
holds:
the answer, the grounds for it, and the evidence it rests on. If it ever carried a
field,
a rule or a lifecycle of its own, it would be a second Decision Layer.

**What changed here.** This module used to map an overall score onto a state through a
table of thresholds — a placeholder standing where a method would go. Measured over real
runs it produced the same state for every asset, every time, and the score behind it was
an average of raw measurements that treated a larger risk as a better reading. The
Decision now reaches the conclusion, and this module does nothing but say it in the
words
a reader receives.

**Two things here are provisional, and both are marked rather than hidden.**

* **The words.** A Decision outcome is mapped onto the vocabulary that already exists,
so
  that no reader-facing surface has to change at the same time. Which words a Decision
  should be said in is a naming decision that has not been taken.
* **The confidence.** The Decision Layer carries no aggregate confidence — the
  Constitution defers that aggregation — so the Recommendation carries the confidence it
  was handed by the assessment the Decision was reached from. Nothing here computes one.
"""

from __future__ import annotations

from models.decision_result import DecisionOutcome, DecisionResult
from models.decision_state import DecisionState
from models.recommendation import Recommendation

# How each Decision outcome is said in the vocabulary the reader already knows. It
# states
# what the Decision concluded rather than reaching a second conclusion: an asset worth
# becoming a standard position is said to be worth buying, one that is not is watched,
# and
# one whose question could not be answered is waited on.
_WORDS: dict[DecisionOutcome, DecisionState] = {
    DecisionOutcome.FAVOURABLE: DecisionState.BUY,
    DecisionOutcome.NOT_FAVOURABLE: DecisionState.WATCH,
    DecisionOutcome.CANNOT_ANSWER: DecisionState.WAIT,
}


class RecommendationEngine:
    """Turns a Decision into the object its consumers read."""

    def recommend(
        self, decision: DecisionResult, *, confidence: float
    ) -> Recommendation:
        """Return the Recommendation that expresses one Decision.

        Args:
            decision: The Decision reached for the asset.
            confidence: Confidence to carry, taken from the judgements the Decision was
                reached from. It is carried, never computed here.

        Returns:
            The Recommendation, holding the Decision's answer, grounds and evidence.
        """
        return Recommendation(
            decision_state=_WORDS[decision.outcome],
            confidence=confidence,
            investment_thesis=decision.summary,
            evidence_references=decision.evidence_references,
            summary=decision.summary,
        )
