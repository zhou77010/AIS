"""The Decision Result: the outcome of the Decision Layer, and its grounds.

The Decision Layer answers one question — whether this asset is worth becoming a
standard
position today — and everything it produces is here. The result is deliberately not a
number and not a state word: it is the answer, the outcome of every condition the answer
rests on, and the names of anything that could not be evaluated.

**Why the answer has three outcomes and not two.** "Not favourable" and "could not be
answered" are different facts, and collapsing them would state that a question nobody
could ask was answered no (§3.18: insufficient evidence for a decision is an outcome,
not
a failure). A reader is entitled to tell the two apart.

**What the result does not carry.** No quantity, no method, no moment, and nothing about
an account. It also carries no aggregate confidence: the aggregation of confidence is
deferred by the Constitution, so this layer passes on what it was given rather than
inventing a number (§7).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DecisionCondition(StrEnum):
    """A condition that must exist before the Decision question can be answered.

    They are the Necessary Set: each one is required for the question to be answerable
    at
    all, and none of them says whether the answer is favourable. Whether a condition is
    met is decided by Policy, not here.
    """

    TERMS = "terms"
    RISK = "risk"
    CURRENCY = "currency"


class DecisionOutcome(StrEnum):
    """What the Decision Layer answered.

    The words are provisional: they name the outcome for the runtime's own use, and the
    vocabulary a reader sees is decided with the Report and is not part of this model.
    """

    FAVOURABLE = "favourable"
    NOT_FAVOURABLE = "not_favourable"
    CANNOT_ANSWER = "cannot_answer"


@dataclass(frozen=True)
class ConditionOutcome:
    """How one Required Condition came out.

    Attributes:
        condition: The condition that was evaluated.
        satisfied: Whether it is met, or None when it could not be evaluated. None is
        not
            a failure: it is the state of a question that was never answered.
        reason: One line stating what was read and what it read as.
        evidence_references: The evidence behind the judgement the condition was
        evaluated
            against, so that the outcome can be traced without this layer holding a
            copy.
    """

    condition: DecisionCondition
    satisfied: bool | None
    reason: str
    evidence_references: tuple[str, ...] = ()


@dataclass(frozen=True)
class DecisionResult:
    """The Decision, its grounds, and its gaps.

    Attributes:
        outcome: What was answered.
        conditions: The outcome of every condition, in a stated order.
        summary: One line naming what holds, what does not, and what was not judged.
        evidence_references: The evidence behind every judgement the answer rests on.
    """

    outcome: DecisionOutcome
    conditions: tuple[ConditionOutcome, ...]
    summary: str
    evidence_references: tuple[str, ...] = ()

    def outcome_for(self, condition: DecisionCondition) -> ConditionOutcome | None:
        """Return how one condition came out, or None when it was not evaluated."""
        for outcome in self.conditions:
            if outcome.condition is condition:
                return outcome
        return None
