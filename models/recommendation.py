"""AIS recommendation domain model.

A recommendation is the analytical outcome reached for an asset: the decision
state, how confident that conclusion is, the thesis behind it, and an optional
summary.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.decision_state import DecisionState


@dataclass(frozen=True)
class Recommendation:
    """Analytical outcome reached for an asset.

    Attributes:
        decision_state: Decision state the recommendation expresses.
        confidence: Confidence in the recommendation, from 0.0 to 1.0.
        investment_thesis: Reasoning that justifies the recommendation.
        summary: Optional short summary of the recommendation.
    """

    decision_state: DecisionState
    confidence: float
    investment_thesis: str
    summary: str | None = None
