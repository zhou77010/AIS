"""Tests for the evaluation framework (Sprint 6)."""

from __future__ import annotations

import inspect

from evaluation.base_evaluator import BaseEvaluator
from evaluation.category_assembler import CategoryAssembler
from evaluation.evaluation_result import EvaluationResult
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evaluation.score_normalizer import ScoreNormalizer
from evidence.evidence_collection import EvidenceCollection
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore


class _DemoEvaluator(BaseEvaluator):
    """Category independent evaluator used only by the tests."""

    def evaluate(self, evidence: EvidenceCollection) -> CategoryScore:
        return CategoryAssembler(category=Category.MARKET, confidence=1.0).assemble(())


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    return RuleResult(
        rule_id="r1", score=2.0, reason="demo", evidence_references=("ev-1",)
    )


def test_score_normalizer_is_an_identity_placeholder() -> None:
    normalizer = ScoreNormalizer()

    assert normalizer.normalize(3.7) == 3.7
    assert normalizer.normalize(-1.0) == -1.0


def test_base_evaluator_is_abstract() -> None:
    assert inspect.isabstract(BaseEvaluator)
    assert getattr(BaseEvaluator.evaluate, "__isabstractmethod__", False) is True


def test_concrete_evaluator_produces_category_score() -> None:
    evaluator = _DemoEvaluator()
    evidence = EvidenceCollection(asset=_asset(), items=())

    score = evaluator.evaluate(evidence)

    assert isinstance(score, CategoryScore)
    assert score.category is Category.MARKET


def test_framework_components_compose() -> None:
    rule = EvaluationRule(
        id="r1",
        name="Rule one",
        description="demo",
        enabled=True,
        execute=_execute,
    )
    result = rule.execute(EvidenceCollection(asset=_asset(), items=()))
    evaluation = EvaluationResult(results=(result,))

    assert evaluation.results == (result,)
    assert result.rule_id == rule.id
