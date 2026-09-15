"""AIS mobile report renderer.

Renders one analysis result as the mobile projection of the Recommendation
Report: plain text, bounded in length, and honest about whatever is missing.

The renderer lives on the analysis side of the pipeline, not in the
Communication layer, because that layer transports a message and must not
create or reinterpret its content.

Reading order is the investor's: identity, then what was decided and how sure
AIS is, then the evidence behind it, and only then how good that evidence is
and what is missing from it.

Rules it follows:

* every category the Constitution defines is listed, in the canonical order of
  :data:`models.category.CATEGORY_ORDER`, and a category with no evaluator is
  rendered as ``NOT EVALUATED`` rather than as a score of zero;
* a value that does not exist is never rendered as a number, including the
  overall score, which is left unevaluated when no category could be assessed;
* the message always states whether the figures came from live market data;
* a report built on incomplete coverage says so, because a conclusion drawn
  from partial evidence is a weaker conclusion;
* an evidence entry is a list of lines, so that an explanation can be added
  beneath the value later. Evidence exists to explain a decision rather than to
  state a number, and this renderer must not cap that.

The evidence block is labelled ``EVIDENCE (max 3)`` rather than ``TOP
EVIDENCE``: no attribution method exists yet, so the entries are shown in
retrieval order and the report does not claim a ranking it cannot make.
"""

from __future__ import annotations

from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.report import data_quality_label
from contracts.market_data_provider import MarketDataPoint, MarketMetric
from models.category import CATEGORY_ORDER, Category

SECTION_SEPARATOR = "-" * 32
NOT_EVALUATED = "NOT EVALUATED"
PARTIAL_EVIDENCE_NOTICE = "Recommendation is based on partial evidence."

_MAX_EVIDENCE = 3
_CATEGORY_WIDTH = 11
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
_UNAVAILABLE_VALUE = "unavailable"

# Metrics that are ratios rather than counts, and read better as percentages.
_PERCENT_METRICS = frozenset({MarketMetric.FCF_YIELD})


def render_mobile_report(result: AnalysisResult, *, generated_at: datetime) -> str:
    """Render the analysis result as the mobile report.

    Args:
        result: Analysis result to render.
        generated_at: Moment the report was produced.

    Returns:
        Plain text report of at most about thirty lines, ready to be sent
        through a push channel.
    """
    lines = [
        f"AIS | {result.asset.ticker}",
        f"Generated {generated_at.strftime(_TIMESTAMP_FORMAT)}",
        SECTION_SEPARATOR,
        f"DECISION    {result.recommendation.decision_state.value.upper()}",
        f"CONFIDENCE  {result.recommendation.confidence:.2f}",
        _score_line(result),
        SECTION_SEPARATOR,
        "CATEGORIES",
        *_category_lines(result),
        SECTION_SEPARATOR,
        f"EVIDENCE (max {_MAX_EVIDENCE})",
        *_evidence_lines(result),
        SECTION_SEPARATOR,
        _data_line(result),
        _coverage_line(result),
        SECTION_SEPARATOR,
        "MISSING",
        *_missing_lines(result),
    ]
    return "\n".join(lines)


def _score_line(result: AnalysisResult) -> str:
    """Return the score line, or state that no score could be produced."""
    if not result.assessment.category_scores:
        return f"SCORE       {NOT_EVALUATED}"
    return f"SCORE       {result.assessment.overall_score:.2f}  (scale undefined)"


def _category_lines(result: AnalysisResult) -> list[str]:
    """Return one line per category, in the canonical category order.

    A category without an evaluator is rendered as ``NOT EVALUATED``. It is
    never rendered as a score, because a zero would read as the worst measured
    value rather than as an absent measurement.
    """
    assessed = {
        category_score.category: category_score
        for category_score in result.assessment.category_scores
    }
    lines: list[str] = []
    for category in CATEGORY_ORDER:
        category_score = assessed.get(category)
        if category_score is None:
            lines.append(f" {category.value:<{_CATEGORY_WIDTH}} {NOT_EVALUATED}")
        else:
            lines.append(
                f" {category.value:<{_CATEGORY_WIDTH}} "
                f"{category_score.score:.2f}  conf {category_score.confidence:.2f}"
            )
    return lines


def _evidence_lines(result: AnalysisResult) -> list[str]:
    """Return at most the mobile limit of evidence lines, in retrieval order."""
    snapshot = result.market_data
    if snapshot is None:
        return [" none: no market data source was connected"]
    available = snapshot.available_points[:_MAX_EVIDENCE]
    if not available:
        return [" none: no input could be retrieved"]

    lines: list[str] = []
    for point in available:
        lines.extend(_evidence_entry(point))
    return lines


def _evidence_entry(point: MarketDataPoint) -> list[str]:
    """Return the lines describing one piece of evidence.

    An entry is a list rather than a single line on purpose. Once evidence
    carries an explanation, that explanation is appended here as an indented
    line beneath the value, and nothing else in the report has to change.
    """
    return [f" {point.metric.label} {_format_value(point)}"]


def _data_line(result: AnalysisResult) -> str:
    """Return the line stating where the figures came from."""
    snapshot = result.market_data
    label = data_quality_label(result)
    if snapshot is None:
        return f"DATA        {label}"
    return f"DATA        {label} ({snapshot.source})"


def _coverage_line(result: AnalysisResult) -> str:
    """Return the line stating how much of the analysis could be performed."""
    assessed = len(result.assessment.category_scores)
    snapshot = result.market_data
    retrieved = 0 if snapshot is None else len(snapshot.available_points)
    total_inputs = 0 if snapshot is None else len(snapshot.points)
    return (
        f"COVERAGE    {assessed}/{len(Category)} categories, "
        f"{retrieved}/{total_inputs} inputs"
    )


def _missing_lines(result: AnalysisResult) -> list[str]:
    """Return the lines naming what this run could not include."""
    lines: list[str] = []
    unevaluated = len(Category) - len(result.assessment.category_scores)
    if unevaluated:
        lines.append(f" categories: {unevaluated} of {len(Category)} not evaluated")

    snapshot = result.market_data
    if snapshot is None:
        lines.append(" inputs: no market data source was connected")
    elif snapshot.missing_points:
        missing = ", ".join(point.metric.value for point in snapshot.missing_points)
        lines.append(f" inputs: {missing}")

    if _coverage_is_complete(result):
        return lines or [" none"]
    lines.append(f" {PARTIAL_EVIDENCE_NOTICE}")
    return lines


def _coverage_is_complete(result: AnalysisResult) -> bool:
    """Return whether every category and every input was available."""
    if len(result.assessment.category_scores) != len(Category):
        return False
    snapshot = result.market_data
    if snapshot is None:
        return False
    return not snapshot.missing_points


def _format_value(point: MarketDataPoint) -> str:
    """Format a retrieved value the way its metric is conventionally read."""
    if point.value is None:
        return _UNAVAILABLE_VALUE
    if point.metric in _PERCENT_METRICS:
        return f"{point.value:.2%}"
    return f"{point.value:.2f}"
