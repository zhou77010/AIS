"""AIS mobile report renderer.

Renders one analysis result as the mobile projection of the Recommendation
Report: plain text, written for an investor, and bounded so that it is actually
read.

**This is a projection, not a report.** Everything the model holds is available
to it, and this renderer chooses what a reader sees on a phone. Nothing here
judges, interprets or summarises — the insight layer already wrote what the
evidence means, and this shows the part of it that earns its place.

Three budgets govern the output, and all three are asserted by tests rather than
described here:

* **32 lines at most.** A report nobody finishes is worth less than a short one
  that is read.
* **42 columns at most.** Chinese characters occupy two, so the budget is in
  display columns.
* **The first 20 lines close the question.** Opening the report must answer why
  today matters: which stock, whether it is worth attention, what to do, what
  changed, and what to watch. A reader who has to hunt through eight category
  blocks for that has been given a data dump, not a report.

What is deliberately absent, and where it went:

* raw measurement lists — the insight sentences say what the numbers mean, and
  the values live in the evidence and in ``generate_report``;
* the full event calendar — one or two events are shown, the rest are in
  ``generate_report``;
* the model's internal gap names — a reader is told which categories were not
  judged, and the dimension-level detail is in ``generate_report``;
* provenance that never changes — the source is named in one tail line, and the
  line exists so that a *degraded* run is visible rather than invisible.

The order the categories appear in is defined once, for every renderer, in
:mod:`models.category`. This renderer does not reorder them.

What it does *not* decide for itself is how a line is measured, how a sentence is
broken, or how small a movement is too small to mention. Those decisions are shared
with every other phone projection and live in :mod:`analysis.projection`, so that
the brief and this report cannot disagree about the same reading from the same run.
"""

from __future__ import annotations

from datetime import datetime

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import grade_for_category, stars
from analysis.insight.builder import insight_for
from analysis.insight.catalyst_insight import focus_events
from analysis.insight.context import context_for
from analysis.labels import (
    DISCLAIMER,
    NO_GRADE,
    catalyst_kind_label,
    catalyst_when,
    category_label,
    decision_label,
    driver_phrase,
    is_improvement,
    opportunity_condition_label,
)
from analysis.plain_language import opportunity_sentence
from analysis.projection import (
    INDENT,
    MOMENTUM_FLOOR,
    PROJECTION_SENTENCE_WIDTH,
    SECTION_SEPARATOR,
    display_width,
    is_a_change,
    named_block,
    wrap,
)
from analysis.report import (
    LIVE_DATA_LABEL,
    NO_DATA_LABEL,
    PLACEHOLDER_DATA_LABEL,
    data_quality_label,
)
from models.catalyst_event import CatalystEvent
from models.category import CATEGORY_ORDER, Category
from models.category_rating import CategoryRating

NOT_ASSESSED_PREFIX = "尚未评估"

# The two budgets this projection is held to. They are asserted by
# tests/test_report_projection.py, and the width it shares with the brief is
# asserted there too.
LINE_BUDGET = 32
FIRST_SCREEN_LINES = 20

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_TIMEZONE_NOTE = "北京时间"

# How many entries each headline block may show.
MAX_CHANGES = 3
MAX_FOCUS_EVENTS = 2

# What is said when the calendar holds nothing that could change a view. It is
# an answer to the question rather than a gap in it, so it is written as one.
_NO_CATALYST_SENTENCE = "近期暂无明确催化。"

# The closing line carries two constant facts and is written compactly: a
# separator with spaces around it costs four columns, which is what the line
# needs to stay inside the width.
_UNCHANGED_PROVENANCE = {
    LIVE_DATA_LABEL: "实时",
    PLACEHOLDER_DATA_LABEL: "占位数据",
    NO_DATA_LABEL: "无行情数据",
}


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
        *_headline(result, generated_at),
        SECTION_SEPARATOR,
    ]
    for category in CATEGORY_ORDER:
        lines.extend(_category_block(result, category))
    lines.extend(_tail(result))
    return "\n".join(lines)


