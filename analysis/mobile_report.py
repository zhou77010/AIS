"""AIS mobile report renderer.

Renders one analysis result as the mobile projection of the Recommendation
Report: plain text, bounded in length, and honest about whatever is missing.

The renderer lives on the analysis side of the pipeline, not in the
Communication layer, because that layer transports a message and must not
create or reinterpret its content.

Every block answers one of three questions, and nothing else is included:

* **What AIS concluded** — the decision, the confidence and the score.
* **Why AIS reached it** — the thesis, with the evidence that supports it
  directly beneath it. Evidence is the reason, so it is shown as part of the
  reason rather than as a separate list of numbers.
* **What we know, and what we do not** — every category with its state, what
  could not be assessed, and how much of the analysis the figures rest on.

Reading order is the investor's: identity, then the conclusion, then why, then
how much of the picture is actually filled in.

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

The evidence is not labelled ``TOP EVIDENCE``: no attribution method exists yet,
so the entries are shown in retrieval order and the report does not claim a
ranking it cannot make.
"""

from __future__ import annotations

import textwrap
from collections.abc import Sequence
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.report import data_quality_label
from contracts.market_data_provider import MarketDataPoint, MarketMetric
from models.category import CATEGORY_ORDER, Category

SECTION_SEPARATOR = "-" * 32
NOT_EVALUATED = "NOT EVALUATED"
PARTIAL_EVIDENCE_NOTICE = "Recommendation is based on partial evidence."
NO_MARKET_DATA_SOURCE = "no market data source was connected"

_MAX_EVIDENCE = 3
_MAX_THESIS_LINES = 3
_CATEGORY_WIDTH = 11
_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_WRAP_WIDTH = 40
_INDENT = " "
_UNAVAILABLE_VALUE = "unavailable"

# Metrics that are ratios rather than counts, and read better as percentages.
_PERCENT_METRICS = frozenset({MarketMetric.FCF_YIELD})


def render_mobile_report(result: AnalysisResult, *, generated_at: datetime) -> str:
    """Render the analysis result as the mobile report.

    Args:
        result: Analysis result to render.
        generated_at: Moment the report was produced.

    Returns:
        Plain text report, ready to be sent through a push channel.
    """
    lines = [
        f"AIS | {result.asset.ticker} | generated "
        f"{generated_at.strftime(_TIMESTAMP_FORMAT)}",
        SECTION_SEPARATOR,
        *_conclusion_lines(result),
        SECTION_SEPARATOR,
        *_reason_lines(result),
        SECTION_SEPARATOR,
        "CATEGORIES",
        *_category_lines(result),
        SECTION_SEPARATOR,
        "MISSING",
        *_missing_lines(result),
        SECTION_SEPARATOR,
        *_data_lines(result),
    ]
    return "\n".join(lines)


def _conclusion_lines(result: AnalysisResult) -> list[str]:
    """Return the decision, the confidence and the score."""
    return [
        f"DECISION    {result.recommendation.decision_state.value.upper()}",
        f"CONFIDENCE  {result.recommendation.confidence:.2f}",
        _score_line(result),
    ]


def _score_line(result: AnalysisResult) -> str:
    """Return the score line, or state that no score could be produced."""
    if not result.assessment.category_scores:
        return f"SCORE       {NOT_EVALUATED}"
    return f"SCORE       {result.assessment.overall_score:.2f}  (scale undefined)"


def _reason_lines(result: AnalysisResult) -> list[str]:
    """Return why AIS reached the recommendation, with the evidence behind it.

    The evidence sits under the thesis on purpose: a reader asking "why" wants
    the argument first and the numbers that carry it second, not a bare list of
    measurements to interpret alone.
    """
    return [
        "WHY",
        *_wrap(_thesis_text(result), limit=_MAX_THESIS_LINES),
        " Evidence",
        *_evidence_lines(result),
    ]


