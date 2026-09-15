"""AIS rule engine.

Executes evaluation rules in order and collects every outcome. The engine is
generic: it knows only EvaluationRule, RuleResult and EvaluationResult, and it
never stops because a single rule fails.
"""

from __future__ import annotations

from evaluation.evaluation_result import EvaluationResult, RuleFailure
from evaluation.evaluation_rule import EvaluationRule
from evaluation.rule_result import RuleResult
from evidence.evidence_collection import EvidenceCollection


class RuleEngine:
    """Executes evaluation rules and collects their results."""

    def run(
        self,
        rules: tuple[EvaluationRule, ...],
        evidence: EvidenceCollection,
    ) -> EvaluationResult:
        """Execute the enabled rules and collect every outcome.

        Disabled rules are skipped. Execution order is the order the rules are
        given in. A rule that raises is recorded as a failure and does not stop
        the remaining rules.

        Args:
            rules: Rules to execute, in execution order.
            evidence: Evidence passed to every rule.

        Returns:
            EvaluationResult holding the results, the skipped rules, the
            failures and the statistics of the run.
        """
        results: list[RuleResult] = []
        skipped: list[str] = []
        failures: list[RuleFailure] = []

        for rule in rules:
            if not rule.enabled:
                skipped.append(rule.id)
                continue
            try:
                results.append(rule.execute(evidence))
            except Exception as error:
                failures.append(
                    RuleFailure(
                        rule_id=rule.id,
                        error_type=type(error).__name__,
                        message=str(error),
                    )
                )

        return EvaluationResult(
            results=tuple(results),
            skipped_rule_ids=tuple(skipped),
            failures=tuple(failures),
        )
