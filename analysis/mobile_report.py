"""AIS mobile report renderer.

Renders one analysis result as the mobile projection of the Recommendation
Report: plain text, written for an investor, and honest about what was not
looked at.

The renderer lives on the analysis side of the pipeline, not in the
Communication layer, because that layer transports a message and must not
create or reinterpret its content.

The report answers three questions, in this order:

* **What AIS concluded** — the decision and how much it can be trusted.
* **What each category says and why** — a grade, the measurements behind it in
  plain language, and how much of that category was actually looked at. The
  measurements are the support; the sentence is what is meant to be read.
* **What was not looked at** — the categories with no judgement, named.

Rules it follows:

* a grade is shown instead of a category score, because the scores are means of
  measurements on different scales and cannot be compared with one another. The
  grade is provisional and the report says so; see :mod:`analysis.category_grade`;
* a category with no judgement is named as not assessed rather than shown with a
  score of zero, because zero would read as the worst measured value rather than
  as an absent measurement;
* how much of a category was looked at is part of the sentence about it, not a
  separate line of model bookkeeping;
* measurements keep the names an investor already reads elsewhere, and the rest
  of the report is in the reader's language.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import grade_for_category, stars
from analysis.labels import (
    CATEGORY_DEFAULT_UNIT_NOUN,
    CATEGORY_UNIT_NOUNS,
    PERCENT_METRICS,
    SIGNED_METRICS,
    category_label,
    decision_label,
    metric_name,
)
from analysis.report import data_quality_label
from contracts.market_data_provider import MarketDataPoint
from models.category import CATEGORY_ORDER, Category
from models.category_score import CategoryScore

SECTION_SEPARATOR = "-" * 32

NO_GRADE = "暂无评级"
DATA_PREFIX = "行情数据"
NOT_ASSESSED_PREFIX = "尚未评估"

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_TIMEZONE_NOTE = "北京时间"

# Chinese characters occupy two columns, so the budget is in display columns.
_LINE_WIDTH = 42
_INDENT = " "
_FOOTER_LINES = (
    "综合评分刻度尚未定义，",
    "本报告只呈现证据与观察，不构成投资建议。",
)

# Scales for measurements that are counts, and are unreadable written out.
_COUNT_SCALES: tuple[tuple[float, str], ...] = (
    (1_000_000_000, "B"),
    (1_000_000, "M"),
)


def render_mobile_report(result: AnalysisResult, *, generated_at: datetime) -> str:
    """Render the analysis result as the mobile report.

    Args:
        result: Analysis result to render.
        generated_at: Moment the report was produced.

    Returns:
        Plain text report, ready to be sent through a push channel.
    """
    lines = [
        f"AIS 日报 · {result.asset.ticker}",
        f"{generated_at.strftime(_TIMESTAMP_FORMAT)} {_TIMEZONE_NOTE}",
        SECTION_SEPARATOR,
        _decision_line(result),
        SECTION_SEPARATOR,
    ]
    for category in CATEGORY_ORDER:
        lines.extend(_category_block(result, category))
    lines.append(SECTION_SEPARATOR)
    lines.extend(_not_assessed_lines(result))
    lines.extend(_data_lines(result))
    lines.extend(_FOOTER_LINES)
    return "\n".join(lines)


def _assessed_categories(result: AnalysisResult) -> dict[Category, CategoryScore]:
    """Return the categories a judgement was actually reached for.

    A category the assembler produced from no rule results carries no evidence
    references. That is an absent judgement rather than a score, and showing its
    zero would report the worst possible value for a dimension nothing looked
    at.
    """
    return {
        category_score.category: category_score
        for category_score in result.assessment.category_scores
        if category_score.evidence_references
    }


def _decision_line(result: AnalysisResult) -> str:
    """Return the line stating what AIS concluded."""
    state = decision_label(result.recommendation.decision_state)
    confidence = result.recommendation.confidence
    return f"结论  {state}          信心  {confidence:.0%}"


def _category_block(result: AnalysisResult, category: Category) -> list[str]:
    """Return the lines describing one category, empty when it was not judged."""
    category_score = _assessed_categories(result).get(category)
    if category_score is None:
        return []

    grade = grade_for_category(result, category)
    heading = f"{category_label(category)}  {stars(grade) if grade else NO_GRADE}"

    lines = [heading]
    lines.extend(_commentary_lines(result, category))
    lines.append(_INDENT + _coverage_phrase(category, category_score))
    return lines


def _commentary_lines(result: AnalysisResult, category: Category) -> list[str]:
    """Return what was measured for a category, in the reader's language."""
    phrases = [
        _measurement_phrase(point)
        for point in _measurements_of(result, category)
        if point.value is not None
    ]
    if not phrases:
        return [_INDENT + "尚未取得该类别所需的测量。"]
    return _pack(phrases, separator="、", trailing="。")


