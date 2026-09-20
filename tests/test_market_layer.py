"""Tests for the market layer: the environment read, scored and interpreted.

The requirement this file exists for is one sentence long: Market must answer what the
current environment means for **this** asset, rather than how the index did. So the
tests below are about pairs. A rising yield is not a finding; a rising yield beside a
valuation that reads expensive is. A weak tape is not a finding; a weak tape beside a
high beta is.

The environment is shared, so the same snapshot appears in every fixture and the
assets differ around it. That is the shape of the thing being tested: one market, many
assets.
"""

from __future__ import annotations

import unicodedata
from dataclasses import replace
from datetime import UTC, datetime

from analysis.analysis_result import AnalysisResult
from analysis.brief import build_daily_brief
from analysis.brief_report import render_daily_brief
from analysis.category_grade import grade_for_category
from analysis.insight.builder import build_insights, insight_for
from analysis.insight.context import context_for
from analysis.insight.market_insight import environment_line
from analysis.mobile_report import render_mobile_report
from analysis.report import generate_report
from contracts.market_data_provider import (
    MarketDataPoint,
    MarketDataSnapshot,
    MarketMetric,
)
from contracts.market_environment import (
    EnvironmentMetric,
    EnvironmentPoint,
    EnvironmentSnapshot,
)
from evaluation.hpo.opportunity_assessor import OpportunityAssessor
from evaluation.market.market_evaluator import MarketEvaluator
from evaluation.reading.category import read_category
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore
from models.coverage import Coverage
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation
from pipeline.evidence_builder import EvidenceBuilder

# 09:00 Beijing, which is when the brief is owed and what the environment describes.
_MORNING = datetime(2026, 9, 18, 1, 0, tzinfo=UTC)

# A full set of measurements for one asset, taken from a real run.
_VALUES: dict[str, float] = {
    "pe": 38.2,
    "peg": 2.67,
    "ev_ebitda": 28.9,
    "fcf_yield": 0.022,
    "beta": 1.08,
    "debt_to_equity": 78.4,
    "current_ratio": 1.0,
    "average_volume": 53_800_000.0,
    "float_shares": 14_600_000_000.0,
    "profit_margin": 0.276,
    "return_on_equity": 1.488,
    "free_cash_flow_margin": 0.231,
    "market_direction": 0.149,
    "trend_range_position": 0.717,
    "trend_direction": 0.246,
    "earnings_growth": 0.271,
    "expected_earnings_change": 0.100,
    "trend_ma20_gap": 0.03,
    "trend_ma60_gap": 0.02,
    "trend_ma120_gap": 0.01,
    "trend_macd": 0.004,
    "trend_rsi": 58.0,
    "trend_volume_ratio": 0.05,
    "risk_volatility": 0.231,
    "risk_drawdown": -0.138,
    "short_percent_of_float": 0.0096,
    "short_ratio": 2.97,
    "institutional_ownership": 0.663,
    "insider_ownership": 0.0165,
}

# What the environment is doing in the fixtures, unless a test changes it.
_CALM_TAPE: dict[EnvironmentMetric, float] = {
    EnvironmentMetric.OVERNIGHT_EQUITY: 0.006,
    EnvironmentMetric.OVERNIGHT_GROWTH: 0.008,
    EnvironmentMetric.VOLATILITY: 14.8,
    EnvironmentMetric.VOLATILITY_CHANGE: -0.6,
    EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: 5.1,
}


def _environment(**overrides: float) -> EnvironmentSnapshot:
    """Return the environment, with the given measurements replaced."""
    values = {**_CALM_TAPE, **overrides}
    return EnvironmentSnapshot(
        source="Test environment",
        retrieved_at=_MORNING,
        points=tuple(
            EnvironmentPoint(
                metric=metric,
                value=values.get(metric),
                reason=f"Test environment: {metric.value}",
            )
            for metric in EnvironmentMetric
        ),
    )


def _asset(
    ticker: str = "APP", profile: AssetProfile = AssetProfile.HIGH_GROWTH
) -> Asset:
    return Asset(
        ticker=ticker,
        name=f"{ticker} Inc.",
        exchange="NASDAQ",
        currency="USD",
        profile=profile,
    )


def _snapshot(**values: float) -> MarketDataSnapshot:
    return MarketDataSnapshot(
        symbol="APP",
        source="Test source",
        retrieved_at=_MORNING,
        points=tuple(
            MarketDataPoint(
                metric=metric,
                value=values.get(metric.value),
                reason="test reason",
            )
            for metric in MarketMetric
        ),
    )