def _headline(result: AnalysisResult, moment: datetime) -> list[str]:
    """Return the block that has to answer the question on its own.

    Five things, in the order a reader asks them: whether this is worth
    attention, what to do about it, what changed today, and what to watch. The
    whole block is meant to fit the first screen, which is why the changes and
    the events are here rather than inside the categories they belong to.
    """
    return [
        *_opportunity_lines(result),
        _decision_line(result),
        *_change_lines(result, moment),
        *_focus_lines(result, moment),
    ]


def _opportunity_lines(result: AnalysisResult) -> list[str]:
    """Return what today amounts to, and why, in the fewest lines that hold it."""
    opportunity = result.opportunity
    if opportunity is None:
        return []
    heading = (
        f"{category_label(Category.HPO)}  "
        f"{stars(opportunity.grade) if opportunity.grade else NO_GRADE}"
    )
    lines = [heading, *wrap(opportunity_sentence(opportunity))]
    unknown = list(opportunity.unknown)
    if unknown:
        # A condition nothing could be said about is named rather than left out:
        # a reader who is not told would read the sentence as though every
        # condition had been checked and passed.
        phrases = [
            opportunity_condition_label(entry.condition, False) for entry in unknown
        ]
        lines.extend(named_block("未评估  ", phrases))
    return lines


def _decision_line(result: AnalysisResult) -> str:
    """Return the line stating what AIS concluded."""
    state = decision_label(result.recommendation.decision_state)
    confidence = result.recommendation.confidence
    return f"结论  {state}          信心  {confidence:.0%}"


def _change_lines(result: AnalysisResult, moment: datetime) -> list[str]:
    """Return what moved since the last run, largest movement first.

    Only real changes appear. A category being rated for the first time is the
    state of the tracker rather than a change in the asset, and writing one line
    per category for it would fill the report with the system's own bookkeeping.

    The block is left out entirely when nothing moved. The report says what
    changed and says nothing when nothing did.
    """
    entries = _changes(result, moment)[:MAX_CHANGES]
    if not entries:
        return []
    lines = [f"变化  {entries[0]}"]
    lines.extend(f"{INDENT * 2}{entry}" for entry in entries[1:])
    return lines


def _changes(result: AnalysisResult, moment: datetime) -> list[str]:
    """Return one phrase per category that moved, most significant first.

    Whether a rating moved at all is decided by :func:`analysis.projection.
    is_a_change`, so that this block and the brief's summary of the universe are
    counting the same movements.
    """
    moves: list[tuple[float, str]] = []
    for rating in result.ratings:
        if not is_a_change(rating):
            continue
        phrase = _change_phrase(rating, moment)
        if phrase is None:
            continue
        weight = 1.0 if rating.changed else abs(rating.momentum)
        moves.append((weight, phrase))
    moves.sort(key=lambda move: -move[0])
    return [phrase for _, phrase in moves]


def _change_phrase(rating: CategoryRating, moment: datetime) -> str | None:
    """Return how one category moved, or None when it did not.

    Three things and no more: how much, over how long, and what moved. A bare
    arrow leaves the reader to guess the other two, and a movement whose cause is
    not named is a number they cannot act on.
    """
    name = category_label(rating.category)
    if rating.changed:
        if rating.previous_grade is None:
            return None
        return f"{name} {'升级' if rating.grade > rating.previous_grade else '降级'}"
    if abs(rating.momentum) < MOMENTUM_FLOOR:
        return None
    improving = is_improvement(rating.category, rating.momentum)
    days = max(1, (moment - rating.since).days)
    phrase = f"{name} {'▲' if improving else '▼'}{abs(rating.momentum):.0%} {days}天"
    driver = _driver_phrase(rating)
    return phrase if driver is None else f"{phrase} · {driver}"


def _driver_phrase(rating: CategoryRating) -> str | None:
    """Return what moved most while the movement accumulated, or None."""
    if rating.driver is None or rating.driver_from is None or rating.driver_to is None:
        return None
    return driver_phrase(rating.driver, rating.driver_to > rating.driver_from)


