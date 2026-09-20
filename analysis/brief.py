"""The morning brief: one message over the whole watch universe.

The daily report describes one asset, and that is the right shape for a message
that arrives because something changed: one asset changed, and the reader is told
about that asset. It is the wrong shape for a report that arrives at an hour the
reader chose, because the question a morning brief answers is not "what does AIS
know about this asset" but "what should I look at first today". Answering that by
sending seven messages answers neither: the reader gets a message stream instead of
a brief, and the conclusion that mattered is somewhere in the middle of it.

**Analysis coverage and notification projection are two different sets.**
Everything in the watch universe is analysed, because AIS cannot know which asset
matters without looking at all of them. Only a few are written into the message.
That those two numbers used to be the same number — one message per asset — was a
consequence of the report model describing one asset, and it is deliberately
undone here: the universe has to be able to grow without the message growing,
which is the only way a brief survives a watchlist of thirty symbols.

**What earns a line is a named reason, not a score.** An asset is in the brief
because of the first of these that applies to it, and the reasons compete in slots:

=================  =================  ==============================================
Slot               Reads as           Applies when
=================  =================  ==============================================
held, and moved    held and moved     it is in the portfolio, and a category grade or
                                      its measurement moved
held               held               it is in the portfolio
moved              moved              a category grade or its measurement moved
standing           risk, or nothing   a risk condition does not hold, or an
                                      opportunity was judged — see below
seen               nothing            it was analysed and nothing above is true of it
=================  =================  ==============================================

The slots are an **editorial ordering, stated once, in one table**, in the same sense
as the attention an event kind is worth in :mod:`models.catalyst_event`: a reader can
disagree with it and can see exactly what was decided. It is not a measurement, a
probability or a prediction, and nothing derived from it may be presented as any of
those.

**Why risk and opportunity share a slot.** They answer one question — where does this
asset stand — and separating them made the brief worse in a way that only showed on
real data. On a run of the watched universe the risk condition does not hold for six
assets of seven, so ranking that above a judged opportunity filled the message with
the same warning three times and left the asset whose judgement read best among the
ones that were not written out. A brief that lists the most common thing about an
asset before the most important thing about the universe has not chosen. Risk is
still managed before return — that is a Constitution rule, and it governs the
decision, which the evaluators make — and it does not order the lines of a brief.

Within a slot, the number of opportunity conditions that hold decides, because that is
a judgement AIS has already reached and already shows the reader. **Nothing here
computes a score** — a weighted combination of these would be a new scoring method, and
AIS already has the judgements it needs to order them.

**A tag is stated only where a judgement supports it.** An asset whose risk condition
does not hold says so on its line. An asset that is in the brief because its standing
is the strongest carries no tag: "opportunity" would be a claim its own judgement does
not make — the sentence beside it may read that the opportunity is ordinary and not a
priority — and AIS does not put a word on a line that its judgement does not support.

What the brief says about the market rather than about one asset is the events that
bear on every asset: a central bank meets on the same date for every symbol, so one
meeting arrives in every calendar. Those are reported once, at the top, deduplicated
by kind and date. **A market *change* is not reported, because AIS cannot read one
yet**: the evidence for it is Phase C, and the closest thing available — a
twelve-month index move carried per asset — is not a statement about today.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import catalyst_days
from analysis.insight.catalyst_insight import focus_events
from analysis.insight.context import context_for
from analysis.insight.market_insight import environment_line
from analysis.projection import is_a_change
from models.catalyst_event import CatalystEvent, CatalystEventKind, CatalystEventScope
from models.category import Category
from models.insight import Insight
from models.opportunity_assessment import OpportunityCondition
from models.watch_universe import WatchSet, WatchUniverse

# How many assets the brief may write into the message. Three: a reader who is
# given a list has been given a feed again, and a brief that names the top of the
# day and nothing else is the shape this module exists to produce.
MAX_FOCUS = 3

# How many events that bear on every asset the top of the brief may carry.
MAX_EXTERNAL_EVENTS = 2

# What a tie is broken by when no event is ahead. It is a distance no event can
# have, so an asset with nothing on its calendar sorts behind one that has.
_NO_EVENT_DAYS = 3650


class BriefReason(StrEnum):
    """Why an asset earned a line in the brief.

    The members are the reasons an asset can be written out, and which slot each of
    them competes in is :data:`BRIEF_REASON_SLOTS` rather than the order they are
    written here.
    """

    PORTFOLIO_CHANGE = "portfolio-change"
    PORTFOLIO = "portfolio"
    MOVED = "moved"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    WATCHED = "watched"


# The slots the reasons compete in, highest first. Two reasons may share a slot, and
# that is a statement rather than an oversight: risk and opportunity answer the same
# question about an asset, and what separates two assets inside that slot is how many
# opportunity conditions hold rather than which of the two reasons applied.
#
# This is the whole of the ordering policy. Changing what the brief leads with means
# changing this table and nothing else.
BRIEF_REASON_SLOTS: tuple[tuple[BriefReason, ...], ...] = (
    (BriefReason.PORTFOLIO_CHANGE,),
    (BriefReason.PORTFOLIO,),
    (BriefReason.MOVED,),
    (BriefReason.RISK, BriefReason.OPPORTUNITY),
    (BriefReason.WATCHED,),
)

# How each reason is written beside the asset it earned a line for. Two of them carry
# no tag: an asset whose risk condition does not hold is flagged, and an asset that is
# here because its standing is the strongest is not, because "opportunity" would be a
# claim its own judgement does not make. A tag that says nothing is noise on a line
# that has one job.
BRIEF_REASON_LABELS: dict[BriefReason, str] = {
    BriefReason.PORTFOLIO_CHANGE: "持仓变化",
    BriefReason.PORTFOLIO: "持仓",
    BriefReason.MOVED: "变化",
    BriefReason.RISK: "风险",
    BriefReason.OPPORTUNITY: "",
    BriefReason.WATCHED: "",
}


@dataclass(frozen=True)
class BriefEntry:
    """One asset that earned a line, and why.

    Attributes:
        result: The analysis the line is written from. It is the same result the
            expanded report is rendered from, so the brief and the report cannot
            describe one run two ways.
        reason: Why the asset is in the brief. It is recorded rather than left
            implicit so that the line can state it, and so that a reader can tell
            why one asset was shown and another was not.
    """

    result: AnalysisResult
    reason: BriefReason

    @property
    def ticker(self) -> str:
        """Return the symbol the entry is about."""
        return self.result.asset.ticker


@dataclass(frozen=True)
class BriefGroup:
    """Assets that reached the same conclusion.

    A group is what stops the report saying the same thing three times: the assets in
    it are written out under one statement of what AIS concluded about them, instead
    of each carrying a copy of that statement.

    Attributes:
        entries: The assets in the group, in the order the brief already held them.
    """

    entries: tuple[BriefEntry, ...]

    @property
    def is_shared(self) -> bool:
        """Return whether more than one asset reached this conclusion."""
        return len(self.entries) > 1

    @property
    def concluded_grade(self) -> int:
        """Return the count of opportunity conditions holding for this group.

        Zero means nothing could be judged about any member, which is a conclusion
        too, and one the report states once rather than once per asset.
        """
        return _opportunity_grade(self.entries[0].result)


@dataclass(frozen=True)
class DailyBrief:
    """One morning's brief: what to look at first, and what it was read from.

    Attributes:
        moment: Moment the brief was built, in the reader's offset. It is the
            moment the report describes and the moment its clock line states, so
            the two cannot disagree.
        entries: The assets that earned a line, most worth the reader's attention
            first. At most :data:`MAX_FOCUS` of them.
        analysed: Every result the brief was built from, in the order the universe
            holds them. The entries are a subset of these, and the rest are the
            ones that were looked at and did not earn a line. It is coverage
            rather than projection: the brief states how much it looked at, and
            the reader is never left to assume that a short message means a short
            look.
        external_events: The events that bear on every asset, most important
            first. A macro event is not one asset's story, so it is stated once
            here rather than repeated in every entry.
        without_data: Symbols that could not be analysed at all. A run that failed
            is named rather than absent: a reader who is not told cannot tell a
            quiet asset from one AIS never managed to look at.
        environment: What the market is doing, as one sentence, or None when no
            environment measurement was retrieved. It is stored as an
            interpretation rather than as the measurements, because composing a
            sentence is analysis and a renderer only ever shows one. Every asset in
            the brief was judged in this same environment, so it belongs to the
            brief rather than to an entry.
    """

    moment: datetime
    entries: tuple[BriefEntry, ...] = ()
    analysed: tuple[AnalysisResult, ...] = ()
    external_events: tuple[CatalystEvent, ...] = ()
    without_data: tuple[str, ...] = ()
    environment: Insight | None = None

    @property
    def day(self) -> date:
        """Return the local day the brief belongs to."""
        return self.moment.date()

    @property
    def tickers(self) -> tuple[str, ...]:
        """Return every symbol that was analysed."""
        return tuple(result.asset.ticker for result in self.analysed)

    @property
    def held_back(self) -> tuple[str, ...]:
        """Return the symbols that were analysed and did not earn a line."""
        shown = {entry.ticker for entry in self.entries}
        return tuple(ticker for ticker in self.tickers if ticker not in shown)

    @property
    def groups(self) -> tuple[BriefGroup, ...]:
        """Return the entries grouped by the conclusion they reached.

        A conclusion several assets share is one thing the report has to say, so it is
        written once and the assets it applies to are named under it. Grouping never
        reorders the brief: a group sits where its most important member sat, and its
        members keep the order they were already in. What changes is that the same
        sentence is not repeated for every asset that happens to have reached it.

        Two assets reached the same conclusion when their opportunity judgements hold
        the same number of conditions. That count is what the sentence is written
        from, so equal counts are equal words, and grouping by the count is the same
        decision as grouping by the sentence without the report having to hold a
        sentence to compare.
        """
        grouped: dict[int, list[BriefEntry]] = {}
        for entry in self.entries:
            grouped.setdefault(_opportunity_grade(entry.result), []).append(entry)
        return tuple(BriefGroup(entries=tuple(entries)) for entries in grouped.values())


def build_daily_brief(
    results: Sequence[AnalysisResult],
    *,
    moment: datetime,
    universe: WatchUniverse | None = None,
    without_data: Sequence[str] = (),
    limit: int = MAX_FOCUS,
    external_limit: int = MAX_EXTERNAL_EVENTS,
) -> DailyBrief:
    """Return the brief for a set of analysis results.

    Args:
        results: Every result produced for this brief, in the order the universe
            holds them. An asset that could not be analysed is not here; it is
            named in ``without_data`` instead.
        moment: Moment the brief is built, carrying the reader's offset.
        universe: The watch universe the results came from. It is consulted for
            membership and for nothing else, and without it no asset is held.
        without_data: Symbols that could not be analysed.
        limit: How many assets may earn a line.
        external_limit: How many shared events the top of the brief may carry.

    Returns:
        The brief, holding the assets that earned a line and the coverage it was
        selected from.
    """
    entries = [
        BriefEntry(
            result=result,
            reason=_reason_for(result, held=_is_held(result, universe)),
        )
        for result in results
    ]
    ordered = [
        entry
        for _, entry in sorted(
            enumerate(entries), key=lambda pair: _order_key(pair[1], pair[0])
        )
    ]
    return DailyBrief(
        moment=moment,
        entries=tuple(ordered[:limit]),
        analysed=tuple(results),
        external_events=_external_events(results, external_limit),
        without_data=tuple(without_data),
        environment=_environment(results),
    )


def _environment(results: Sequence[AnalysisResult]) -> Insight | None:
    """Return what the market is doing, as one sentence, or None.

    Every asset in a pass is judged in the same environment, so the brief states it
    once for all of them rather than once per entry. It is taken from the first result
    that carries one: the results share the environment, and a result analysed without
    one has nothing to say about it.
    """
    for result in results:
        line = environment_line(context_for(result, Category.MARKET))
        if line is not None:
            return Insight(category=Category.MARKET, lines=(line,))
    return None


def _reason_for(result: AnalysisResult, *, held: bool) -> BriefReason:
    """Return the first reason in the table that applies to one result.

    Args:
        result: Analysis result to classify.
        held: Whether the asset is in the portfolio, which the universe decides.

    Returns:
        The reason the asset is in the brief.
    """
    if held:
        return BriefReason.PORTFOLIO_CHANGE if _moved(result) else BriefReason.PORTFOLIO
    if _moved(result):
        return BriefReason.MOVED
    if _risk_reads_badly(result):
        return BriefReason.RISK
    if _has_an_opportunity(result):
        return BriefReason.OPPORTUNITY
    return BriefReason.WATCHED


def _order_key(entry: BriefEntry, index: int) -> tuple[int, int, int, int]:
    """Return what one entry is ordered by, most significant part first.

    The slot its reason competes in, then three judgements that already exist, and
    then the order the universe holds. The last part is what makes the brief stable:
    two assets that nothing distinguishes are not shuffled between runs, so the same
    brief is written the same way twice.
    """
    return (
        _slot_of(entry.reason),
        -_opportunity_grade(entry.result),
        _nearest_event_days(entry.result),
        index,
    )


def _slot_of(reason: BriefReason) -> int:
    """Return the slot a reason competes in, lowest being the most worth attention."""
    for index, slot in enumerate(BRIEF_REASON_SLOTS):
        if reason in slot:
            return index
    raise ValueError(f"{reason} competes in no slot, which cannot happen")


def _is_held(result: AnalysisResult, universe: WatchUniverse | None) -> bool:
    """Return whether the asset is one AIS holds."""
    if universe is None:
        return False
    return WatchSet.PORTFOLIO in universe.sets_of(result.asset.ticker)


def _moved(result: AnalysisResult) -> bool:
    """Return whether anything about the asset moved.

    Whether a rating counts as a movement is decided once, in
    :func:`analysis.projection.is_a_change`, which is the same answer the per-asset
    report writes its change block from.
    """
    return any(is_a_change(rating) for rating in result.ratings)


def _risk_reads_badly(result: AnalysisResult) -> bool:
    """Return whether the risk condition was judged and does not hold.

    It reads the judgement rather than the measurements: the condition is where
    AIS has already said whether the risk of this asset is acceptable, and reading
    the numbers again here would be a second opinion about the same question.
    """
    opportunity = result.opportunity
    if opportunity is None:
        return False
    return any(
        condition.condition is OpportunityCondition.RISK
        and condition.satisfied is False
        for condition in opportunity.conditions
    )


def _has_an_opportunity(result: AnalysisResult) -> bool:
    """Return whether any opportunity condition could be answered at all."""
    opportunity = result.opportunity
    return opportunity is not None and opportunity.grade is not None


def _opportunity_grade(result: AnalysisResult) -> int:
    """Return how many opportunity conditions hold, or zero when none could be."""
    opportunity = result.opportunity
    if opportunity is None or opportunity.grade is None:
        return 0
    return opportunity.grade


def _nearest_event_days(result: AnalysisResult) -> int:
    """Return how far away the nearest event that could change a view is."""
    days = catalyst_days(result)
    return _NO_EVENT_DAYS if days is None else days


def _external_events(
    results: Sequence[AnalysisResult], limit: int
) -> tuple[CatalystEvent, ...]:
    """Return the events that bear on every asset, most important first.

    They are read through the same ordering the per-asset report uses for the
    events it shows, so the brief and the report cannot disagree about which event
    matters most.

    A macro event arrives in every asset's calendar, because it is not one asset's
    event: the central bank meets on the same date whichever symbol is asked about.
    Reporting it once per asset would turn one fact into seven lines, so the copies
    are collapsed into one by kind and date.
    """
    found: dict[tuple[CatalystEventKind, date], CatalystEvent] = {}
    for result in results:
        for event in focus_events(context_for(result, Category.CATALYST)):
            if event.scope is not CatalystEventScope.MACRO:
                continue
            found.setdefault((event.kind, event.occurs_on), event)
    return tuple(found.values())[:limit]


def own_event(result: AnalysisResult) -> CatalystEvent | None:
    """Return the event worth watching for one asset, or None when it has none.

    The macro events are not returned: they belong to the whole universe and are
    stated once at the top of the brief, so repeating one beside an asset would
    report the same meeting as though it were that asset's own.
    """
    for event in focus_events(context_for(result, Category.CATALYST)):
        if event.scope is not CatalystEventScope.MACRO:
            return event
    return None
