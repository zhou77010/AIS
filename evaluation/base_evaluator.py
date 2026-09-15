"""AIS base evaluator.

The abstract base every category evaluator inherits from. It defines the
framework shape only and holds no category specific implementation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from evidence.evidence_collection import EvidenceCollection
from models.category_score import CategoryScore


class BaseEvaluator(ABC):
    """Abstract base for every category evaluator.

    Concrete evaluators implement evaluate to turn the evidence for one
    category into its category score.
    """

    @abstractmethod
    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Assess one category from the evidence.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            Assessment of the category this evaluator is bound to.
        """
