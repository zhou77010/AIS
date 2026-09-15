"""Contract for category evaluators.

A category evaluator consumes evidence and produces the assessment of a single
category. This module defines the interface only and holds no evaluation logic.
"""

from __future__ import annotations

from typing import Protocol

from evidence.evidence_collection import EvidenceCollection
from models.category_score import CategoryScore


class CategoryEvaluator(Protocol):
    """Contract for a component that assesses one category."""

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Assess one category from the evidence.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            Assessment of the single category this evaluator is bound to.
        """