def _result(
    *,
    asset: Asset | None = None,
    environment: EnvironmentSnapshot | None = None,
    **values: float,
) -> AnalysisResult:
    """Return a result with its insights and opportunity built, as a run produces."""
    measured = {**_VALUES, **values}
    snapshot = _snapshot(**measured)
    result = AnalysisResult(
        asset=asset if asset is not None else _asset(),
        assessment=OverallAssessment(
            overall_score=12.0,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=tuple(
                CategoryScore(
                    category=category,
                    score=4.0,
                    confidence=1.0,
                    coverage=Coverage(assessed=1, total=1),
                    summary="summary",
                    evidence_references=(f"APP.market_data.{category.value}",),
                )
                for category in CATEGORY_ORDER
                if category is not Category.HPO
            ),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="Placeholder decision.",
            evidence_references=("APP.market_data.pe",),
        ),
        market_data=snapshot,
        environment=environment,
    )
    readings = {
        score.category: read_category(snapshot, score.category, environment=environment)
        for score in result.assessment.category_scores
    }
    result = replace(result, opportunity=OpportunityAssessor().assess(readings, 12))
    return replace(result, insights=build_insights(result))


def _market_lines(result: AnalysisResult) -> list[str]:
    insight = insight_for(result, Category.MARKET)
    return [] if insight is None else [line.text for line in insight.lines]


# --------------------------------------------------------------------------
# The environment is evidence, read like any other
# --------------------------------------------------------------------------


def test_the_environment_is_read_beside_the_assets_own_measurements() -> None:
    reading = read_category(
        _snapshot(**_VALUES), Category.MARKET, environment=_environment()
    )

    metrics = {read.metric for read in reading.reads}

    assert MarketMetric.MARKET_DIRECTION in metrics
    assert EnvironmentMetric.OVERNIGHT_EQUITY in metrics
    assert EnvironmentMetric.VOLATILITY in metrics


def test_a_category_that_the_environment_does_not_serve_does_not_read_it() -> None:
    # The environment answers the Market question and no other. Letting it leak into
    # Valuation would price an asset off the weather.
    reading = read_category(
        _snapshot(**_VALUES), Category.VALUATION, environment=_environment()
    )

    assert all(
        isinstance(read.metric, MarketMetric) for read in reading.reads
    ), reading.reads


def test_risk_appetite_and_volatility_are_graded_and_rates_is_not() -> None:
    # A tape that is being bought and a market that is calm are favourable conditions
    # for owning risk. A rise in the cost of money is not favourable or unfavourable
    # in itself, so it is described and never scored.
    reading = read_category(
        _snapshot(**_VALUES), Category.MARKET, environment=_environment()
    )
    scores = {read.metric: read.score for read in reading.reads}

    assert scores[EnvironmentMetric.OVERNIGHT_EQUITY] is not None
    assert scores[EnvironmentMetric.VOLATILITY] is not None
    assert scores[EnvironmentMetric.TEN_YEAR_YIELD_CHANGE] is None


def test_a_measurement_knows_whether_it_moved() -> None:
    calm = context_for(_result(environment=_environment()), Category.MARKET)
    moving = context_for(
        _result(
            environment=_environment(**{EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: 12.0})
        ),
        Category.MARKET,
    )

    assert calm.moved(EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) is True
    assert moving.moved(EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) is True
    assert (
        calm.moved(EnvironmentMetric.VOLATILITY_CHANGE) is False
    ), "a flat band is not a move"
    assert moving.rose(EnvironmentMetric.TEN_YEAR_YIELD_CHANGE) is True


# --------------------------------------------------------------------------
# The rules close the aspects that were open
# --------------------------------------------------------------------------


def _evidence(result: AnalysisResult):
    return EvidenceBuilder().build(
        result.asset, result.market_data, result.events, result.environment
    )


def test_the_environment_closes_the_aspects_that_were_open() -> None:
    # Volatility and rates were listed as aspects of the environment while nothing
    # measured them, so the category reported one of three. The evidence is what
    # closes them, not a changed aspect set.
    without = MarketEvaluator().evaluate(
        EvidenceBuilder().build(_asset(), _snapshot(**_VALUES))
    )
    with_environment = MarketEvaluator().evaluate(
        _evidence(_result(environment=_environment()))
    )

    assert without.coverage.describe() == "1/4"
    assert with_environment.coverage.describe() == "4/4"
    assert with_environment.coverage.is_complete is True


def test_the_environment_is_recorded_as_evidence_under_the_market_category() -> None:
    evidence = _evidence(_result(environment=_environment()))
    items = {
        item.id: item for item in evidence.items if item.id.startswith("environment.")
    }

    assert "environment.volatility" in items
    assert items["environment.volatility"].category is Category.MARKET
    assert items["environment.volatility"].metadata["market_metric"] == "volatility"


