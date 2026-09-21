"""What the environment means for this asset.

Market answers a question about context, and this is where that question is actually
answered. The reading layer says what each measurement means and the evaluator says
how much of the environment was examined; neither writes the sentence a reader needs,
which is: **what do the conditions mean for the position being judged?**

**Two inputs, one sentence.** The environment's measurements are the market's own —
the futures overnight, volatility, the cost of money — and they are the same for every
asset in the market. The asset's measurements are what it is: its beta, what its
valuation reads as, what kind of business it was declared to be. Neither alone answers
the question. A rising yield is not bad news; a rising yield beside a valuation that
reads expensive is, and that pair is what this module is for.

**Every sentence names both halves.** "Growth is under pressure" is a market recap;
"growth is under pressure and this is a growth company" is a judgement about the
asset. So each sentence is read from named measurements on both sides and carries the
identifiers of exactly those measurements, the way every other sentence in the report
does.

**Nothing here has a threshold of its own.** Whether a measurement reads high or low
is a band position, and whether it moved is the band the reading layer marks as flat.
This module reads those and composes phrases, which is why the sentence and the grade
above it cannot disagree about what a number meant.

**What it will not say.** Where a mechanism needs evidence AIS does not have, the
sentence says so instead of guessing a direction: a rate move reaches a bank's margin
through the shape of the curve, not through one yield, and the curve is not connected.
An environment with nothing in it produces no claim at all.
"""

from __future__ import annotations

from dataclasses import dataclass

from analysis.insight.context import InsightContext
from analysis.labels import sector_label
from contracts.market_data_provider import MarketMetric as M
from contracts.market_environment import EnvironmentMetric as E
from models.asset_profile import AssetProfile
from models.insight import InsightLine

# A band position at or above this reads favourably and one at or below it reads
# unfavourably. The positions are the reading layer's: two is the second lowest of
# five bands and four the second highest, and they are read here rather than derived
# again.
_STRONG = 4
_WEAK = 2

# The kinds of asset an environment sentence can be written about. Only the kinds AIS
# can say something honest about appear: a cyclical is exposed to a cycle AIS does not
# measure, an ETF holds a style of its own, and an unknown kind supports no claim.
_GROWTH_PROFILE = AssetProfile.HIGH_GROWTH
_FINANCIAL_PROFILE = AssetProfile.FINANCIAL

# The measurements that make up the environment, in the order they are named.
_ENVIRONMENT_METRICS: tuple[E, ...] = (
    E.OVERNIGHT_EQUITY,
    E.OVERNIGHT_GROWTH,
    E.VOLATILITY,
    E.VOLATILITY_CHANGE,
    E.TEN_YEAR_YIELD_CHANGE,
)

# What is said when the environment was read and nothing about this asset meets it.
_NO_EXPOSURE = "当前环境与本标的的敏感属性没有叠加，影响有限。"

# What the growth tape is doing, when it is doing anything different from the broad
# one. The two are read against each other: a market where growth falls less than the
# broad tape is still a market where growth is being preferred. The wording is short
# because it is read inside a sentence that already names three other conditions.
_GROWTH_LEADING = "成长股领先"
_GROWTH_LAGGING = "成长股落后"


@dataclass(frozen=True)
class _Impact:
    """One way the environment bears on an asset.

    Attributes:
        phrase: The sentence, read from measurements on both sides.
        references: The evidence it was read from, which is always an environment
            measurement and one of the asset's own.
    """

    phrase: str
    references: tuple[str, ...]


def build(context: InsightContext) -> tuple[InsightLine, ...]:
    """Return what the environment means for this asset, then what it is doing.

    The first sentence is the one a phone report shows, so it is the sentence about
    this asset. The environment itself comes second, because it is the same for every
    asset: the brief states it once for the whole universe, and repeating it per asset
    is repeating one fact. What the asset's own price did before the session opened
    comes last, because it is the one measurement here that is about this asset alone.

    Where no environment measurement was retrieved, the sentence falls back to what
    the broad market has done over a year, which is the measure of the environment AIS
    has had all along and is the honest answer for a run that has nothing else.
    """
    if not context.has_any(*_ENVIRONMENT_METRICS):
        direction = _direction_line(context)
        fallback = [] if direction is None else [direction]
        premarket = _premarket_line(context)
        return tuple(fallback + ([] if premarket is None else [premarket]))

    lines: list[InsightLine] = [
        InsightLine(impact.phrase, impact.references)
        for impact in _impacts(context)[:2]
    ]
    if not lines:
        references = context.reference(*_ENVIRONMENT_METRICS)
        lines.append(InsightLine(_NO_EXPOSURE, references))
    environment = environment_line(context)
    if environment is not None:
        lines.append(environment)
    premarket = _premarket_line(context)
    if premarket is not None:
        lines.append(premarket)
    return tuple(lines)


