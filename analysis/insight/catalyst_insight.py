"""Which events are worth a reader's attention, and which are not.

The event list says what is on the calendar. This says which of it matters: an
event is chosen by how much of the investment case it could change, and only
then by when it falls. Distance is not importance, which is why nothing here
picks the nearest event and calls it the most important.

Priority is a property of the kind of event, from one table, and it is an
editorial ordering rather than a measurement. A reader can disagree with it and
can see exactly what was decided.

Nothing here says an event will go well or badly. It says which one is worth
watching and why that kind of event is worth watching.
"""

from __future__ import annotations

from analysis.insight.context import InsightContext
from analysis.labels import catalyst_kind_label, catalyst_kind_reason, catalyst_when
from models.catalyst_event import (
    CatalystEvent,
    CatalystEventPriority,
    CatalystEventScope,
)
from models.insight import InsightLine

# How far ahead an event is still worth writing an insight about.
_WINDOW_DAYS = 90
_DENSE_EVENTS = 3


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return which events matter most, in reading order."""
    upcoming = _upcoming(context)
    if not upcoming:
        return ()

    primary = _first(upcoming, CatalystEventPriority.PRIMARY, context)
    secondary = _first(upcoming, CatalystEventPriority.SECONDARY, context)
    macro = _first(upcoming, CatalystEventPriority.SECONDARY, context, macro_only=True)

    lines: list[InsightLine] = []
    if primary is not None:
        lines.append(_leading(upcoming, primary, context))
    if secondary is not None:
        lines.append(_line("其次是：", secondary, context))
    if macro is not None and macro is not secondary:
        lines.append(_line("宏观方面关注：", macro, context))
    return tuple(lines)


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
        and event.days_from(context.moment) <= _WINDOW_DAYS
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


def _leading(
    events: list[CatalystEvent], event: CatalystEvent, context: InsightContext
) -> InsightLine:
    """Return the line naming the event most worth watching."""
    opening = "未来一段时间事件较为密集，" if len(events) >= _DENSE_EVENTS else ""
    return InsightLine(
        f"{opening}当前最值得关注的是：{_describe(event, context)}。",
        (context.event_reference(event),),
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