def _thesis_text(result: AnalysisResult) -> str:
    """Return the thesis, or a plain statement that none was given.

    A recommendation without a stated thesis cannot answer why it was reached,
    and the report says so rather than leaving the block empty.
    """
    thesis = result.recommendation.investment_thesis.strip()
    return thesis or "No thesis was given for this recommendation."


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
        return [f"  none: {NO_MARKET_DATA_SOURCE}"]
    available = snapshot.available_points[:_MAX_EVIDENCE]
    if not available:
        return ["  none: no measurement could be retrieved"]

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
    return [f"  {point.metric.label} {_format_value(point)}"]


def _missing_lines(result: AnalysisResult) -> list[str]:
    """Return the lines naming what this run could not include.

    The measurements are named with their human labels rather than their keys,
    because a reader who is told that ``dcf`` is unavailable has been told
    nothing they can act on.
    """
    lines: list[str] = []
    unevaluated = len(Category) - len(result.assessment.category_scores)
    if unevaluated:
        lines.append(f" {unevaluated} of {len(Category)} categories not evaluated")

    snapshot = result.market_data
    if snapshot is None:
        lines.append(f" {NO_MARKET_DATA_SOURCE}")
    elif snapshot.missing_points:
        lines.extend(
            _pack(
                [point.metric.label for point in snapshot.missing_points],
                prefix="Unavailable: ",
            )
        )

    if _coverage_is_complete(result):
        return lines or [" none"]
    lines.append(f" {PARTIAL_EVIDENCE_NOTICE}")
    return lines


def _coverage_is_complete(result: AnalysisResult) -> bool:
    """Return whether every category and every measurement was available."""
    if len(result.assessment.category_scores) != len(Category):
        return False
    snapshot = result.market_data
    if snapshot is None:
        return False
    return not snapshot.missing_points


def _data_lines(result: AnalysisResult) -> list[str]:
    """Return where the figures came from, and how much of the picture they cover."""
    snapshot = result.market_data
    label = data_quality_label(result)
    if snapshot is None:
        return [label, f" {NO_MARKET_DATA_SOURCE}"]

    retrieved = len(snapshot.available_points)
    assessed = len(result.assessment.category_scores)
    return [
        f"{label} - {snapshot.source}",
        f" {retrieved} of {len(snapshot.points)} measurements, "
        f"{assessed} of {len(Category)} categories",
    ]


def _pack(items: Sequence[str], prefix: str) -> list[str]:
    """Pack items into as few lines as will hold them, never splitting one.

    Wrapping on whitespace alone would break a measurement name across two
    lines, and "DCF fair" followed by "value" reads as two different
    measurements. Items are therefore packed whole.

    Nothing is ever dropped: when the items do not fit, the list grows rather
    than the content shrinking.

    Args:
        items: Items to lay out, in order.
        prefix: Text that starts the first line.

    Returns:
        The packed lines, indented to the report's text column.
    """
    limit = _WRAP_WIDTH - len(_INDENT)
    lines: list[str] = []
    current = prefix
    for item in items:
        separator = "" if current == prefix else ", "
        if current != prefix and len(current) + len(separator) + len(item) > limit:
            lines.append(f"{_INDENT}{current}")
            current = item
        else:
            current = f"{current}{separator}{item}"
    lines.append(f"{_INDENT}{current}")
    return lines


def _wrap(text: str, *, limit: int | None = None) -> list[str]:
    """Wrap text to the report width, keeping every line inside the budget.

    Args:
        text: Text to wrap.
        limit: Maximum number of lines, or None to wrap the whole text. A limit
            is only ever applied to prose, where an explicit ellipsis is an
            honest abbreviation. A list of facts is never truncated, because a
            reader who cannot see that something is missing will assume it is
            not.
    """
    return textwrap.wrap(
        text,
        width=_WRAP_WIDTH,
        initial_indent=_INDENT,
        subsequent_indent=_INDENT,
        max_lines=limit,
        placeholder=" ...",
    )


def _format_value(point: MarketDataPoint) -> str:
    """Format a retrieved value the way its metric is conventionally read."""
    if point.value is None:
        return _UNAVAILABLE_VALUE
    if point.metric in _PERCENT_METRICS:
        return f"{point.value:.2%}"
    return f"{point.value:.2f}"
