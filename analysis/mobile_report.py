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
    DAY_METRICS,
    PERCENT_METRICS,
    SIGNED_METRICS,
    UNASSESSED_ITEMS,
    catalyst_kind_label,
    catalyst_kind_reason,
    catalyst_scope_label,
    category_label,
    decision_label,
    driver_phrase,
    is_improvement,
    metric_name,
    opportunity_condition_label,
)
from analysis.plain_language import (
    measurements_of,
    opportunity_sentence,
    sentence_for,
)
from analysis.report import data_quality_label
from contracts.market_data_provider import MarketDataPoint
from models.catalyst_event import CatalystEvent, CatalystEventScope
from models.category import CATEGORY_ORDER, Category
from models.category_rating import CategoryRating
from models.category_score import CategoryScore

SECTION_SEPARATOR = "-" * 32

NO_GRADE = "暂无评级"
DATA_PREFIX = "行情数据"
NOT_ASSESSED_PREFIX = "尚未评估"

# What is said when there is nothing on the calendar. It is an answer to the
# question rather than a gap in it, so it is written as a sentence.
_NO_CATALYST_SENTENCE = "近期暂无明确催化。"

# How much of the calendar is written out. A reader needs the near ones, not an
# agenda: a meeting a year and a half away is a fact about the calendar and not
# something to watch this month.
_EVENT_WINDOW_DAYS = 90
_MAX_EVENTS = 6
_MAX_EVENTS_PER_SCOPE = 3

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_TIMEZONE_NOTE = "北京时间"

# Chinese characters occupy two columns, so the budget is in display columns.
_LINE_WIDTH = 42
_INDENT = " "

# Below this, a movement rounds to nothing and is not worth a line.
_MOMENTUM_FLOOR = 0.005
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
        lines.extend(_category_block(result, category, generated_at))
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


def _category_block(
    result: AnalysisResult, category: Category, moment: datetime
) -> list[str]:
    """Return the lines describing one category, empty when it was not judged."""
    if category is Category.HPO:
        return _opportunity_block(result)
    if category is Category.CATALYST:
        return _catalyst_block(result, category, moment)
    if category not in _assessed_categories(result):
        return []

    grade = grade_for_category(result, category)
    heading = f"{category_label(category)}  {stars(grade) if grade else NO_GRADE}"
    return [
        heading,
        *_movement_lines(result, category, moment),
        *_commentary_lines(result, category),
    ]


def _catalyst_block(
    result: AnalysisResult, category: Category, moment: datetime
) -> list[str]:
    """Return what could change the investment case, and why each thing matters.

    The block writes the calendar out and not the score: which events are coming,
    grouped by whether they bear on the company, on its industry or on the
    conditions everything is valued under, each with one clause saying why that
    sort of event matters. A reader who wants to know what to watch next month
    gets an answer from this block and not from a number.

    The grade is shown above all of it and answers a different question — how
    soon the nearest of them falls. An empty calendar is an answer too, and it is
    written as one rather than left as a category nothing was done about.
    """
    assessed = category in _assessed_categories(result)
    grade = grade_for_category(result, category) if assessed else None
    lines = [f"{category_label(category)}  {stars(grade) if grade else NO_GRADE}"]
    if assessed:
        lines.extend(_movement_lines(result, category, moment))

    sentence = sentence_for(result, category) or _NO_CATALYST_SENTENCE
    lines.extend(_pack([sentence], separator="", trailing=""))
    lines.extend(_event_lines(result, moment))
    return lines


