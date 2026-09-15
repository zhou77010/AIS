"""AIS score normalizer.

Converts raw rule measurements into NormalizedScore values on the AIS standard
scale. The current implementation is a placeholder that passes measurements
through unchanged and applies no threshold.
"""

from __future__ import annotations

from dataclasses import replace

from evaluation.normalized_score import NormalizedScore
from evaluation.rule_result import RuleResult

_PLACEHOLDER_CONFIDENCE = 1.0


class ScoreNormalizer:
    """Converts raw rule measurements into the AIS standard scale."""

    def normalize(self, raw_value: float) -> NormalizedScore:
        """Convert one raw measurement into the standard scale.

        Placeholder: the standard scale is not defined yet, so the measurement
        is returned unchanged and no threshold is applied.

        Args:
            raw_value: Raw measurement produced by a rule.

        Returns:
            NormalizedScore carrying the unchanged measurement.
        """
        return NormalizedScore(
            raw_value=raw_value,
            normalized_value=raw_value,
            confidence=_PLACEHOLDER_CONFIDENCE,
            reason=f"Placeholder normalization of {raw_value}; standard scale pending.",
        )

    def normalize_result(self, result: RuleResult) -> NormalizedScore:
        """Convert one rule result into a normalized score.

        The reason and the evidence references of the rule result are preserved,
        so that normalization never loses the traceability of a measurement.

        Args:
            result: Rule result to convert.

        Returns:
            NormalizedScore carrying the measurement and its traceability.
        """
        return replace(
            self.normalize(result.score),
            reason=result.reason,
            evidence_references=result.evidence_references,
        )
