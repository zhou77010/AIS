"""AIS evaluation result.

An evaluation result is the outcome of one rule engine run: the rule results
that succeeded, the rules that were skipped, the rules that failed, and the
counts describing the run.
"""

from __future__ import annotations

from dataclasses import dataclass

from evaluation.rule_result import RuleResult


@dataclass(frozen=True)
class RuleFailure:
    """Record of a rule that failed during execution.

    Attributes:
        rule_id: Identifier of the rule that failed.
        error_type: Name of the exception class the rule raised.
        message: Message of the exception the rule raised.
    """

    rule_id: str
    error_type: str
    message: str


@dataclass(frozen=True)
class ExecutionStatistics:
    """Counts describing one rule engine run.

    Attributes:
        total: Number of rules the engine received.
        succeeded: Number of rules that produced a result.
        skipped: Number of disabled rules that were skipped.
        failed: Number of rules that raised an error.
    """

    total: int
    succeeded: int
    skipped: int
    failed: int


@dataclass(frozen=True)
class EvaluationResult:
    """Outcome of one rule engine run.

    Attributes:
        results: Results of the rules that succeeded, in execution order.
        skipped_rule_ids: Identifiers of the disabled rules that were skipped.
        failures: Records of the rules that failed, in execution order.
    """

    results: tuple[RuleResult, ...]
    skipped_rule_ids: tuple[str, ...] = ()
    failures: tuple[RuleFailure, ...] = ()

    @property
    def statistics(self) -> ExecutionStatistics:
        """Return the counts describing this run."""
        succeeded = len(self.results)
        skipped = len(self.skipped_rule_ids)
        failed = len(self.failures)
        return ExecutionStatistics(
            total=succeeded + skipped + failed,
            succeeded=succeeded,
            skipped=skipped,
            failed=failed,
        )
