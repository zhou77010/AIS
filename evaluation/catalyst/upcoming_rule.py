"""Catalyst rule: how near is the next event that could change a view?

The Catalyst question is what could change the picture, and when. This rule
answers the second half of it from the event layer: it takes the nearest event
that could change what the market expects, and reports how far away it is.

**How many events there are is not the measurement.** Four events next month and
one event next month are the same reading here, because what a reader needs to
know from a score is whether something is coming and how soon, not how busy the
calendar is. The report writes the calendar out in full; the score only says how
near the nearest thing is.

**Events that move the price without moving a view are excluded.** Going
ex-dividend moves the price by the dividend by construction, and paying one
settles a decision already taken. Both are reported and neither sets this
reading, because neither is a reason for the market to expect something
different.

The score is a raw measurement on a scale that is not defined yet, and the report
labels it as such. Direction: a shorter distance means a nearer event, so smaller
means a more immediate reading.

Direction of the event is never stated. Whether a report will be good, whether a
decision will be a surprise, whether a launch will succeed — none of it is known
before it happens, and a rule that implied otherwise would be forecasting.
"""

from __future__ import annotations

from datetime import datetime

from contracts.catalyst_event_provider import DATE_METADATA_KEY, KIND_METADATA_KEY
from evaluation.catalyst.event_reading import read_events
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "catalyst.upcoming"


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the distance to the nearest event that could change a view.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the number of days until the nearest such event.

    Raises:
        DataError: When no forthcoming event was recorded, so that no invented
            distance reaches the score. The absence is the answer to the
            question and is reported as one.
    """
    moment = datetime.now()
    upcoming = [
        event
        for event in read_events(evidence)
        if event.is_upcoming(moment) and not event.is_mechanical
    ]
    if not upcoming:
        raise DataError(
            f"{RULE_ID}: no forthcoming event was recorded for "
            f"{evidence.asset.ticker}, so no catalyst reading was formed."
        )

    nearest = min(upcoming, key=lambda event: (event.days_from(moment), event.kind))
    days = nearest.days_from(moment)
    references = tuple(
        item.id
        for item in evidence.items
        if item.metadata.get(DATE_METADATA_KEY) == nearest.occurs_on.isoformat()
        and item.metadata.get(KIND_METADATA_KEY) == nearest.kind.value
    )
    return RuleResult(
        rule_id=RULE_ID,
        score=float(days),
        reason=(
            f"The nearest event that could change expectations for "
            f"{evidence.asset.ticker} is {nearest.description} in {days} days, "
            f"on {nearest.occurs_on}, reported by {nearest.source}"
        ),
        evidence_references=references,
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Next catalyst",
    description="Reports how far away the nearest event that could change a view is.",
    enabled=True,
    execute=_execute,
)