def _premarket_line(context: InsightContext) -> InsightLine | None:
    """Return what the price did before the session opened, or None.

    This is the freshest thing AIS knows about the asset itself: the move was made
    before the session it belongs to has opened, and it is a fact about this asset
    rather than about the market it is in. It is described and not graded — the reading
    layer decides that, and it decided against grading it — so the sentence says what
    happened and claims nothing about what it is worth.

    The wording carries the size only where there is a size to carry: a move inside the
    flat band is a session that has not said anything yet, and putting a number beside
    it would invite a reader to read one into it.
    """
    word = context.word(M.PREMARKET_GAP)
    value = context.value(M.PREMARKET_GAP)
    reference = context.reference(M.PREMARKET_GAP)
    if word is None or value is None or not reference:
        return None
    band = context.band(M.PREMARKET_GAP)
    if band is not None and band.is_flat:
        return InsightLine("盘前基本持平，开盘前没有新的价格信息。", reference)
    return InsightLine(f"{word} {abs(value):.1%}，开盘前价格已经先动。", reference)


def environment_line(context: InsightContext) -> InsightLine | None:
    """Return what the market is doing, said once for every asset in it.

    This is the sentence a brief leads with. It names no asset, because it is about no
    asset: it says what the conditions are, and what they mean for a particular
    holding is a different sentence, written beside that holding's own measurements.

    Args:
        context: Interpretation context holding the environment's measurements.

    Returns:
        The sentence, or None when no environment measurement was retrieved.
    """
    references = context.reference(*_ENVIRONMENT_METRICS)
    if not references:
        return None
    return InsightLine(f"{_conditions(context)}，{_verdict(context)}。", references)


def _conditions(context: InsightContext) -> str:
    """Return what the environment is doing, as a clause.

    Only what moved is named, and the level of volatility is named whether or not it
    moved, because it is the one reading here that is a condition rather than a
    change. A market where nothing moved is a fact and the verdict says so; listing
    three measurements that did not move would spend the sentence saying nothing three
    times.
    """
    parts: list[str] = []
    appetite = context.word(E.OVERNIGHT_EQUITY)
    if appetite is not None and context.moved(E.OVERNIGHT_EQUITY):
        parts.append(appetite)
    style = _style_clause(context)
    if style is not None:
        parts.append(style)
    volatility = context.word(E.VOLATILITY)
    if volatility is not None:
        change = context.word(E.VOLATILITY_CHANGE)
        parts.append(
            f"{volatility}且{change}"
            if change is not None and context.moved(E.VOLATILITY_CHANGE)
            else volatility
        )
    rates = context.word(E.TEN_YEAR_YIELD_CHANGE)
    if rates is not None and context.moved(E.TEN_YEAR_YIELD_CHANGE):
        parts.append(rates)
    curve = _inverted_curve_clause(context)
    if curve is not None:
        parts.append(curve)
    return "、".join(parts) if parts else "环境各项指标均无明显变化"


def _inverted_curve_clause(context: InsightContext) -> str | None:
    """Return the shape of the curve when it is inverted, and nothing otherwise.

    A level is named when it is a state the reader has to know about. "The curve is
    normal" every morning is noise; an inverted curve is not, and it is worth saying
    even on a day when it did not move.
    """
    return context.word(E.CURVE_STEEPNESS) if _curve_is_inverted(context) else None


def _verdict(context: InsightContext) -> str:
    """Return what the conditions amount to for risk, in one clause.

    Two readings decide it and no more: whether risk is being taken, and how turbulent
    the market is. Both are graded, which is what makes them a judgement about whether
    the conditions favour owning risk rather than a description of them.
    """
    grades = [
        grade
        for grade in (
            context.score(E.OVERNIGHT_EQUITY),
            context.score(E.VOLATILITY),
        )
        if grade is not None
    ]
    if not grades:
        return "环境没有给出方向"
    if all(grade >= _STRONG for grade in grades):
        return "环境对风险资产偏友好"
    if all(grade <= _WEAK for grade in grades):
        return "环境对风险资产不利"
    return "环境对风险资产偏中性"


