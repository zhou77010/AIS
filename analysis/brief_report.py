"""The morning brief rendered for a phone.

This is the projection of :class:`~analysis.brief.DailyBrief`, and it is the only
thing the reader receives at the hour the brief is owed. Everything else AIS
produced for that hour — one full report per asset, every sentence the insight
layer wrote, every measurement, the whole calendar, the model's own names for what
was not looked at — is rendered by :func:`analysis.report.generate_report` into the
log, where it can be looked up and where it does not interrupt anybody.

**A brief is not a list of notifications.** It answers one question: what should
this reader look at first today? So it leads with how much was looked at and how
much earned a line, states the events that bear on everything, and then gives the
few assets that matter a name, a standing, a conclusion and the one thing to watch
about each. An asset that has nothing to say about it today is named in one line
with the others rather than given a block of its own.

Three budgets govern the output, and all three are asserted rather than described:

* **24 lines at most.** The per-asset report is allowed 32; a brief that is as
  long as the report it summarises has not summarised anything.
* **42 columns at most** — the same width every phone projection uses, held in
  :mod:`analysis.projection` so that this and the per-asset report cannot
  disagree about what fits.
* **The first lines carry the day.** How much was looked at, what bears on
  everything, and which assets matter come before any detail, because a reader who
  stops after three lines has still been told where to look.

What is deliberately absent, and where it went:

* the per-asset report — one is rendered into the log for every asset, and this
  message names the asset instead;
* the opportunity conditions — the per-asset report writes them out; a brief
  states the conclusion they amount to, which is the part that decides what to
  look at;
* measurements, category grades and coverage gaps — all of them are in the log;
* a market state — AIS cannot read one yet. The evidence for it is market-level
  and does not exist, and the closest thing available is a twelve-month index move
  carried per asset, which is not a statement about today.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.analysis_result import AnalysisResult
from analysis.brief import BRIEF_REASON_LABELS, BriefEntry, DailyBrief, own_event
from analysis.category_grade import stars
from analysis.labels import (
    DISCLAIMER,
    NO_GRADE,
    catalyst_kind_label,
    catalyst_when,
    decision_label,
    opportunity_headline,
)
from analysis.plain_language import opportunity_sentence
from analysis.projection import SECTION_SEPARATOR, named_block, wrap
from analysis.report import (
    LIVE_DATA_LABEL,
    NO_DATA_LABEL,
    PLACEHOLDER_DATA_LABEL,
    data_quality_label,
)
from models.catalyst_event import CatalystEvent

# The budget this projection is held to by tests/test_daily_brief.py. A brief that
# has to be scrolled is a brief nobody finishes, and the cap is what stops a
# growing watch universe from growing the message.
BRIEF_LINE_BUDGET = 24

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_TIMEZONE_NOTE = "北京时间"
_TITLE = "AIS 晨报"
_EXTERNAL_LABEL = "外部事件  "
_NO_EXTERNAL_EVENT = "外部事件  暂无"
_CATALYST_LABEL = "关注  "
_WITHOUT_DATA_LABEL = "无实时数据  "
_DEGRADED = "部分标的无实时数据"

# What each state of the data is called when a whole universe is described at once.
_DATA_STATES = {
    LIVE_DATA_LABEL: "实时",
    PLACEHOLDER_DATA_LABEL: "占位数据",
    NO_DATA_LABEL: "无行情数据",
}


def render_daily_brief(brief: DailyBrief) -> str:
    """Render the morning brief as the one message the reader receives.

    Args:
        brief: The brief to render.

    Returns:
        Plain text, ready to be sent through a push channel.
    """
    parts = [
        [_header(brief), _coverage(brief), *_external_lines(brief)],
        [line for entry in brief.entries for line in _entry_lines(entry, brief)],
        _tail(brief),
    ]
    return "\n".join(_joined(parts))


def _joined(parts: Sequence[Sequence[str]]) -> list[str]:
    """Return the parts of a report, separated by a rule and never by a blank one.

    An empty part is dropped rather than written as two rules in a row, which is
    what a reader sees as a mistake.
    """
    lines: list[str] = []
    for part in parts:
        if not part:
            continue
        if lines:
            lines.append(SECTION_SEPARATOR)
        lines.extend(part)
    return lines


def _header(brief: DailyBrief) -> str:
    """Return the line naming the report, the day it is for, and the hour."""
    return f"{_TITLE} · {brief.moment.strftime(_TIMESTAMP_FORMAT)} {_TIMEZONE_NOTE}"


def _coverage(brief: DailyBrief) -> str:
    """Return the line stating how much was looked at and how much earned a line.

    These are the two numbers the brief exists to keep apart. A reader who is told
    only what is shown cannot tell a quiet universe from a narrow one.
    """
    return f"分析 {len(brief.analysed)} 个标的 · 今日优先 {len(brief.entries)} 个"


def _external_lines(brief: DailyBrief) -> list[str]:
    """Return the events that bear on every asset, most important first.

    An empty calendar is written as an answer rather than left out: the events
    that apply to everything are the closest thing this brief has to a statement
    about the market, and a reader who is told nothing about them cannot tell
    whether there are none or whether AIS did not look.
    """
    if not brief.external_events:
        return [_NO_EXTERNAL_EVENT]
    return named_block(
        _EXTERNAL_LABEL,
        [_event_phrase(event, brief) for event in brief.external_events],
    )


def _entry_lines(entry: BriefEntry, brief: DailyBrief) -> list[str]:
    """Return the block one asset gets: what it is, what AIS concluded, what to watch.

    Three lines at most. The standing is on the heading so that a reader can scan
    the column of them, the conclusion is one sentence, and the event is the one
    thing about this asset that is still ahead.
    """
    result = entry.result
    lines = [_entry_heading(entry)]
    judgement = _judgement(result)
    if judgement is not None:
        lines.extend(wrap(judgement))
    event = own_event(result)
    if event is not None:
        lines.extend(wrap(f"{_CATALYST_LABEL}{_event_phrase(event, brief)}"))
    return lines


def _entry_heading(entry: BriefEntry) -> str:
    """Return the line naming one asset and where it stands.

    The reason is written beside the standing when there is one worth stating. Two
    of the reasons carry no words: they say the asset was read at all, which a
    reader assumes of everything in their own brief.
    """
    result = entry.result
    opportunity = result.opportunity
    grade = None if opportunity is None else opportunity.grade
    standing = stars(grade) if grade else NO_GRADE
    decision = decision_label(result.recommendation.decision_state)
    tag = BRIEF_REASON_LABELS.get(entry.reason, "")
    suffix = f" · {tag}" if tag else ""
    return f"{result.asset.ticker}  {standing} {decision}{suffix}"


def _judgement(result: AnalysisResult) -> str | None:
    """Return the one sentence saying what AIS concluded about one asset.

    The headline is used where there is a grade, because the whole opportunity
    sentence is written for a report about one asset: a brief that repeated it
    three times would spend most of its width restating the conditions the reader
    can open the full report for. Where nothing could be judged at all there is no
    headline to lead with, and the sentence stating that is the answer.
    """
    opportunity = result.opportunity
    if opportunity is None:
        return None
    if opportunity.grade is None:
        return opportunity_sentence(opportunity)
    return opportunity_headline(opportunity.grade) + "。"


def _event_phrase(event: CatalystEvent, brief: DailyBrief) -> str:
    """Return one event as a short phrase: when it is and what it is."""
    name = catalyst_kind_label(event.kind, event.description)
    return f"{catalyst_when(event, brief.moment)} {name}"


def _tail(brief: DailyBrief) -> list[str]:
    """Return the closing lines: who was left out, and where the data came from.

    A reader is owed both. The symbols that did not earn a line are named, so that
    a short brief cannot be read as a narrow one; the ones that could not be
    analysed at all are named separately, because an asset AIS failed to look at
    is a different thing from an asset that had nothing to say; and the provenance
    line says which source answered and whether every run was live.
    """
    lines: list[str] = []
    held_back = brief.held_back
    if held_back:
        lines.extend(named_block(f"其余 {len(held_back)} 个：", list(held_back)))
    if brief.without_data:
        lines.extend(named_block("未分析  ", list(brief.without_data)))
    degraded = [
        result.asset.ticker
        for result in brief.analysed
        if data_quality_label(result) != LIVE_DATA_LABEL
    ]
    if degraded:
        lines.extend(named_block(_WITHOUT_DATA_LABEL, degraded))
    lines.append(_provenance(brief))
    return lines


def _provenance(brief: DailyBrief) -> str:
    """Return one line naming the sources and whether the data behind it was live.

    It describes every run the brief was built from and not only the assets it
    shows: a brief that read well because three of its assets were measured, while
    four were not, would be describing a universe it cannot describe.
    """
    states = {data_quality_label(result) for result in brief.analysed}
    sources = sorted(
        {
            result.market_data.source
            for result in brief.analysed
            if result.market_data is not None
        }
    )
    if not states:
        return DISCLAIMER
    if states == {LIVE_DATA_LABEL}:
        state = _DATA_STATES[LIVE_DATA_LABEL]
    elif len(states) > 1:
        state = _DEGRADED
    else:
        state = _DATA_STATES[next(iter(states))]
    if not sources:
        return f"{state}·{DISCLAIMER}"
    return f"来源 {'、'.join(sources)}·{state}·{DISCLAIMER}"
