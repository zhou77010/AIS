"""Tests for the overall evaluation and recommendation (Sprint 11)."""

from __future__ import annotations

import dataclasses
import inspect

import pytest

import models.overall_assessment as overall_assessment_module
from contracts.overall_evaluator import OverallEvaluator as OverallEvaluatorContract
from contracts.recommendation_engine import (
    RecommendationEngine as RecommendationEngineContract,
)
from core.overall_evaluator import OverallEvaluator
from core.recommendation_engine import RecommendationEngine
from evaluation.valuation.valuation_evaluator import ValuationEvaluator
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import Category
from models.category_score import CategoryScore
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder


def _category_score(score: float, *references: str) -> CategoryScore:
    """Return a category score carrying the given evidence references."""
    return CategoryScore(
        category=Category.VALUATION,
        score=score,
        confidence=1.0,
        summary="placeholder",
        evidence_references=references,
    )


def _assessment(
    overall_score: float, *category_scores: CategoryScore
) -> OverallAssessment:
    """Return an overall assessment for the given score and category scores."""
    return OverallAssessment(
        overall_score=overall_score,
        confidence=0.7,
        grade="PLACEHOLDER",
        category_scores=category_scores,
    )


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def test_overall_assessment_carries_no_recommendation_field() -> None:
    field_names = [field.name for field in dataclasses.fields(OverallAssessment)]

    assert "recommendation" not in field_names


def test_overall_assessment_does_not_depend_on_recommendation() -> None:
    assert not hasattr(overall_assessment_module, "Recommendation")


def test_overall_evaluator_returns_an_assessment() -> None:
    category_scores = (_category_score(10.0, "ev-1"),)

    assessment = OverallEvaluator().evaluate(category_scores)

    assert isinstance(assessment, OverallAssessment)
    assert assessment.category_scores == category_scores


def test_overall_evaluator_uses_placeholder_score_and_grade() -> None:
    assessment = OverallEvaluator().evaluate(
        (_category_score(10.0), _category_score(30.0))
    )

    assert assessment.overall_score == 20.0
    assert assessment.grade == "PLACEHOLDER"
    assert assessment.confidence == 1.0


def test_overall_evaluator_handles_no_category_scores() -> None:
    assessment = OverallEvaluator().evaluate(())

    assert assessment.overall_score == 0.0
    assert assessment.category_scores == ()


@pytest.mark.parametrize(
    ("overall_score", "expected"),
    [
        (100.0, DecisionState.BUY),
        (80.0, DecisionState.BUY),
        (79.9, DecisionState.ACCUMULATE),
        (60.0, DecisionState.ACCUMULATE),
        (59.9, DecisionState.HOLD),
        (40.0, DecisionState.HOLD),
        (39.9, DecisionState.WATCH),
        (0.0, DecisionState.WATCH),
    ],
)
def test_recommendation_engine_placeholder_mapping(
    overall_score: float, expected: DecisionState
) -> None:
    recommendation = RecommendationEngine().recommend(_assessment(overall_score))

    assert recommendation.decision_state is expected


def test_recommendation_engine_preserves_evidence_traceability() -> None:
    assessment = _assessment(
        70.0,
        _category_score(10.0, "ev-1", "ev-2"),
        _category_score(20.0, "ev-2", "ev-3"),
    )

    recommendation = RecommendationEngine().recommend(assessment)

    assert recommendation.evidence_references == ("ev-1", "ev-2", "ev-3")


def test_recommendation_engine_carries_the_assessment_confidence() -> None:
    recommendation = RecommendationEngine().recommend(_assessment(50.0))

    assert recommendation.confidence == 0.7
    assert "Placeholder" in recommendation.investment_thesis


def test_implementations_match_their_contracts() -> None:
    overall_parameters = inspect.signature(OverallEvaluator.evaluate).parameters
    contract_overall_parameters = inspect.signature(
        OverallEvaluatorContract.evaluate
    ).parameters
    recommendation_parameters = inspect.signature(
        RecommendationEngine.recommend
    ).parameters
    contract_recommendation_parameters = inspect.signature(
        RecommendationEngineContract.recommend
    ).parameters

    assert list(overall_parameters) == list(contract_overall_parameters)
    assert list(recommendation_parameters) == list(contract_recommendation_parameters)


def test_complete_pipeline_produces_a_recommendation() -> None:
    evidence = EvidenceBuilder().build(_asset())

    category_score = ValuationEvaluator().evaluate(evidence)
    assessment = OverallEvaluator().evaluate((category_score,))
    recommendation = RecommendationEngine().recommend(assessment)

    assert isinstance(category_score, CategoryScore)
    assert isinstance(assessment, OverallAssessment)
    assert isinstance(recommendation, Recommendation)
    assert recommendation.evidence_references == category_score.evidence_references


def test_complete_pipeline_is_deterministic() -> None:
    evidence = EvidenceBuilder().build(_asset())

    def run() -> Recommendation:
        category_score = ValuationEvaluator().evaluate(evidence)
        return RecommendationEngine().recommend(
            OverallEvaluator().evaluate((category_score,))
        )

    assert run() == run()
