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
from analysis.brief import (
    BRIEF_REASON_LABELS,
    BriefEntry,
    BriefGroup,
    BriefReason,
    DailyBrief,
    own_event,
)
from analysis.category_grade import stars
from analysis.insight.builder import insight_for
from analysis.labels import (
    DISCLAIMER,
    NO_GRADE,
    catalyst_kind_label,
    catalyst_when,
    decision_label,
    opportunity_headline,
)
from analysis.plain_language import opportunity_sentence
from analysis.projection import (
    SECTION_SEPARATOR,
    named_block,
    wrap,
    wrap_at_clauses,
)
from analysis.report import (
    LIVE_DATA_LABEL,
    NO_DATA_LABEL,
    PLACEHOLDER_DATA_LABEL,
    data_quality_label,
)
from models.catalyst_event import CatalystEvent
from models.category import Category

# The budget this projection is held to by tests/test_daily_brief.py. A brief that
# has to be scrolled is a brief nobody finishes, and the cap is what stops a
# growing watch universe from growing the message.
BRIEF_LINE_BUDGET = 24

_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M"
_TIMEZONE_NOTE = "北京时间"
_TITLE = "AIS 晨报"
_ENVIRONMENT_LABEL = "市场环境  "
_LEADER_LINK = "对今日优先的 {ticker} 而言，"
_RANK_LABEL = "今日优先  "
_MOST_CONDITIONS = "机会条件最多"
_HAS_MOVED = "今日有变化"

# The reasons that mean something about this asset moved, rather than where it stands.
# A leader whose reason is one of these leads because it moved, which is what the brief
# sorts on first.
_MOVED_REASONS = frozenset({BriefReason.MOVED, BriefReason.PORTFOLIO_CHANGE})

_EXTERNAL_LABEL = "外部事件  "
_NO_EXTERNAL_EVENT = "外部事件  暂无"
_SHARED_LABEL = "共同结论"
_INDENT = "  "
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
        [
            _header(brief),
            _coverage(brief),
            *_environment_lines(brief),
            *_external_lines(brief),
        ],
        _body(brief),
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


def _environment_lines(brief: DailyBrief) -> list[str]:
    """Return what the market is doing, and what it means for the asset put first.

    This is the line that makes the brief a pre-market brief rather than a review: it
    is the environment the reader is about to trade into, and every asset below it was
    judged in it. It is absent when no environment measurement was retrieved, which is
    the honest thing to show rather than a claim about a market nobody looked at.

    The second half answers the question the first half raises. A reader told what the
    market is doing, and then given a list in which one asset leads, still does not know
    why that one leads — so the environment is applied to it, in the words that asset's
    own report opens its Market block with. The sentence is read from the insight the
    run already built, so the brief and the report cannot say two things about one
    holding.
    """
    if brief.environment is None or brief.environment.is_empty:
        return []
    lines = wrap_at_clauses(
        brief.environment.lines[0].text, first_prefix=_ENVIRONMENT_LABEL
    )
    lines.extend(_leader_link(brief))
    return lines


def _leader_link(brief: DailyBrief) -> list[str]:
    """Return what the environment means for the first asset, or nothing."""
    if not brief.entries:
        return []
    entry = brief.entries[0]
    insight = insight_for(entry.result, Category.MARKET)
    if insight is None or insight.is_empty:
        return []
    return wrap(f"{_LEADER_LINK.format(ticker=entry.ticker)}{insight.lines[0].text}")


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


def _body(brief: DailyBrief) -> list[str]:
    """Return the assets the brief writes out, with a shared conclusion said once.

    Assets that reached the same conclusion are written under one statement of it, and
    that statement names them: a reader who is told a conclusion applies to several
    assets and not which ones has to work it out from the order, and the order is the
    one thing about a shared conclusion that carries no meaning.

    A brief for a universe that reads alike would otherwise spend its width saying the
    same sentence three times, which costs the reader the lines that could have
    differed and tells them nothing the first one did not.
    """
    lines: list[str] = []
    for group in brief.groups:
        conclusion = _judgement(group.entries[0].result)
        shared = group.is_shared and conclusion is not None
        if shared:
            lines.append(_shared_label(group))
            lines.extend(wrap_at_clauses(conclusion))
        for entry in group.entries:
            lines.extend(_entry_lines(entry, brief, with_judgement=not shared))
    return lines


def _shared_label(group: BriefGroup) -> str:
    """Return the label naming a shared conclusion and the assets it covers.

    The label carries the roster because a conclusion stated once for several assets
    is ambiguous without it: a reader has to work out which assets it applies to from
    the order, and the order between assets that reached the same conclusion is the one
    thing about them that carries no meaning.

    It goes on a line of its own rather than in front of the sentence. The roster is
    long enough that a sentence beside it would be broken in the middle of a phrase,
    and a phrase broken in half is harder to read than a line spent on the roster.
    """
    names = "、".join(entry.ticker for entry in group.entries)
    return f"{_SHARED_LABEL}（{names}）"


def _entry_lines(
    entry: BriefEntry, brief: DailyBrief, *, with_judgement: bool
) -> list[str]:
    """Return the block one asset gets: what it is, why it leads, what to watch.

    Three lines at most, and a fourth for the asset the brief put first. The standing
    is on the heading so that a reader can scan the column of them, the conclusion is
    one sentence, and the event is the one thing about this asset that is still ahead.
    The conclusion is left out when the assets around this one share it: it has already
    been stated for all of them, and saying it again is the repetition this projection
    exists to avoid.
    """
    result = entry.result
    lines = [_entry_heading(entry)]
    if entry is brief.entries[0]:
        rank = _rank_line(brief)
        if rank is not None:
            lines.append(rank)
    judgement = _judgement(result) if with_judgement else None
    if judgement is not None:
        lines.extend(wrap(judgement))
    event = own_event(result)
    if event is not None:
        lines.extend(wrap(f"{_CATALYST_LABEL}{_event_phrase(event, brief)}"))
    return lines


def _rank_line(brief: DailyBrief) -> str | None:
    """Return why the first asset is first, in the fewest words that are true.

    The order is decided by the brief's own rule, and this only puts that decision into
    words a reader can check. It describes what is already on the screen: the asset
    leads either because it moved while the others did not, or because it holds more
    opportunity conditions than the others shown, which is what the stars beside each
    heading count. Where neither is true, nothing is claimed — the assets are alike and
    the order between them means nothing, so saying why would invent a reason.
    """
    if not brief.entries:
        return None
    leader = brief.entries[0]
    if _leads_on_conditions(brief):
        return f"{_RANK_LABEL}{_MOST_CONDITIONS}"
    if leader.reason in _MOVED_REASONS:
        return f"{_RANK_LABEL}{_HAS_MOVED}"
    return None


def _leads_on_conditions(brief: DailyBrief) -> bool:
    """Return whether the leading asset holds more conditions than the rest shown.

    It compares the conclusions the brief already reached rather than recomputing
    anything: a group's conclusion is the count of opportunity conditions that hold,
    and two assets in the same group hold the same number by definition.

    One group is the case this is written for. Where every asset shown holds the same
    number of conditions there is nothing for the leader to hold more of, and a claim
    that it holds the most would be a comparison against a list that does not exist.
    """
    grades = [group.concluded_grade for group in brief.groups]
    if len(grades) < 2 or grades[0] <= 0:
        return False
    return grades[0] > max(grades[1:])


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
