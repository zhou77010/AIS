"""Turning measurements into the sentences an investor reads.

A report is not a table of numbers. A reader wants to be told what the numbers
amount to, in their own language: "整体趋势向上" rather than a range position of
0.717 beside a change of +24.6%.

Everything here is a translation, never a new judgement. Each sentence restates
measurements that were retrieved and says nothing that those measurements do not
already say. Where a measurement is missing, the sentence is not written at all;
nothing is inferred to fill it.

The bands below are the same kind of provisional presentation as the category
grade: conventional readings, not methodology and not Constitution semantics,
and to be replaced once the standard score is defined. See
:mod:`analysis.category_grade`.
"""

from __future__ import annotations

# Where the price sits within the range it has traded in.
_POSITION_BANDS: tuple[tuple[float, str], ...] = (
    (0.80, "接近一年高位"),
    (0.60, "位于一年高位区间"),
    (0.40, "位于一年中段"),
    (0.20, "位于一年低位区间"),
    (float("-inf"), "接近一年低位"),
)

# Which way the price has moved over the window.
_DIRECTION_BANDS: tuple[tuple[float, str], ...] = (
    (0.20, "整体趋势向上"),
    (0.05, "整体小幅上行"),
    (-0.05, "整体横盘"),
    (-0.20, "整体小幅下行"),
    (float("-inf"), "整体趋势向下"),
)


def trend_sentence(position: float | None, direction: float | None) -> str | None:
    """Return what the price has been doing, in plain language.

    Args:
        position: Where the price sits within its range, or None.
        direction: How far the price moved over the window, or None.

    Returns:
        A sentence, or None when neither measurement was retrieved. A partial
        sentence is returned when only one of the two was available, because
        half the picture stated is worth more than none, as long as the missing
        half is not implied.
    """
    parts: list[str] = []
    if direction is not None:
        parts.append(_band(direction, _DIRECTION_BANDS))
    if position is not None:
        parts.append(_band(position, _POSITION_BANDS))
    if not parts:
        return None
    return "，".join(parts) + "。"


def _band(value: float, bands: tuple[tuple[float, str], ...]) -> str:
    """Return the phrase a value reads at, first matching band winning."""
    for threshold, phrase in bands:
        if value >= threshold:
            return phrase
    return bands[-1][1]