def test_a_shared_fact_carries_no_ticker_in_its_identifier() -> None:
    # The fact belongs to the market, not to this asset: the identifier says which of
    # the two a reader is looking at.
    evidence = _evidence(_result(environment=_environment()))

    assert all(
        not item.id.startswith("APP") for item in evidence.items if item.id[:1] == "e"
    )


def test_a_missing_environment_measurement_is_recorded_with_its_reason() -> None:
    environment = EnvironmentSnapshot(
        source="Test environment",
        retrieved_at=_MORNING,
        points=tuple(
            EnvironmentPoint(metric=metric, value=None, reason="the source was down")
            for metric in EnvironmentMetric
        ),
    )
    evidence = _evidence(_result(environment=environment))
    item = next(item for item in evidence.items if item.id == "environment.volatility")

    assert item.confidence == 0.0
    assert item.description == "the source was down"


# --------------------------------------------------------------------------
# What the environment means for this asset
# --------------------------------------------------------------------------


def test_the_first_sentence_is_about_this_asset_and_the_second_is_the_market() -> None:
    result = _result(environment=_environment(), pe=41.0)
    insight = insight_for(result, Category.MARKET)

    assert insight is not None
    assert insight.lines[0].text == "利率上行而估值很贵，分母端承压。"
    assert "环境对风险资产" in insight.lines[1].text


def test_a_sentence_names_the_environment_and_the_asset_it_was_read_from() -> None:
    result = _result(environment=_environment(), pe=41.0)
    line = insight_for(result, Category.MARKET).lines[0]

    assert "environment.ten_year_yield_change" in line.references
    assert any(
        reference.startswith("APP.market_data.") for reference in line.references
    ), line.references


def test_a_rising_yield_beside_an_expensive_valuation_presses_the_multiple() -> None:
    # Any of the three measurements that can call a valuation dear is enough: a
    # multiple and a cash flow yield are views of the same thing, and requiring all
    # of them would let an asset be called cheap because only one scale agreed.
    dear = _market_lines(_result(environment=_environment(), pe=41.0))
    cheap = _market_lines(
        _result(environment=_environment(), pe=9.0, ev_ebitda=6.0, fcf_yield=0.08)
    )

    assert any("分母端承压" in line for line in dear), dear
    assert not any("分母端承压" in line for line in cheap), cheap


def test_a_falling_yield_does_not_press_a_dear_valuation() -> None:
    lines = _market_lines(
        _result(
            environment=_environment(**{EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: -8.0}),
            pe=41.0,
        )
    )

    assert not any("分母端承压" in line for line in lines), lines


def test_a_high_beta_in_a_weak_tape_widens_the_warning() -> None:
    lines = _market_lines(
        _result(
            environment=_environment(
                **{
                    EnvironmentMetric.OVERNIGHT_EQUITY: -0.012,
                    EnvironmentMetric.VOLATILITY_CHANGE: 4.0,
                }
            ),
            beta=2.1,
        )
    )

    assert any("波动可能放大" in line for line in lines), lines
    assert any("盘前明显走弱" in line for line in lines), lines


def test_a_low_beta_in_a_weak_tape_reads_as_defensive() -> None:
    lines = _market_lines(
        _result(
            environment=_environment(**{EnvironmentMetric.OVERNIGHT_EQUITY: -0.012}),
            beta=0.6,
        )
    )

    assert any("相对抗跌" in line for line in lines), lines


def test_a_strong_tape_says_nothing_about_beta() -> None:
    # The exposure only matters when the environment is against it: a beta is not a
    # finding on a day when the tape is being bought.
    lines = _market_lines(_result(environment=_environment(), beta=2.1))

    assert not any("波动可能放大" in line for line in lines), lines


def test_growth_lagging_beside_a_growth_company_reads_as_under_pressure() -> None:
    lagging = _environment(
        **{
            EnvironmentMetric.OVERNIGHT_EQUITY: 0.006,
            EnvironmentMetric.OVERNIGHT_GROWTH: -0.004,
        }
    )

    growth = _market_lines(_result(environment=lagging))
    defensive = _market_lines(
        _result(
            environment=lagging,
            asset=_asset("HSBC", AssetProfile.FINANCIAL),
        )
    )

    assert any("属成长型" in line for line in growth), growth
    assert not any("属成长型" in line for line in defensive), defensive


def test_a_bank_is_told_the_direction_needs_the_curve() -> None:
    # One yield is not the curve, so the exposure is named and the direction is not
    # claimed. Reading a direction out of one yield would be a guess.
    lines = _market_lines(
        _result(
            asset=_asset("HSBC", AssetProfile.FINANCIAL),
            environment=_environment(),
        )
    )

    assert any("收益率曲线" in line for line in lines), lines
    assert any("目前判断不了" in line for line in lines), lines


