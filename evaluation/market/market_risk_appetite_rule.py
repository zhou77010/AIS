"""Market rule: is the market being bought or sold right now?

Direction asks where the market has been over a year. This asks what it is doing
about risk today: the equity futures are the price of the whole market outside its
cash hours, and for a reader of a morning report they are the part of the
environment that has moved since the last close.

Two futures are read, and they are read together. The broad index says whether risk
is being taken at all; the growth index says which end of the market it is being
taken in. A tape where growth leads is a different environment from one where it
lags, and it is the difference the style sentence is written from.

Direction: a higher reading is a market being bought, so larger means a more
favourable environment. The score is a raw measurement on a scale that is not
defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_environment import EnvironmentMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

RULE_ID = "market.risk_appetite"
_EQUITY = EnvironmentMetric.OVERNIGHT_EQUITY
_GROWTH = EnvironmentMetric.OVERNIGHT_GROWTH
_PLACEHOLDER_CHANGE = 0.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without an environment source."""
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_CHANGE,
        reason=(
            f"Placeholder overnight equity change of {_PLACEHOLDER_CHANGE:.1%} for "
            f"{evidence.asset.ticker}; no environment source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return what the tape has done since the last close.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the broad futures move, with the growth move beside it
        in the reason.

    Raises:
        DataError: When an environment source was consulted and did not provide the
            measurement, so that no invented value reaches the score.
    """
    equity = read_metric(evidence, _EQUITY)
    if equity is None:
        return _placeholder(evidence)
    if equity.value is None:
        raise DataError(f"{RULE_ID}: {equity.reason}")

    growth = read_metric(evidence, _GROWTH)
    references = [equity.evidence_id]
    lead = ""
    if growth is not None and growth.value is not None:
        references.append(growth.evidence_id)
        lead = (
            f", growth {'leading' if growth.value > equity.value else 'lagging'} at "
            f"{growth.value:+.2%}"
        )
    return RuleResult(
        rule_id=RULE_ID,
        score=equity.value,
        reason=(
            f"Equity futures {equity.value:+.2%} since the last close for "
            f"{evidence.asset.ticker}{lead}; the risk being taken today"
        ),
        evidence_references=tuple(references),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Market risk appetite",
    description=(
        "Reports what the equity futures have done since the last close, and whether "
        "growth is leading or lagging."
    ),
    enabled=True,
    execute=_execute,
)
