"""AIS coverage domain model.

Coverage is how much of what a judgement needed was actually assessed. The
Constitution defines the term; this model carries the number.
"""

from __future__ import annotations

from dataclasses import dataclass

from utils.exceptions import ValidationError


@dataclass(frozen=True)
class Coverage:
    """How much of one category was actually assessed.

    Coverage and confidence answer different questions and neither replaces the
    other. Confidence says how much a claim should be trusted; coverage says how
    much of the ground the claim covers was examined at all. A category scored
    from three of eight dimensions is a different claim from one scored from
    eight, whatever confidence either carries.

    Attributes:
        assessed: How many of the category's units were assessed.
        total: How many units the category has.
    """

    assessed: int
    total: int

    def __post_init__(self) -> None:
        """Reject a coverage that cannot describe anything real.

        Raises:
            ValidationError: When the category has no units, or when more units
                were assessed than exist.
        """
        if self.total < 1:
            raise ValidationError(
                "a category must have at least one unit to assess, so total "
                "cannot be below one"
            )
        if not 0 <= self.assessed <= self.total:
            raise ValidationError(
                f"assessed ({self.assessed}) must be between 0 and total "
                f"({self.total})"
            )

    @property
    def is_complete(self) -> bool:
        """Return whether every unit of the category was assessed."""
        return self.assessed == self.total

    def describe(self) -> str:
        """Return the coverage as a short ratio."""
        return f"{self.assessed}/{self.total}"