def _style_clause(context: InsightContext) -> str | None:
    """Return whether growth is leading or lagging the broad market, if either is."""
    growth = context.score(E.OVERNIGHT_GROWTH)
    broad = context.score(E.OVERNIGHT_EQUITY)
    if growth is None or broad is None or growth == broad:
        return None
    return _GROWTH_LEADING if growth > broad else _GROWTH_LAGGING


def _impacts(context: InsightContext) -> list[_Impact]:
    """Return every way the environment bears on this asset, most concrete first.

    The order is the order they are worth reading: what this asset's own part of the
    market is doing, then what the tape is doing to a position of this sensitivity,
    then what the cost of money does to what it costs, then whether the kind of
    business it is happens to be in or out of favour, and last an exposure AIS can
    name and cannot yet judge the direction of.
    """
    impacts: list[_Impact] = []
    for rule in (_sector, _movement, _cost_of_money, _kind, _sensitivity):
        impact = rule(context)
        if impact is not None:
            impacts.append(impact)
    return impacts


def _sector(context: InsightContext) -> _Impact | None:
    """Return what the asset's own part of the market is doing.

    This is the most specific thing the environment can say about a holding, and it is
    the reason the sector is stated at all: the market being up says little about a
    bank, and the financial sector being sold while the market is bought says a great
    deal about one. The reading is the sector's move against the market over the same
    session, so it is a comparison and not a level.

    It says what was measured — the sector moved against the market — and not why.
    A relative move is consistent with money leaving a sector and it is not a flow
    figure, and a sentence claiming flows would be claiming something nobody measured.
    """
    if context.sector is None or not context.moved(E.SECTOR_RELATIVE_MOVE):
        return None
    score = context.score(E.SECTOR_RELATIVE_MOVE)
    if score is None:
        return None
    name = sector_label(context.sector)
    references = context.reference(E.SECTOR_RELATIVE_MOVE)
    if score <= _WEAK:
        return _Impact(f"所属板块（{name}）跑输大盘，本标的短期承压。", references)
    if score >= _STRONG:
        return _Impact(f"所属板块（{name}）跑赢大盘，本标的短期有支撑。", references)
    return None


def _movement(context: InsightContext) -> _Impact | None:
    """Return what the tape is doing to a position of this sensitivity.

    A falling tape and a rising price of protection are the same statement about risk,
    so either raises the question, and the asset's own beta is what answers it. Beta is
    read from its own scale, so an asset described as low beta is told it is
    defensive, and one described as high beta is told its swings may widen, from the
    same reading that produced the description.
    """
    if not _risk_is_falling(context):
        return None
    beta = context.score(M.BETA)
    if beta is None:
        return None
    conditions = _risk_off_clause(context)
    references = context.reference(E.OVERNIGHT_EQUITY, E.VOLATILITY_CHANGE, M.BETA)
    word = context.word(M.BETA)
    if beta <= _WEAK:
        return _Impact(f"{conditions}，本标的贝塔{word}，波动可能放大。", references)
    if beta >= _STRONG:
        return _Impact(f"{conditions}，本标的贝塔{word}，相对抗跌。", references)
    return None


def _cost_of_money(context: InsightContext) -> _Impact | None:
    """Return what a move in the cost of money does to what this asset costs.

    The pair is the point and neither half is a judgement alone: a rise in the yield
    is not a problem for a cheap asset, and an expensive valuation is not a problem
    while money is cheap. The valuation is read from the asset's own scales, so
    whichever measurement a reader would call expensive decides it.
    """
    if not context.rose(E.TEN_YEAR_YIELD_CHANGE):
        return None
    valuation = _valuation_word(context)
    if valuation is None:
        return None
    metrics = (E.TEN_YEAR_YIELD_CHANGE, M.PE, M.EV_EBITDA, M.FCF_YIELD)
    return _Impact(
        f"利率上行而估值{valuation}，分母端承压。", context.reference(*metrics)
    )