def _measurements_of(
    result: AnalysisResult, category: Category
) -> list[MarketDataPoint]:
    """Return the retrieved measurements that bear on one category."""
    snapshot = result.market_data
    if snapshot is None:
        return []
    return [
        point
        for point in snapshot.available_points
        if category in point.metric.categories
    ]


def _measurement_phrase(point: MarketDataPoint) -> str:
    """Return one measurement written the way it is read."""
    return f"{metric_name(point.metric)} {_format_value(point)}"


def _coverage_phrase(category: Category, category_score: CategoryScore) -> str:
    """Return how much of a category was looked at, as a sentence.

    Coverage belongs in the sentence about the category rather than on a line of
    its own: a reader wants to know how much of the judgement stands on, not to
    be handed a fraction to interpret.
    """
    coverage = category_score.coverage
    unit = CATEGORY_UNIT_NOUNS.get(category, CATEGORY_DEFAULT_UNIT_NOUN)
    if coverage.is_complete:
        return "该类别已完整评估。"
    if unit == CATEGORY_DEFAULT_UNIT_NOUN:
        return f"{coverage.total} {unit}中已评估 {coverage.assessed} {unit}。"
    return f"{coverage.total} {unit}中已评估 {coverage.assessed} 个。"


def _not_assessed_lines(result: AnalysisResult) -> list[str]:
    """Return the line naming the categories with no judgement."""
    assessed = _assessed_categories(result)
    missing = [
        category_label(category)
        for category in CATEGORY_ORDER
        if category not in assessed
    ]
    if not missing:
        return []
    return [f"{NOT_ASSESSED_PREFIX}  " + "、".join(missing)]


def _data_lines(result: AnalysisResult) -> list[str]:
    """Return where the figures came from.

    The source is named on its own line: the state of the data and the source it
    came from are two facts, and running them together makes one line that is
    too wide to read comfortably on a phone.
    """
    snapshot = result.market_data
    lines = [f"{DATA_PREFIX}  {data_quality_label(result)}"]
    if snapshot is not None:
        lines.append(f"来源  {snapshot.source}")
    return lines


def _pack(phrases: Sequence[str], *, separator: str, trailing: str) -> list[str]:
    """Pack phrases into as few lines as fit, never splitting one.

    Chinese characters and measurement values occupy different widths, so the
    packing counts display columns rather than characters.
    """
    budget = _LINE_WIDTH - _display_width(_INDENT) - _display_width(trailing)
    lines: list[str] = []
    current = ""
    for phrase in phrases:
        candidate = phrase if not current else f"{current}{separator}{phrase}"
        if current and _display_width(candidate) > budget:
            lines.append(f"{_INDENT}{current}{separator}")
            current = phrase
        else:
            current = candidate
    lines.append(f"{_INDENT}{current}{trailing}")
    return lines


def _display_width(text: str) -> int:
    """Return how many columns a string occupies, counting Chinese as two."""
    return sum(2 if _is_wide(character) else 1 for character in text)


def _is_wide(character: str) -> bool:
    """Return whether a character is drawn full width."""
    return unicodedata.east_asian_width(character) in {"W", "F"}


def _format_value(point: MarketDataPoint) -> str:
    """Format a retrieved measurement the way it is conventionally read."""
    if point.value is None:
        return "未取得"
    if point.metric in PERCENT_METRICS:
        if point.metric in SIGNED_METRICS:
            return f"{point.value:+.1%}"
        return f"{point.value:.1%}"
    for scale, suffix in _COUNT_SCALES:
        if abs(point.value) >= scale:
            return f"{point.value / scale:.1f}{suffix}"
    return f"{point.value:.2f}"
