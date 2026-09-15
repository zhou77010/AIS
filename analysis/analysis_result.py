"""AIS analysis result.

One analysis run of a single asset: the asset itself, the overall assessment
reached for it, and the recommendation derived from that assessment.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.asset import Asset
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation


@dataclass(frozen=True)
class AnalysisResult:
    """Outcome of one analysis run for a single asset.

    The category scores are not duplicated here: they are reachable through the
    assessment, which is the model that owns them.

    Attributes:
        asset: Asset that was analysed.
        assessment: Overall assessment reached for the asset.
        recommendation: Recommendation derived from the assessment.
    """

    asset: Asset
    assessment: OverallAssessment
    recommendation: Recommendation