def _event_lines(result: AnalysisResult, moment: datetime) -> list[str]:
    """Return the forthcoming events within the window, grouped by layer.

    What falls outside the window is counted rather than listed. A calendar
    reaching into the following year is a fact about the calendar, and writing it
    out would bury the two events a reader could act on.
    """
    upcoming = [
        event
        for event in result.events
        if event.is_upcoming(moment) and event.days_from(moment) <= _EVENT_WINDOW_DAYS
    ]
    if not upcoming:
        return []

    lines: list[str] = []
    budget = _MAX_EVENTS
    for scope in CatalystEventScope:
        if budget <= 0:
            break
        in_scope = sorted(
            (event for event in upcoming if event.scope is scope),
            key=lambda event: (event.days_from(moment), event.kind),
        )
        if not in_scope:
            continue
        shown = in_scope[: min(len(in_scope), _MAX_EVENTS_PER_SCOPE, budget)]
        budget -= len(shown)
        lines.append(f"{_INDENT}{catalyst_scope_label(scope)}")
        lines.extend(_event_line(event, moment) for event in shown)
        hidden = len(in_scope) - len(shown)
        if hidden:
            lines.append(_INDENT + f"· 另有 {hidden} 项未列出")
    return lines


def _event_line(event: CatalystEvent, moment: datetime) -> str:
    """Return one event as a line: when it is, what it is, and why it matters."""
    name = catalyst_kind_label(event.kind, event.description)
    reason = catalyst_kind_reason(event.kind)
    confirmation = "" if event.confirmed else "（未确认）"
    return f"{_INDENT}· {_when(event, moment)}{name}{confirmation} — {reason}"


def _when(event: CatalystEvent, moment: datetime) -> str:
    """Return when an event falls, in the words a reader would use."""
    days = event.days_from(moment)
    if days <= 0:
        return "今日 "
    if days == 1:
        return "明日 "
    if days <= 14:
        return f"{days} 天后 "
    return f"{event.occurs_on.month}月{event.occurs_on.day}日 "


def _opportunity_block(result: AnalysisResult) -> list[str]:
    """Return the lines describing whether this is worth allocating to today.

    The opportunity judgement is written first among the categories because it is
    the one an investor reads to decide whether to read the rest. It is shown
    with the same stars a category is shown with, because it is a count of the
    same kind of thing, and it carries no number of its own.
    """
    opportunity = result.opportunity
    if opportunity is None:
        return []

    heading = (
        f"{category_label(Category.HPO)}  "
        f"{stars(opportunity.grade) if opportunity.grade else NO_GRADE}"
    )
    lines = [
        heading,
        *_pack([opportunity_sentence(opportunity)], separator="", trailing=""),
    ]
    unknown = [result.condition for result in opportunity.unknown]
    if unknown:
        phrases = [
            opportunity_condition_label(condition, False) for condition in unknown
        ]
        lines.extend(
            _pack([f"未评估的条件：{'、'.join(phrases)}。"], separator="", trailing="")
        )
    return lines


def _movement_lines(
    result: AnalysisResult, category: Category, moment: datetime
) -> list[str]:
    """Return how far a category has moved inside its grade, and why.

    A grade says where a category stands. This says whether it is moving inside
    that standing, which a grade cannot show: a category can improve for weeks
    without crossing into the next grade.

    A movement is only useful if a reader is told three things: how much, for
    how long, and why. A bare arrow answers the first and leaves the other two
    to be guessed at, so all three are always written together.
    """
    rating = result.rating_for(category)
    if rating is None:
        return []
    if rating.changed:
        return [_INDENT + _change_note(rating)]
    if abs(rating.momentum) < _MOMENTUM_FLOOR:
        return []

    improving = is_improvement(category, rating.momentum)
    lines = [
        _INDENT + f"{'▲' if improving else '▼'}{abs(rating.momentum):.0%}",
        _INDENT + _duration_phrase(rating.since, moment, improving),
    ]
    reason = _driver_reason(rating)
    if reason is not None:
        lines.append(_INDENT + f"原因：{reason}。")
    return lines


def _duration_phrase(since: datetime, moment: datetime, improving: bool) -> str:
    """Return how long the movement has been running.

    The length comes from when the movement began, which the tracker recorded,
    and not from anything the renderer can see. A movement that began today
    reads as one day rather than as none.
    """
    days = max(1, (moment - since).days)
    return f"近{days}天{'累计改善' if improving else '持续走弱'}"


