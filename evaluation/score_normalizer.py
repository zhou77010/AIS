"""AIS score normalizer.

Converts raw rule scores into the AIS standard scale. The current
implementation is a placeholder that passes scores through unchanged.
"""

from __future__ import annotations


class ScoreNormalizer:
    """Converts raw rule scores into the AIS standard scale."""

    def normalize(self, score: float) -> float:
        """Convert a raw rule score into the standard scale.

        Placeholder: the standard scale is not defined yet, so the score is
        returned unchanged.

        Args:
            score: Raw rule score.

        Returns:
            Score on the standard scale.
        """
        return score
