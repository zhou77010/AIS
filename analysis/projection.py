"""What every phone projection decides the same way.

AIS renders the same analysis twice: once for one asset, when something about it
changed, and once as a brief over the whole watch universe. Both are phone
projections of the same model, and both must make the same decisions about how a
line is measured, how a sentence is broken, and how small a movement is too small
to mention.

Two renderers that each decided those things privately would drift apart, and the
drift would be invisible: both outputs would still look reasonable on their own.
A reader would then be told a category moved in one report and shown nothing
about it in the other, about the same reading from the same run.

So the decisions are made here, once, and both projections read them. What is
here is presentation and nothing else: no judgement is reached, no reading is
interpreted, and nothing here knows what a report is about.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence

from models.category_rating import CategoryRating

# The width a phone line may occupy, in display columns. Chinese characters
# occupy two, so counting characters would let a line be twice as wide as it looks.
LINE_WIDTH = 42

# What a wrapped sentence begins with, and how many columns are held back on every
# wrapped line so that a closing mark which may not start a line cannot push the
# line past the width.
INDENT = " "
WRAP_RESERVE = 2

# What a sentence may occupy and still be shown as one line.
PROJECTION_SENTENCE_WIDTH = LINE_WIDTH - len(INDENT) - WRAP_RESERVE

# What separates the parts of a report. It is a plain rule rather than a heading,
# because a heading would be a second name for a part the reader already has.
SECTION_SEPARATOR = "-" * 32

# Below this, a movement rounds to nothing and is not worth telling a reader
# about. It is a projection threshold and not a reading: the reading layer decides
# what a measurement means, and this decides only whether the movement is large
# enough to be worth a line on a phone.
MOMENTUM_FLOOR = 0.005

# Punctuation that may not begin a line. Chinese punctuation hangs off what it
# follows, so a break in front of it reads as a mistake.
NEVER_STARTS_A_LINE = "，。；：、？！）》”’%"


def display_width(text: str) -> int:
    """Return how many columns a string occupies, counting Chinese as two."""
    return sum(2 if is_wide(character) else 1 for character in text)


def is_wide(character: str) -> bool:
    """Return whether a character is drawn full width."""
    return unicodedata.east_asian_width(character) in {"W", "F"}


def wrap(text: str, *, first_prefix: str = INDENT) -> list[str]:
    """Break a sentence across lines, for text that has no items to keep whole.

    A sentence is not a list: it can be broken wherever it runs out of room, unlike
    a measurement or a name, which has to stay on one line to be read at all. Two
    columns are held back on every line so that a closing mark, which may not begin a
    line, cannot push a line past the width.

    Args:
        text: Sentence to break.
        first_prefix: Columns the sentence begins with. A sentence introduced by a
            label begins with the label, and its first line then holds fewer columns
            than the rest — which is what keeps a labelled sentence inside the width
            rather than overflowing the moment the label is added to it.
    """
    lines: list[str] = []
    current = ""
    for character in text:
        lead = first_prefix if not lines else INDENT
        if (
            current
            and character not in NEVER_STARTS_A_LINE
            and display_width(lead) + display_width(current) + display_width(character)
            > LINE_WIDTH - WRAP_RESERVE
        ):
            lines.append(lead + current)
            current = ""
        current += character
    if current:
        lines.append((first_prefix if not lines else INDENT) + current)
    return lines


def named_block(prefix: str, items: Sequence[str]) -> list[str]:
    """Return a labelled list of names, wrapped without splitting one.

    A name broken across two lines reads as two things, so the wrapping happens
    between names rather than inside them.
    """
    lines: list[str] = []
    current = prefix
    for index, item in enumerate(items):
        glue = "" if index == 0 else "、"
        width = display_width(current) + display_width(glue) + display_width(item)
        if width > LINE_WIDTH:
            lines.append(current)
            current = INDENT * 2 + item
            continue
        current += glue + item
    lines.append(current)
    return lines


def is_a_change(rating: CategoryRating) -> bool:
    """Return whether a rating says something about the asset has changed.

    Three things stay silent, and the per-asset report and the brief must agree on
    all of them, which is why the answer is computed here rather than in either
    renderer:

    * nothing moved — the grade stands where it stood and nothing accumulated
      inside it;
    * the grade is being read for the first time, which is a fact about the
      tracker rather than about the asset;
    * the movement is too small to read, below :data:`MOMENTUM_FLOOR`.
    """
    if rating.changed:
        return rating.previous_grade is not None
    return abs(rating.momentum) >= MOMENTUM_FLOOR