def _focus_lines(result: AnalysisResult, moment: datetime) -> list[str]:
    """Return the one or two events most worth a reader's attention.

    Chosen by how much of the investment case the kind of event could change,
    and only then by when it falls. The rest of the calendar is in the expanded
    report: a reader needs the event that matters, not an agenda.
    """
    events = focus_events(context_for(result, Category.CATALYST), MAX_FOCUS_EVENTS)
    if not events:
        return []
    lines = [f"关注  {_focus_phrase(events[0], moment)}"]
    lines.extend(f"{INDENT * 2}{_focus_phrase(event, moment)}" for event in events[1:])
    return lines


def _focus_phrase(event: CatalystEvent, moment: datetime) -> str:
    """Return one event as a short phrase: when it is and what it is."""
    name = catalyst_kind_label(event.kind, event.description)
    return f"{catalyst_when(event, moment)} {name}"


def _category_block(result: AnalysisResult, category: Category) -> list[str]:
    """Return the two lines a category gets, or none when it has nothing to say.

    A heading and one sentence: the grade, and the most important thing the
    evidence supports. The remaining sentences the insight layer wrote are still
    in the model and are shown in the expanded report — a phone gets the
    headline, which is what a category has to earn its place with.
    """
    if category is Category.HPO:
        return []
    assessed = category in _assessed_categories(result)
    grade = grade_for_category(result, category) if assessed else None
    heading = f"{category_label(category)}  {stars(grade) if grade else NO_GRADE}"
    sentence = _category_sentence(result, category)
    if sentence is None:
        # An empty calendar is an answer, and a category nothing was judged for
        # is a gap the tail reports. Only the first of those is written here.
        if category is Category.CATALYST:
            return [heading, *wrap(_NO_CATALYST_SENTENCE)]
        return []
    return [heading, *wrap(sentence)]


def _category_sentence(result: AnalysisResult, category: Category) -> str | None:
    """Return the one sentence a category is projected with."""
    insight = insight_for(result, category)
    if insight is None or insight.is_empty:
        return None
    return insight.lines[0].text


def _assessed_categories(result: AnalysisResult) -> set[Category]:
    """Return the categories a judgement was actually reached for.

    A category the assembler produced from no rule results carries no evidence
    references. That is an absent judgement rather than a score, and showing its
    zero would report the worst possible value for a dimension nothing looked at.
    """
    return {
        category_score.category
        for category_score in result.assessment.category_scores
        if category_score.evidence_references
    }


def _tail(result: AnalysisResult) -> list[str]:
    """Return the closing lines: what was not judged, and where the data came from.

    Only whole categories are named. A reader is owed the fact that an entire
    question went unasked; the model's own dimension and metric names are not
    their business, and they are in the expanded report where they can be looked
    up.

    The provenance line says which source answered and whether the run was live.
    It is constant on a good day, and the one day it is not is the day it needs
    to be there.
    """
    lines: list[str] = [SECTION_SEPARATOR]
    missing = [
        category_label(category)
        for category in CATEGORY_ORDER
        if category is not Category.HPO
        and category is not Category.CATALYST
        and category not in _assessed_categories(result)
    ]
    if missing:
        lines.extend(named_block(f"{NOT_ASSESSED_PREFIX}  ", missing))
    lines.append(_provenance_line(result))
    return lines


def _provenance_line(result: AnalysisResult) -> str:
    """Return one line naming the source and whether the data was live."""
    quality = _UNCHANGED_PROVENANCE.get(data_quality_label(result), "行情状态未知")
    snapshot = result.market_data
    if snapshot is None:
        return f"{quality}·{DISCLAIMER}"
    return f"来源 {snapshot.source}·{quality}·{DISCLAIMER}"


def fits_one_line(text: str) -> bool:
    """Return whether a sentence is shown as a single line of the report.

    The insight layer's tests use this to hold the first sentence of every
    category to a length the projection can show in one line. A headline that
    wraps is still readable; a category block that wraps costs the report a line
    it has not budgeted for, and the budget is what keeps the report short enough
    to finish.
    """
    return display_width(text) <= PROJECTION_SENTENCE_WIDTH
