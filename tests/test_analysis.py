"""Tests for the asset analysis flow (Sprint 12)."""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from analysis.analyzer import AssetAnalyzer
from analysis.report import generate_report
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation


def _asset() -> Asset:
    return Asset(
        ticker="AAPL",
        name="Apple Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=AssetProfile.MATURE_TECH,
    )


def test_analyzer_returns_one_recommendation() -> None:
    recommendation = AssetAnalyzer().analyze(_asset())

    assert isinstance(recommendation, Recommendation)
    assert recommendation.investment_thesis


def test_analyzer_result_holds_every_stage() -> None:
    result = AssetAnalyzer().analyze_result(_asset())

    assert isinstance(result, AnalysisResult)
    assert result.asset == _asset()
    assert isinstance(result.assessment, OverallAssessment)
    assert isinstance(result.recommendation, Recommendation)
    assert result.assessment.category_scores


def test_analyze_delegates_to_the_single_orchestration_path() -> None:
    analyzer = AssetAnalyzer()
    asset = _asset()

    assert analyzer.analyze(asset) == analyzer.analyze_result(asset).recommendation


def test_analysis_preserves_evidence_traceability() -> None:
    result = AssetAnalyzer().analyze_result(_asset())
    merged = tuple(
        dict.fromkeys(
            reference
            for category_score in result.assessment.category_scores
            for reference in category_score.evidence_references
        )
    )
    decision = result.decision

    assert decision is not None
    # The recommendation expresses the Decision and adds nothing to it, so it carries
    # the
    # Decision's references rather than a second copy of the whole assessment's. A run
    # with
    # nothing to judge carries none, and says so rather than answering.
    assert result.recommendation.evidence_references == decision.evidence_references
    assert set(decision.evidence_references) <= set(merged)
    assert merged


def test_analysis_is_deterministic() -> None:
    analyzer = AssetAnalyzer()
    asset = _asset()

    assert analyzer.analyze(asset) == analyzer.analyze(asset)


def test_report_contains_every_required_fact() -> None:
    result = AssetAnalyzer().analyze_result(_asset())

    report = generate_report(result)

    assert result.asset.ticker in report
    assert result.asset.name in report
    assert result.assessment.category_scores[0].category.value in report
    assert str(result.assessment.overall_score) in report
    assert result.recommendation.decision_state.value in report
    assert str(result.recommendation.confidence) in report
    assert result.recommendation.investment_thesis in report
    for reference in result.recommendation.evidence_references:
        assert reference in report


def test_report_is_plain_line_based_text() -> None:
    report = generate_report(AssetAnalyzer().analyze_result(_asset()))

    assert isinstance(report, str)
    assert report.splitlines()[0] == "AIS analysis report"
