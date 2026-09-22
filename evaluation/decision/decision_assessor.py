"""The Decision Layer: one answer, from judgements that already exist.

This layer answers exactly one question — **is this asset worth becoming a standard
position today** — and it answers it from judgements other layers have already reached.
It
reads no fact, re-interprets nothing, re-synthesises no category and decides no
quantity:
what it produces is the warrant, its grounds, and the gaps where a condition could not
be
evaluated.

**Why it is not a second assessment.** The Assessment says what AIS thinks of the
company.
This says whether what is already thought warrants holding a position now. The two read
different questions from the same judgements, and this layer adds no new judgement about
the asset: it evaluates the conditions its own question requires and reports how they
came
out.

**Why the conditions are evaluated here but decided elsewhere.** The method requires
that
each condition is evaluated; how it is evaluated — the bar — is Policy, read from
:mod:`config.decision_policy`. This module holds no threshold of its own, so that
changing
what "reads well enough" means is a change in one place rather than in a judgement.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from analysis.category_grade import reading_for
from config.decision_policy import BARS, CONDITION_CATEGORY
from evaluation.reading.category import CategoryReading
from models.category import Category
from models.decision_result import (
    ConditionOutcome,
    DecisionCondition,
    DecisionOutcome,
    DecisionResult,
)

# What the answer says when a condition could not be evaluated at all.
_NO_READING = (
    "{category} was not read, so the condition was not evaluated: nothing about it "
    "could be judged"
)
_NO_STEP = (
    "{category} was read but nothing in it carries a step, so nothing was compared"
)
_NO_MOMENT = (
    "the run produced no market data, so the judgements cannot be placed at this moment"
)


class DecisionAssessor:
    """Reaches a Decision from the judgements a run has already reached."""

    def assess(self, result: AnalysisResult) -> DecisionResult:
        """Return the Decision for one analysed asset.

        Args:
            result: The run's result, carrying the judgements already reached for it.

        Returns:
            The answer, the outcome of every condition, and the evidence behind them.
        """
        outcomes = tuple(
            self._decide(condition, result) for condition in DecisionCondition
        )
        return DecisionResult(
            outcome=_outcome_of(outcomes),
            conditions=outcomes,
            summary=_summary(outcomes),
            evidence_references=_references(outcomes),
        )

    def _decide(
        self, condition: DecisionCondition, result: AnalysisResult
    ) -> ConditionOutcome:
        """Return how one condition came out for one asset."""
        if condition is DecisionCondition.CURRENCY:
            return _currency_outcome(result)
        category = CONDITION_CATEGORY[condition]
        return _reading_outcome(
            condition, category, reading_for(result, category), result
        )


def _reading_outcome(
    condition: DecisionCondition,
    category: Category,
    reading: CategoryReading,
    result: AnalysisResult,
) -> ConditionOutcome:
    """Return how a condition read from one category came out."""
    references = _category_references(result, category)
    if reading.is_empty:
        return ConditionOutcome(
            condition=condition,
            satisfied=None,
            reason=_NO_READING.format(category=category.value),
        )
    mean = reading.mean_score
    weakest = reading.weakest_score
    if mean is None or weakest is None:
        return ConditionOutcome(
            condition=condition,
            satisfied=None,
            reason=_NO_STEP.format(category=category.value),
        )
    bar = BARS[condition]
    return ConditionOutcome(
        condition=condition,
        satisfied=mean >= bar.least_mean and weakest >= bar.least_weakest,
        reason=(
            f"{category.value} reads {mean} with a weakest member of {weakest}, "
            f"against a bar of {bar.least_mean} and {bar.least_weakest}"
        ),
        evidence_references=references,
    )


def _currency_outcome(result: AnalysisResult) -> ConditionOutcome:
    """Return whether the judgements belong to the moment of this judgement.

    The run retrieves its data and judges from it in the same pass, so a run with market
    data is by construction a judgement about now. A run without it has nothing to place
    at
    this moment, and that is reported as unevaluated rather than as a failure.
    """
    snapshot = result.market_data
    if snapshot is None:
        return ConditionOutcome(
            condition=DecisionCondition.CURRENCY, satisfied=None, reason=_NO_MOMENT
        )
    return ConditionOutcome(
        condition=DecisionCondition.CURRENCY,
        satisfied=True,
        reason=(
            f"the judgements were read from data retrieved at {snapshot.retrieved_at}"
        ),
    )


def _category_references(result: AnalysisResult, category: Category) -> tuple[str, ...]:
    """Return the evidence references the category judgement already carries.

    The condition rests on a judgement somebody else made, so its evidence is theirs:
    this
    layer carries the references forward rather than holding a copy of the evidence.
    """
    for score in result.assessment.category_scores:
        if score.category is category:
            return score.evidence_references
    return ()


def _outcome_of(outcomes: tuple[ConditionOutcome, ...]) -> DecisionOutcome:
    """Return the answer the condition outcomes amount to.

    A condition that could not be evaluated makes the question unanswerable rather than
    unfavourable: stating a no would claim an answer nobody reached.
    """
    if any(outcome.satisfied is None for outcome in outcomes):
        return DecisionOutcome.CANNOT_ANSWER
    if all(outcome.satisfied for outcome in outcomes):
        return DecisionOutcome.FAVOURABLE
    return DecisionOutcome.NOT_FAVOURABLE


def _summary(outcomes: tuple[ConditionOutcome, ...]) -> str:
    """Return one line naming what held, what did not, and what was not evaluated."""
    held = [outcome.condition.value for outcome in outcomes if outcome.satisfied]
    failed = [
        outcome.condition.value for outcome in outcomes if outcome.satisfied is False
    ]
    unknown = [
        outcome.condition.value for outcome in outcomes if outcome.satisfied is None
    ]
    parts = [f"{len(held)} of {len(outcomes)} conditions hold"]
    if held:
        parts.append(f"holds: {', '.join(held)}")
    if failed:
        parts.append(f"does not hold: {', '.join(failed)}")
    if unknown:
        parts.append(f"not evaluated: {', '.join(unknown)}")
    return "; ".join(parts)


def _references(outcomes: tuple[ConditionOutcome, ...]) -> tuple[str, ...]:
    """Return the evidence behind every judgement the answer rests on."""
    return tuple(
        dict.fromkeys(
            reference
            for outcome in outcomes
            for reference in outcome.evidence_references
        )
    )
