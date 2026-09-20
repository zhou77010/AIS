"""Which events are worth a reader's attention, and which are not.

The event list says what is on the calendar. This says what the calendar amounts
to and which of it matters: an event is chosen by how much of the investment
case it could change, and only then by when it falls. Distance is not importance,
which is why nothing here picks the nearest event and calls it the most
important.

Priority is a property of the kind of event, from one table, and it is an
editorial ordering rather than a measurement. A reader can disagree with it and
can see exactly what was decided.

Nothing here says an event will go well or badly. It says which one is worth
watching and why that kind of event is worth watching.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from analysis.labels import catalyst_kind_label, catalyst_kind_reason, catalyst_when
from evaluation.reading.windows import (
    CATALYST_WINDOW_DAYS,
    IMMINENT_DAYS,
    NEAR_TERM_DAYS,
)
from models.catalyst_event import (
    CATALYST_PRIORITY_ORDER,
    CatalystEvent,
    CatalystEventPriority,
    CatalystEventScope,
)
from models.insight import InsightLine

# How many events make a calendar worth calling busy. It decides wording and never
# a judgement: the reading is the nearest event and never how many there are.
_DENSE_EVENTS = 3


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the calendar amounts to, then which events matter most.

    The first sentence is the one a phone report shows, so it says what the
    calendar amounts to and names no event. Which event matters is a sentence of
    its own, and leading with it would put the same fact in the report twice —
    once here and once wherever the event itself is shown.
    """
    upcoming = _upcoming(context)
    if not upcoming:
        return ()

    lines: list[InsightLine] = [_timing(upcoming, context)]
    primary = _first(upcoming, CatalystEventPriority.PRIMARY, context)
    secondary = _first(upcoming, CatalystEventPriority.SECONDARY, context)
    macro = _first(upcoming, CatalystEventPriority.SECONDARY, context, macro_only=True)
    if primary is not None:
        lines.append(_line("当前最值得关注的是：", primary, context))
    if secondary is not None:
        lines.append(_line("其次是：", secondary, context))
    if macro is not None and macro is not secondary:
        lines.append(_line("宏观方面关注：", macro, context))
    return tuple(lines)


def focus_events(
    context: InsightContext, limit: int | None = None
) -> tuple[CatalystEvent, ...]:
    """Return the events worth showing a reader, most worth watching first.

    Chosen by how much of the investment case the kind of event could change, and
    only then by when it falls. This is the ordering the insight uses, exposed so
    that the report can show the events without writing a second rule for which
    ones matter.

    Args:
        context: The catalyst evidence, and the moment it is measured from.
        limit: How many events to return, or None for every one of them. The brief
            asks for all of them and then takes the ones that bear on the whole
            universe, so that it orders what it shows by this rule rather than by a
            copy of it.
    """
    upcoming = _upcoming(context)
    ordered: list[CatalystEvent] = []
    for priority in CATALYST_PRIORITY_ORDER:
        ordered.extend(
            sorted(
                (event for event in upcoming if event.priority is priority),
                key=lambda event: (event.days_from(context.moment), event.kind.value),
            )
        )
    return tuple(ordered[:limit])


def _timing(events: list[CatalystEvent], context: InsightContext) -> InsightLine:
    """Return what the calendar amounts to, naming no event."""
    nearest = min(event.days_from(context.moment) for event in events)
    reference = tuple(context.event_reference(event) for event in events)
    if nearest <= IMMINENT_DAYS:
        text = "一周内即有事件落地。"
    elif len(events) >= _DENSE_EVENTS:
        text = "未来一个月催化较密集。"
    elif nearest <= NEAR_TERM_DAYS:
        text = "未来一个月存在可能改变预期的事件。"
    else:
        text = "近期暂无明确催化，等待更远的事件。"
    return InsightLine(text, reference)


def _upcoming(context: InsightContext) -> list[CatalystEvent]:
    """Return the forthcoming events in the window, mechanical ones excluded.

    An event that moves the price without moving a view is written out in the
    event list and is not what a reader should be watching for a change in the
    case, so it is not what this insight is about.
    """
    return [
        event
        for event in context.events
        if event.is_upcoming(context.moment)
        and not event.is_mechanical
        and event.days_from(context.moment) <= CATALYST_WINDOW_DAYS
    ]


def _first(
    events: list[CatalystEvent],
    priority: CatalystEventPriority,
    context: InsightContext,
    *,
    macro_only: bool = False,
) -> CatalystEvent | None:
    """Return the earliest event of one priority, or None when there is none."""
    candidates = [
        event
        for event in events
        if event.priority is priority
        and (not macro_only or event.scope is CatalystEventScope.MACRO)
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda event: (event.days_from(context.moment), event.kind.value),
    )


def _line(prefix: str, event: CatalystEvent, context: InsightContext) -> InsightLine:
    """Return a line naming a further event of interest."""
    return InsightLine(
        f"{prefix}{_describe(event, context)}。",
        (context.event_reference(event),),
    )


def _describe(event: CatalystEvent, context: InsightContext) -> str:
    """Return an event written as the reader will see it, with why it matters."""
    name = catalyst_kind_label(event.kind, event.description)
    when = catalyst_when(event, context.moment)
    return f"{name}（{when.strip()}）— {catalyst_kind_reason(event.kind)}"