def _driver_reason(rating: CategoryRating) -> str | None:
    """Return what moved most while the movement accumulated, or None."""
    if rating.driver is None or rating.driver_from is None or rating.driver_to is None:
        return None
    rising = rating.driver_to > rating.driver_from
    return driver_phrase(rating.driver, rising)


def _change_note(rating: CategoryRating) -> str:
    """Return the note describing when a grade last changed and which way."""
    moment = f"{rating.changed_at.month}月{rating.changed_at.day}日"
    if rating.previous_grade is None:
        return f"（{moment} 首次评级）"
    if rating.grade > rating.previous_grade:
        return f"（{moment} 升级）"
    return f"（{moment} 降级）"


def _commentary_lines(result: AnalysisResult, category: Category) -> list[str]:
    """Return what a category says, in the reader's language.

    A category whose measurements read better as a sentence is written as one.
    The measurements themselves stay in the evidence, where they support the
    conclusion rather than being the thing the reader is asked to interpret.
    """
    sentence = sentence_for(result, category)
    if sentence is not None:
        return _pack([sentence], separator="", trailing="")

    phrases = [
        _measurement_phrase(point)
        for point in measurements_of(result, category)
        if point.value is not None
    ]
    if not phrases:
        return [_INDENT + "尚未取得该类别所需的测量。"]
    return _pack(phrases, separator="、", trailing="。")


def _measurement_phrase(point: MarketDataPoint) -> str:
    """Return one measurement written the way it is read."""
    return f"{metric_name(point.metric)} {_format_value(point)}"


def _not_assessed_lines(result: AnalysisResult) -> list[str]:
    """Return the block naming everything that was not looked at.

    Nothing here is a proportion. A reader is told what was not examined by
    name, which is a fact they can act on, rather than by a fraction, which is
    bookkeeping about the model.
    """
    items = _not_assessed_items(result)
    if not items:
        return []
    return [NOT_ASSESSED_PREFIX, *_pack(items, separator="、", trailing="")]


def _not_assessed_items(result: AnalysisResult) -> list[str]:
    """Return the named things this run did not assess, in a stable order.

    HPO and Catalyst are never listed here. Both write a block of their own when
    they have no judgement — one says what it was not able to judge, the other
    says there was no catalyst — and naming them here as well would be reporting
    the same absence twice.
    """
    assessed = _assessed_categories(result)
    unassessed_categories = [
        category
        for category in CATEGORY_ORDER
        if category not in assessed and category not in _self_reporting(result)
    ]

    items: list[str] = [category_label(category) for category in unassessed_categories]

    for category in CATEGORY_ORDER:
        category_score = assessed.get(category)
        if category_score is not None and not category_score.coverage.is_complete:
            items.extend(UNASSESSED_ITEMS.get(category, ()))

    snapshot = result.market_data
    if snapshot is not None:
        items.extend(
            metric_name(point.metric)
            for point in snapshot.missing_points
            if point.metric.primary_category not in unassessed_categories
        )

    return list(dict.fromkeys(items))


def _self_reporting(result: AnalysisResult) -> frozenset[Category]:
    """Return the categories that write their own absence in a block.

    Catalyst always does: an empty calendar is reported as no evaluable catalyst
    where the category belongs. HPO does whenever the run reached a judgement,
    which is every run the analyzer produced.
    """
    categories = {Category.CATALYST}
    if result.opportunity is not None:
        categories.add(Category.HPO)
    return frozenset(categories)


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
    if point.metric in DAY_METRICS:
        return f"{point.value:g} 天"
    if point.metric in PERCENT_METRICS:
        if point.metric in SIGNED_METRICS:
            return f"{point.value:+.1%}"
        return f"{point.value:.1%}"
    for scale, suffix in _COUNT_SCALES:
        if abs(point.value) >= scale:
            return f"{point.value / scale:.1f}{suffix}"
    return f"{point.value:.2f}"
