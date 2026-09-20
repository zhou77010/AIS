"""Market rule: which way is the cost of money going?

Every asset is priced off a discount rate, and the rate the environment sets is the
one nobody can opt out of. The ten year yield is the market's own reading of it.

Only the **change** is read, and deliberately so. A level is high or low against a
scale, and AIS has no agreed scale for what a high yield is: that number has moved
over decades and means different things in different regimes. The change over the
session is a fact that needs no such scale, and it is the part that has moved since
the reader last looked.

The direction is not scored. A rise in the cost of money is not worse in itself, and
it is not worse for every asset: it is worse for a long duration than a short one,
which is a statement about an asset and is made beside that asset's own
measurements, not here. The rule therefore reports the move and carries no score
that would pretend to a judgement this category cannot make alone.
"""

from __future__ import annotations

from contracts.market_environment import EnvironmentMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "market.rates"
_CHANGE = EnvironmentMetric.TEN_YEAR_YIELD_CHANGE
_PLACEHOLDER_CHANGE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without an environment source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CHANGE,
        reason=(
            f"Placeholder ten year yield change of {_PLACEHOLDER_CHANGE:+.1f} basis "
            f"points for {evidence.asset.ticker}; no environment source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return which way the cost of money moved over the session.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the yield change in basis points.

    Raises:
        DataError: When an environment source was consulted and did not provide the
            measurement, so that no invented value reaches the score.
    """
    change = read_metric(evidence, _CHANGE)
    if change is None:
        return _placeholder(evidence)
    if change.value is None:
        raise DataError(f"{RULE_ID}: {change.reason}")
    return RuleResult(
        rule_id=RULE_ID,
        score=change.value,
        reason=(
            f"Ten year yield {change.value:+.1f} basis points over the session for "
            f"{evidence.asset.ticker}; the rate every asset is priced off"
        ),
        evidence_references=(change.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Market rates",
    description="Reports which way the ten year yield moved over the session.",
    enabled=True,
    execute=_execute,
)