def test_an_asset_the_environment_does_not_reach_is_told_that() -> None:
    calm = _environment(
        **{
            EnvironmentMetric.OVERNIGHT_EQUITY: 0.001,
            EnvironmentMetric.OVERNIGHT_GROWTH: 0.001,
            EnvironmentMetric.VOLATILITY_CHANGE: 0.2,
            EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: 1.0,
        }
    )

    lines = _market_lines(_result(environment=calm))

    assert any("影响有限" in line for line in lines), lines


def test_a_sentence_never_claims_a_market_it_did_not_read() -> None:
    lines = _market_lines(_result(environment=_environment(**{}), beta=2.1))
    joined = " ".join(lines)

    assert "美元" not in joined
    assert "行业" not in joined


def test_without_an_environment_the_broad_market_is_still_answered() -> None:
    result = _result(market_direction=0.25)

    assert _market_lines(result) == ["大盘整体上行，环境对风险资产偏友好。"]


def test_the_environment_sentence_is_the_same_for_every_asset() -> None:
    first = environment_line(
        context_for(_result(environment=_environment(), pe=9.0), Category.MARKET)
    )
    second = environment_line(
        context_for(
            _result(
                asset=_asset("HSBC", AssetProfile.FINANCIAL),
                environment=_environment(),
                beta=2.0,
            ),
            Category.MARKET,
        )
    )

    assert first is not None and second is not None
    assert first.text == second.text


# --------------------------------------------------------------------------
# What the report and the brief do with it
# --------------------------------------------------------------------------


def test_the_grade_moves_with_the_environment() -> None:
    result = _result(environment=_environment())

    assert grade_for_category(result, Category.MARKET) is not None


def test_the_expanded_report_writes_the_environment_out_once() -> None:
    report = generate_report(_result(environment=_environment()))

    assert "Environment (Test environment):" in report
    assert "overnight_equity" in report
    assert "ten_year_yield_change" in report


def test_the_phone_shows_the_impact_and_not_the_environment_repeat() -> None:
    # The phone shows the first sentence of a category, so the first sentence of
    # Market has to be the one about this asset.
    report = render_mobile_report(
        _result(environment=_environment(), pe=41.0), generated_at=_MORNING
    )

    assert "利率上行而估值很贵，分母端承压。" in report


def test_the_brief_states_the_environment_once_for_the_whole_universe() -> None:
    environment = _environment()
    results = [
        _result(asset=_asset(ticker), environment=environment)
        for ticker in ("AAPL", "CGDV", "APP")
    ]

    report = render_daily_brief(build_daily_brief(results, moment=_MORNING))

    assert report.count("市场环境") == 1, report
    assert "环境对风险资产偏友好" in report
    assert report.index("市场环境") < report.index("AAPL")


def test_the_brief_says_nothing_about_the_market_it_did_not_read() -> None:
    results = [_result(asset=_asset("AAPL"))]
    brief = build_daily_brief(results, moment=_MORNING)

    assert brief.environment is None
    assert "市场环境" not in render_daily_brief(brief)


def test_the_brief_keeps_its_budget_with_the_environment_in_it() -> None:
    environment = _environment(
        **{
            EnvironmentMetric.OVERNIGHT_EQUITY: -0.012,
            EnvironmentMetric.OVERNIGHT_GROWTH: -0.004,
            EnvironmentMetric.VOLATILITY_CHANGE: 6.0,
            EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: 12.0,
        }
    )
    results = [
        _result(
            asset=_asset(ticker, AssetProfile.HIGH_GROWTH),
            environment=environment,
            beta=2.1,
        )
        for ticker in ("AAPL", "CGDV", "APP", "BABA", "HSBC", "MNST", "RKLB")
    ]

    report = render_daily_brief(build_daily_brief(results, moment=_MORNING))
    lines = report.splitlines()

    assert len(lines) <= 24, report
    for line in lines:
        assert _width(line) <= 42, line


def test_the_environment_line_is_broken_between_clauses() -> None:
    # A sentence of clauses reads as clauses: breaking one in half makes the reader
    # reassemble a phrase they had already understood.
    environment = _environment(**{EnvironmentMetric.TEN_YEAR_YIELD_CHANGE: 12.0})
    report = render_daily_brief(
        build_daily_brief([_result(environment=environment)], moment=_MORNING)
    )
    lines = [line for line in report.splitlines() if line.startswith("市场环境")]

    assert lines and lines[0].rstrip().endswith(("、", "，")), report


def _width(line: str) -> int:
    """Return how many columns a line occupies, counting Chinese as two."""
    return sum(
        2 if unicodedata.east_asian_width(character) in {"W", "F"} else 1
        for character in line
    )
