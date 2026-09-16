"""Risk rule: market risk.

Market risk is the possibility that the asset moves against the holder for
reasons that have nothing to do with the business (Constitution, Section 5.2).
The measurement reported here is beta, which describes how much an asset has
moved relative to the market it trades in.

Beta is evidence for market risk. It is not the definition of it: an asset with
a low beta still carries market risk, and beta says nothing about the reasons
the market might move.

Direction: a higher beta means a larger move for a given market move, so higher
means more market risk. The score is a raw measurement on a scale that is not
defined yet, and the report labels it as such.
"""

from __future__ import annotations

from contracts.market_data_provider import MarketMetric
from evaluation.evaluation_rule import EvaluationRule
from evaluation.market_evidence import read_metric
from evaluation.risk.risk_dimensions import RiskDimension
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection
from utils.exceptions import DataError

DIMENSION = RiskDimension.MARKET

RULE_ID = "risk.market"
_METRIC = MarketMetric.BETA
_PLACEHOLDER_BETA = 1.0


def _placeholder(evidence: EvidenceCollection) -> RuleResult:
    """Return the placeholder measurement for a run without a market source.

    No evidence references are recorded, because no evidence stands behind a
    placeholder value. Claiming otherwise would put a reference in the report
    that points at nothing.
    """
    return RuleResult(
        rule_id=RULE_ID,
        score=_PLACEHOLDER_BETA,
        reason=(
            f"Placeholder beta of {_PLACEHOLDER_BETA} for "
            f"{evidence.asset.ticker}; no market data source connected."
        ),
        evidence_references=(),
    )


def _execute(evidence: EvidenceCollection) -> RuleResult:
    """Return the market risk measurement for the asset.

    Args:
        evidence: Evidence collected for the asset.

    Returns:
        Rule result carrying the retrieved beta.

    Raises:
        DataError: When a market data source was consulted and did not provide
            the measurement, so that no invented value reaches the score.
    """
    reading = read_metric(evidence, _METRIC)
    if reading is None:
        return _placeholder(evidence)
    if reading.value is None:
        raise DataError(f"{RULE_ID}: {reading.reason}")
    return RuleResult(
        rule_id=RULE_ID,
        score=reading.value,
        reason=(
            f"Beta {reading.value:.2f} for {evidence.asset.ticker}; "
            f"a larger beta means larger moves against the market"
        ),
        evidence_references=(reading.evidence_id,),
    )


RULE = EvaluationRule(
    id=RULE_ID,
    name="Market risk",
    description="Reports the retrieved beta as a measurement of market risk.",
    enabled=True,
    execute=_execute,
)
