"""Catalyst evaluator.

Reads the event layer and assembles the Catalyst category score.

The category question, from the Constitution, is what identifiable event could
change this picture, and when. The events come from
:mod:`contracts.catalyst_event_provider` rather than from individual rules, so a
new kind of event is a new source or a new row in a table and never a change to
this file.

**What the score is.** The distance to the nearest event that could change what
the market expects. It is not the number of events: a busy month and a quiet one
with one event in the same place read the same, because how crowded a calendar is
is not how large an opportunity is. The report writes the whole calendar out so
that a reader can see it; the score says only how soon something is coming.

**Coverage is per layer.** An event bears on the company, on its industry, or on
the conditions everything is valued under, and coverage counts the layers that
produced at least one event. One limitation is recorded rather than hidden: a
layer with nothing on it is counted as not covered, which conflates "nothing is
scheduled" with "nothing is connected". Telling those apart needs each source to
report the reach it has, and that is deferred.

**What is not done here.** No event is ranked by importance, no event is given a
probability, and nothing is summarised from news. AIS has no basis for any of
those, and a plausible ranking would be indistinguishable from a real one.
"""

from __future__ import annotations

from evaluation.base_evaluator import BaseEvaluator
from evaluation.catalyst import upcoming_rule
from evaluation.catalyst.event_reading import read_events
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.rule_engine import RuleEngine
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.catalyst_event import CatalystEventScope
from models.category import Category
from models.category_score import CategoryScore

_PLACEHOLDER_CONFIDENCE = 1.0


class CatalystEvaluator(BaseEvaluator):
    """Orchestrates the catalyst rule into one CategoryScore."""

    def __init__(self) -> None:
        """Create the evaluator with the catalyst rule."""
        self._rules = (upcoming_rule.RULE,)
        self._engine = RuleEngine()
        self._normalizer = ScoreNormalizer()
        self._assembler = CategoryAssembler(
            category=Category.CATALYST,
            confidence=_PLACEHOLDER_CONFIDENCE,
            total_units=len(CatalystEventScope),
        )

    def collect_results(self, evidence: EvidenceCollection) -> EvaluationResult:
        """Run the catalyst rule through the rule engine.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            EvaluationResult holding the rule outcome.
        """
        return self._engine.run(self._rules, evidence)

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        """Execute the rule, normalize its result and assemble the score.

        Args:
            evidence: Evidence collected for the asset.

        Returns:
            CategoryScore for the CATALYST category.
        """
        evaluation = self.collect_results(evidence)
        normalized = tuple(
            self._normalizer.normalize_result(result) for result in evaluation.results
        )
        return self._assembler.assemble(normalized, assessed=_layers_assessed(evidence))


def _layers_assessed(evidence: EvidenceCollection) -> int:
    """Return how many layers of the catalyst question produced an event."""
    return len({event.scope for event in read_events(evidence)})
