"""Market rule: how turbulent is the environment?

An asset is judged in conditions, and one of those conditions is how violently
prices are moving. A calm market and a turbulent one are different places to hold
the same position: the same fall hurts differently when everything is moving
together.

The volatility index is the market's own price for that turbulence, and both its
level and its change are read. The level says what the conditions are; the change
says whether they are settling or deteriorating, which is the part that has moved
since the last close.

Direction: a lower reading is a calmer market, so smaller means a more favourable
environment. The score is a raw measurement on a scale that is not defined yet, and
the report labels it as such.
"""

from __future__ import annotations

from contracts.market_environment import EnvironmentMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "market.volatility"
_LEVEL = EnvironmentMetric.VOLATILITY
_CHANGE = EnvironmentMetric.VOLATILITY_CHANGE
_PLACEHOLDER_LEVEL = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without an environment source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_LEVEL,
        reason=(
            f"Placeholder volatility level of {_PLACEHOLDER_LEVEL} for "
            f"{evidence.asset.ticker}; no environment source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return how turbulent the market is, and which way that is going.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the volatility level, with its change beside it.

    Raises:
        DataError: When an environment source was consulted and did not provide the
            measurement, so that no invented value reaches the score.
    """
    level = read_metric(evidence, _LEVEL)
    if level is None:
        return _placeholder(evidence)
    if level.value is None:
        raise DataError(f"{RULE_ID}: {level.reason}")

    change = read_metric(evidence, _CHANGE)
    references = [level.evidence_id]
    moved = ""
    if change is not None and change.value is not None:
        references.append(change.evidence_id)
        moved = f", {change.value:+.2f} points on the session"
    return RuleResult(
        rule_id=RULE_ID,
        score=level.value,
        reason=(
            f"Volatility index at {level.value:,.2f} for {evidence.asset.ticker}"
            f"{moved}; the conditions the position is held in"
        ),
        evidence_references=tuple(references),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Market volatility",
    description=(
        "Reports the volatility index level and how far it moved on the session."
    ),
    enabled=True,
    execute=_execute,
)
