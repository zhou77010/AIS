"""What the evidence means, as opposed to what it is.

An insight is an interpretation of evidence that has already been collected. It
says what the measurements amount to, and it is the answer to the question a
reader actually has: not "what is the P/E" but "what does this P/E mean".

**An insight is not a prediction.** Every line restates something the evidence
already supports and stops there. AIS does not say what will happen, does not
give a target, and does not put a probability on anything. The difference is the
whole point of this layer: an interpretation can be checked against the evidence
behind it, and a forecast cannot be checked against anything until it is too late
to matter.

**Every line is traceable.** A line carries the identifiers of the evidence it
was read from, so a reader asking "why does it say that" can be answered with the
records rather than with an explanation written afterwards. A line that cannot
name its evidence is not an insight; it is an opinion.

**An insight is not a summary.** A summary repeats the measurements. This layer
exists because repeating measurements leaves the reader to do the interpreting,
which is the part they came for.
"""

from __future__ import annotations

from dataclasses import dataclass

from models.category import Category


@dataclass(frozen=True)
class InsightLine:
    """One sentence of interpretation, and the evidence behind it.

    Attributes:
        text: The sentence, written for a reader.
        references: Identifiers of the evidence the sentence was read from. It
            is never empty: a sentence with nothing behind it would be an
            opinion presented as a reading.
    """

    text: str
    references: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject a line that cannot say where it came from."""
        if not self.references:
            raise ValueError(f"an insight line must name its evidence: {self.text!r}")


@dataclass(frozen=True)
class Insight:
    """What one category's evidence means.

    Attributes:
        category: Category the interpretation is about.
        lines: Sentences that were supported by the evidence, in reading order.
            A category whose evidence supports nothing is empty rather than
            filled with a sentence that would be invented.
    """

    category: Category
    lines: tuple[InsightLine, ...]

    @property
    def is_empty(self) -> bool:
        """Return whether nothing could be said about this category."""
        return not self.lines

    @property
    def references(self) -> tuple[str, ...]:
        """Return every piece of evidence the interpretation stands on."""
        return tuple(
            dict.fromkeys(
                reference for line in self.lines for reference in line.references
            )
        )
