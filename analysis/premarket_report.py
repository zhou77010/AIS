"""The pre-market brief rendered for a phone.

This is a second projection of :class:`~analysis.brief.DailyBrief`, and it is *not* a
second report model: the same analysis produces it, the same selection decides which
assets it shows, and the same sentences are read back from the insights the run already
built. What differs is the question it answers and the hour it answers it at.

**What makes it a different report from the morning one.** The morning brief is sent
after
the United States day has ended and describes a session that is over. This one is sent
thirty minutes before the next session opens, and the fact it can state that the morning
one cannot is **what price is doing before the open**: the pre-market move, read minutes
ago rather than twelve hours ago. Everything else is deliberately the same digest the
reader already knows, so that the two reports cannot describe the same session two ways.

**It states which layers answered.** The report is built from three kinds of evidence —
the environment, the company's own pre-market evidence, and news — and they arrive at
different speeds. Rather than waiting for all three before saying anything, it says
which
of them it holds, once, near the top. A reader told that the company layer answered for
five assets of seven knows what the rest of the message is and is not about.

**What it deliberately does not do.** It does not forecast the session, it does not
state
an opening price, and it does not re-rank the assets: the pre-market move is described
and
not graded, because the reading layer has not decided what it is worth, and a renderer
may
not decide that on its own.
"""

from __future__ import annotations

from analysis.brief import BriefEntry, DailyBrief
from analysis.brief_report import (
    coverage_line,
    entry_heading,
    environment_lines,
    header_line,
    joined_parts,
    tail_lines,
)
from analysis.category_grade import reading_for
from analysis.projection import display_width
from contracts.market_data_provider import MarketMetric
from evaluation.reading.category import CategoryReading
from models.category import Category

# The budget this projection is held to by tests/test_premarket_brief.py. The same cap
# as
# the morning brief: a report that has to be scrolled is a report nobody finishes.
PREMARKET_LINE_BUDGET = 24

_TITLE = "AIS 盘前简报"
# The label and the states are short because the line names three layers with a state
# each and the whole of it has to fit the width every phone projection uses. The company
# layer is called 公司 rather than 公司盘前 so that it cannot be confused with the
# section label below it.
_LAYERS_LABEL = "层次  "
_PREMARKET_LABEL = "盘前  "
# How a continuation line of a named block is indented. It is the label's own width, so
# that the lines under a label line up with it whatever the label is written in.
_PREMARKET_INDENT = " " * display_width(_PREMARKET_LABEL)

# The three kinds of evidence the report is built from, named as a reader would name
# them.
_ENVIRONMENT_LAYER = "环境"
_COMPANY_LAYER = "公司"
_NEWS_LAYER = "新闻"

_LAYER_PRESENT = "完整"
_LAYER_PARTIAL = "部分"
_LAYER_ABSENT = "不可得"
# The news layer is not missing from this run: it is not connected at all. That is a
# fact
# about AIS rather than about the source, and it is said with its own word.
_LAYER_UNCONNECTED = "未接"


def render_premarket_brief(brief: DailyBrief) -> str:
    """Render the pre-market brief as the one message the reader receives.

    Args:
        brief: The brief to render, built from this run's results.

    Returns:
        Plain text, ready to be sent through a push channel.
    """
    parts = [
        [
            header_line(brief, title=_TITLE),
            coverage_line(brief),
            *_layer_lines(brief),
            *environment_lines(brief),
        ],
        _premarket_lines(brief),
        tail_lines(brief),
    ]
    return "\n".join(joined_parts(parts))


def _layer_lines(brief: DailyBrief) -> list[str]:
    """Return the line stating which of the three layers of evidence answered.

    The report exists before all three layers do. Saying which of them answered is what
    makes that honest: a reader then knows whether the message is thin because the
    market
    is quiet or because AIS could not see the company's own morning.

    It is kept to one line rather than wrapped. Three layers with a state each fit the
    width if the words are short, and wrapping the list was breaking a word in half to
    do
    it, which is worse than the shorter word.
    """
    shown = [entry for entry in brief.entries if entry.result.market_data is not None]
    answered = [entry for entry in shown if _premarket_value(entry) is not None]
    environment = _LAYER_PRESENT if brief.environment is not None else _LAYER_ABSENT
    if not shown:
        company = _LAYER_ABSENT
    elif len(answered) == len(shown):
        company = _LAYER_PRESENT
    else:
        company = f"{len(answered)}/{len(shown)}"
    return [
        f"{_LAYERS_LABEL}{_ENVIRONMENT_LAYER} {environment} · "
        f"{_COMPANY_LAYER} {company} · {_NEWS_LAYER} {_LAYER_UNCONNECTED}"
    ]


def _premarket_lines(brief: DailyBrief) -> list[str]:
    """Return what price is doing before the open, for the assets the brief shows.

    Only the assets the brief already selected are named, and only those the source
    answered for. An asset with no pre-market reading is left out rather than shown with
    a
    blank, and the count on the layer line says how many were left out.
    """
    lines = [
        f"{entry_heading(entry)}  {phrase}"
        for entry in brief.entries
        if (phrase := _premarket_phrase(entry)) is not None
    ]
    if not lines:
        return []
    return [
        f"{_PREMARKET_LABEL}{lines[0]}",
        *[f"{_PREMARKET_INDENT}{line}" for line in lines[1:]],
    ]


def _premarket_phrase(entry: BriefEntry) -> str | None:
    """Return the pre-market move of one asset as a phrase, or None.

    The wording is the reading layer's own: it decided what the move reads as, and this
    only puts the size beside that word. A move inside the band that means nothing
    happened gets no number, because a number beside it invites a reader to read one
    into
    it.
    """
    value = _premarket_value(entry)
    reading = reading_for(entry.result, Category.MARKET)
    word = reading.word(MarketMetric.PREMARKET_GAP)
    if value is None or word is None:
        return None
    return word if _is_flat(reading) else f"{word} {abs(value):.1%}"


def _is_flat(reading: CategoryReading) -> bool:
    """Return whether the pre-market move fell in the band that means nothing moved."""
    read = reading.read(MarketMetric.PREMARKET_GAP)
    return read is not None and read.band.is_flat


def _premarket_value(entry: BriefEntry) -> float | None:
    """Return the pre-market move the run retrieved for one asset, or None."""
    snapshot = entry.result.market_data
    if snapshot is None:
        return None
    return snapshot.point(MarketMetric.PREMARKET_GAP).value