def _kind(context: InsightContext) -> _Impact | None:
    """Return whether the kind of business this is happens to be in favour.

    What kind of thing an asset is decides which environment bears on it, and that is
    stated rather than inferred: AIS was told this is a growth company, so a tape that
    is selling growth is a tape that is selling this.
    """
    if context.profile is not _GROWTH_PROFILE:
        return None
    if _style_clause(context) != _GROWTH_LAGGING:
        return None
    return _Impact(
        "成长风格弱于大盘，本标的属成长型，短期相对承压。",
        context.reference(E.OVERNIGHT_GROWTH, E.OVERNIGHT_EQUITY),
    )


def _sensitivity(context: InsightContext) -> _Impact | None:
    """Return what the shape of the curve means for a rate sensitive business.

    This is the sentence that used to say the direction could not be judged. A bank's
    margin moves with the shape of the curve rather than with one yield, and the curve
    is read now — from the Treasury's daily file, which is the only place rates are read
    from — so the sentence can say which way the margin environment is moving.

    An inverted curve is named whether or not it moved: it is a state a holder of a
    financial needs to know about, and the morning after it stopped moving it is still
    inverted.
    """
    if context.profile is not _FINANCIAL_PROFILE:
        return None
    inverted = _curve_is_inverted(context)
    if not inverted and not context.moved(E.CURVE_CHANGE):
        return None
    references = context.reference(E.CURVE_CHANGE, E.CURVE_STEEPNESS)
    if inverted:
        return _Impact(
            f"{context.word(E.CURVE_STEEPNESS)}，金融机构的息差环境偏紧。", references
        )
    if context.rose(E.CURVE_CHANGE):
        return _Impact("曲线走陡，金融机构的息差环境偏有利。", references)
    return _Impact("曲线趋平，金融机构的息差环境偏紧。", references)


def _curve_is_inverted(context: InsightContext) -> bool:
    """Return whether the curve is inverted, which is what a negative spread is.

    It is asked of the value rather than of a band because inversion has a definition
    and not a threshold: a ten year yield below a two year yield is an inverted curve,
    by the meaning of the words.
    """
    spread = context.value(E.CURVE_STEEPNESS)
    return spread is not None and spread < 0


def _risk_is_falling(context: InsightContext) -> bool:
    """Return whether the environment is turning against risk today."""
    appetite = context.score(E.OVERNIGHT_EQUITY)
    return (appetite is not None and appetite <= _WEAK) or context.rose(
        E.VOLATILITY_CHANGE
    )


def _risk_off_clause(context: InsightContext) -> str:
    """Return the conditions turning against risk, named."""
    parts = [
        word
        for metric, word in (
            (E.OVERNIGHT_EQUITY, context.word(E.OVERNIGHT_EQUITY)),
            (E.VOLATILITY_CHANGE, context.word(E.VOLATILITY_CHANGE)),
        )
        if word is not None and context.moved(metric)
    ]
    return "、".join(parts) if parts else "环境转向防御"


def _valuation_word(context: InsightContext) -> str | None:
    """Return how this asset's valuation reads, when it reads dear.

    Three measurements can say it and any of them is enough: the multiples that read
    expensive and the cash flow yield that reads thin are views of the same thing, and
    requiring all of them would let an asset be called cheap because only one of its
    scales noticed.
    """
    for metric in (M.PE, M.EV_EBITDA):
        score = context.score(metric)
        if score is not None and score <= _WEAK:
            return context.word(metric)
    if context.is_at_most(M.FCF_YIELD, _WEAK):
        return context.word(M.FCF_YIELD)
    return None


def _direction_line(context: InsightContext) -> InsightLine | None:
    """Return what the broad market has done, for a run with no environment.

    This is the sentence the category wrote before the environment was connected, and
    it is kept for the case it was written for: a run whose only measurement of the
    environment is the broad market's change over a year.
    """
    direction = context.score(M.MARKET_DIRECTION)
    if direction is None:
        return None
    reference = context.reference(M.MARKET_DIRECTION)
    if direction >= _STRONG:
        return InsightLine("大盘整体上行，环境对风险资产偏友好。", reference)
    if direction <= _WEAK:
        return InsightLine("大盘整体下行，环境对新增仓位不利。", reference)
    return InsightLine("大盘整体横盘，环境没有提供方向。", reference)
