# AIS Backlog

Deferred work, recorded so it is not lost and not repeated. Nothing here blocks
current development.

This is a list of pending items, not an authoritative document. Meaning lives in
`docs/Constitution.md`, available evidence lives in `docs/EvidenceSurvey.md`, and
structure lives in `docs/Architecture.md`.

---

## Product review, after all nine categories are evaluated

The report currently speaks in developer language. It is read by an investor, so
the following changes are agreed and deferred to one review rather than made
piecemeal:

**Model information must not be shown raw.** Coverage is reported as fractions
such as `3/8 dimensions`, `2/3 aspects`, `4/5 measurements`. Those are model
internals. They should be translated into investor language — "partly covered",
or "not yet assessed: event risk, horizon risk" — rather than exposed as ratios.
The model keeps the numbers; the renderer decides what a reader sees.

**Translated, not tabulated.** The report no longer shows how much of a category
was assessed as a fraction. What a reader needs is what was not examined, named:
"尚未评估：事件风险、长期风险、DCF 公允价值". A proportion is bookkeeping about
the model, and the model keeps it.

The intended shape, so far:

1. **The judgement**, as a visual grade rather than a number. An investor should
   not be asked to compare `13.26` against `0.48` against `5.95`, which are
   different units on an undefined scale.
2. **Why**, as one plain sentence — valuation looks stretched, cash flow is
   deteriorating. The summary is what is meant to be read; the evidence is only
   support. Where a measurement reads better as a sentence, the report writes
   the sentence and leaves the number in the evidence, as Trend now does.
3. **What was not looked at**, named rather than counted.

**Chinese first.** Except for technical terms, the report should be in Chinese:
估值, 风险, 趋势, 盈利, 市场环境, 催化因素, 仓位. Evidence may keep English
metric names. Summaries and the recommendation should be Chinese.

The unified score is not a prerequisite for any of this. When the AIS Standard
Score lands, the visual grade can be restored to a real scale.

---

## Category structure, for the same review

Each category so far has answered its question with a different structure, and
that was deliberate: the structure was chosen per category rather than fixed as a
pattern.

| Category | Unit of coverage | Why |
| --- | --- | --- |
| Valuation | measurements | Its rules are its measurements. |
| Risk | dimensions | The Constitution fixes eight risk dimensions. |
| Fundamental | measurements | Each measurement is one part of soundness; an aspect layer would only rename them. |
| Market | aspects | One measurement, and `1/1` would have claimed the environment was examined. |
| Trend | aspects | Two measurements, and nothing is seen about how the price travelled. |
| Earnings | parts | The Constitution names both parts in the question. |
| Catalyst | parts | One part is dated by a source, one part has no source at all. |
| Positioning | parts | Ownership and crowding are measured; flow is not. |

The review should decide which of these are right, and whether the aspect and
dimension layers are real parts of a question or scaffolding that should be
replaced. None of them is Constitution semantics today.

**Also deferred to that review:**

- The Fundamental question reads "What is the business, and is it financially
  sound?" — two clauses, where every other category asks one question. Only the
  second clause is evaluated.
- The Market aspect set and the Trend aspect set are this implementation's
  reading of the Constitution's questions, not definitions from it.
- `docs/RecommendationReport.md` specifies that a category shows coverage,
  confidence, summary, drivers and warnings. Only the first three exist.

---

## Market must describe the asset's own environment

Market currently reports the broad market's change over a year, and every asset
therefore reports the same thing. NVDA, HSBC and RKLB sit in different
environments — semiconductors, banks, space — and a report that says the same
sentence about all three is not telling an investor anything about the asset.

The broad index is one piece of evidence, not the answer. Market should describe
the environment this particular asset is being judged in: its industry, its
sector, the money flowing through it, the prevailing style, and the macro
backdrop.

Not built today because the evidence is not connected. Naming an industry by
inference from a ticker would be guessing, and stating an environment AIS cannot
see would be worse than saying nothing.

---

## Runtime, after the report is settled

Three notification behaviours are agreed and not built:

- **Daily report**, every day at 21:00 Beijing time, whether or not anything
  changed. This is the point of v1: one report a day that can carry a decision.
- **Weekly report**, Saturdays at 12:00 Beijing time.
- **Event alert**, sent as it happens, triggered by a change rather than a price:
  the decision changed, the thesis changed, or a category changed materially
  even when the decision did not. The message must state why it interrupted —
  "Reason: Valuation improved significantly." — and never just "AIS Update".

The material-change trigger needs a threshold for what counts as material. Every
threshold is deferred with the AIS Standard Score, so this one will be
provisional, configurable, and labelled as such.

A single combined daily message would be a new report structure. The report model
currently describes one asset, and adding a digest is a decision for that review.

---

## Portfolio Layer — how much

Not built, and not to be built before the review that follows the nine
categories. It answers a fourth question AIS does not answer today: **How much?**

It will need, at minimum:

- **Initial allocation** — the size of a first position.
- **Maximum allocation** — the largest position this asset may ever take.
- **Scale-in conditions** — what would justify adding.
- **Scale-out conditions** — what would justify reducing.
- **Opportunity cost** — why this asset rather than another one today.

Opportunity cost belongs to this layer rather than to Risk or Positioning: it is
a question about the alternatives available, not about the asset. HPO states
whether an opportunity is worth allocating to; only this layer can say whether it
is a better use of capital than something else.

It is deferred because it cannot be answered in the abstract. It needs a
portfolio: live positions, cash, sector exposure and the other opportunities
available. The intended input is an IBKR connection, and building the layer
before that exists would mean inventing the portfolio it is supposed to read.

The risk philosophy for this layer is already agreed and recorded here so it is
not lost: a recommendation must not simply follow the opportunity judgement.
Extreme risk has veto capability — a high opportunity with extreme risk is a
reason to wait, not to buy. Nothing of this is implemented, and it belongs to the
review.

---

## The overall score is being retired

`OverallEvaluator` combines every category score into one number on a scale that
is not defined, and it currently treats a larger reading as favourable in every
category. The daily report does not show it, and no new feature may depend on it.

It is not deleted yet, because the recommendation still reads the overall
assessment. Removing it means deciding what the recommendation reads instead,
which is a chain change and belongs to the review after the nine categories.

---

## Catalyst: what is connected, and what is not

Catalyst reads three sources today:

| Layer | Source | State |
| --- | --- | --- |
| Company | Market data vendor calendar | Results date, ex-dividend date, dividend date. |
| Macro | Federal Reserve published schedule | Policy meeting dates, read from the published page. |
| Industry | **None** | Nothing is connected, so the layer reports that it has nothing. |
| Company (other) | Curated file, `data/calendar/events.json` | Launch windows, product launches, regulatory dates, investor days — entered by hand, currently empty. |

**What is missing, and why it is not filled in.** Product launches, rocket launch
windows, FDA decisions, shareholder meetings, industry policy, competition news,
CPI, payrolls and GDP have no connected source. AIS will not infer a date, and it
will not summarise news to produce one. Each is named as not covered wherever it
would have appeared.

**What would close the gap.** A calendar source per layer: an economic calendar
for the macro releases, an industry or regulatory feed, and a company events feed
beyond the market data vendor's own calendar. Each is a provider behind
`CatalystEventProvider`, which is why none of them needs a change to the
evaluator.

**The curated file needs a person.** It is the only place an unscheduled event
can enter AIS. It ships empty and stays empty until somebody enters something
they can point at. See `data/calendar/README.md`.

**The Federal Reserve source reads a page written for people.** It is guarded to
fail empty rather than wrong: if the markup changes, AIS records no macro events
and says so, instead of publishing dates it cannot stand behind. A structured
feed would be better and none exists.

---

## Catalyst: deferred by decision

These are not gaps. They are things AIS has decided not to do, recorded so that
the decision is not rediscovered as an oversight:

- **Real-time news analysis.** AIS does not report what happened today.
- **LLM news summarisation.** A summary is an opinion with no evidence behind it,
  and it would be indistinguishable in the report from a stated fact.
- **News sentiment scoring.** Sentiment is not evidence about an investment case
  until somebody defines what it is evidence *of*.
- **Learned importance ranking.** A model that ranks which events matter would be
  unauditable, and the ranking would be trusted exactly as much as it looked
  reasonable.

What AIS does instead is smaller and checkable: it reports events a source
published, says what layer each bears on, and says why that kind of event
matters. That reason is a property of the kind, never of the instance.

---

## The insight layer: what it cannot say yet

Every category now interprets its own evidence. These are the interpretations it
cannot honestly produce today, and what each one is waiting for.

| Not said | Why not |
| --- | --- |
| Market regime and style | Only the broad market's yearly change is connected. Risk appetite, growth versus value and rotation need index and sector data. |
| Industry position and competition | No industry source exists. A company's place in its market cannot be read off its own figures. |
| Where the growth is coming from | Segment and product revenue do not exist in the data. A growth rate without its source is one number. |
| Whether a valuation is fair for the sector | Judging a multiple needs the multiples of comparable businesses, and AIS compares one asset at a time. |
| Whether the holders are changing | Only the current register is known; institutional and insider *changes* need a second observation over time. |
| Liquidity and execution | Average volume is known; spread, depth and the cost of building a position are not. |
| What the price has already discounted | This needs an estimate of expectations, which is the deferred standard score's job. |

None of these is filled in by inference. A category that cannot say something
says less, and the report names what it did not cover.

**The insight layer itself needs a review point.** The rules behind each sentence
are conventional thresholds — a 30% margin reads strong, a 45% volatility reads
high — and they live beside the code that uses them. They are the same kind of
provisional presentation as the grade bands, and they are to be revisited
together with it, once the AIS Standard Score defines what a reading means.

---

## Declined by decision, recorded so it is not rediscovered

These are not waiting for data. They are things AIS has decided not to do:

- **LLM news summarisation.** A summary is an opinion with no evidence behind it,
  and in a report it is indistinguishable from a stated fact.
- **AI-written research reports.** Prose generated to sound like analysis is
  analysis nobody can check. Every sentence AIS writes comes from a rule that can
  be pointed at.
- **Forecasts.** No prediction of prices, no expected returns.
- **Target prices.** A target price is a forecast with a number attached, and the
  number makes it look more considered than it is.
- **Probabilities.** AIS cannot estimate the likelihood of an event moving a
  price, and a number that looked like an estimate would be used as one.
- **News sentiment, learned importance ranking.** Recorded above; both need
  something AIS has decided it cannot stand behind.

---

## Registered blockers

- **AIS Standard Score direction.** Recorded in `docs/Constitution.md`. Until the
  scale exists, scores are raw measurements averaged together, and different
  categories measure in opposite directions: a larger risk measurement currently
  raises the overall score rather than lowering it. Not worked around, because
  inverting or weighting to compensate would be inventing the scale.

- **HPO condition thresholds.** HPO decides its named conditions from the
  provisional grade of each category, so it inherits that grade's provisionality.
  The thresholds are stated openly in the code and are to be re-derived once the
  standard score defines what a category reading means. They are not to be tuned
  in the meantime: tuning them would make a presentation band look like a
  methodology.

- **The positioning score mixes holdings and days.** The Positioning category
  score is the mean of four readings on different scales, and the days-to-cover
  reading dominates it numerically. Direction is read as "lower is better", which
  is right for crowding and wrong for holdings. This is the standard-score
  blocker showing through a single category, and it is recorded rather than
  patched.

- **Catalyst can never report complete coverage.** One of its layers — industry
  events — has no connected source by construction, so the category always
  reports partial coverage and always names what it could not see.

- **A layer with no events counts as a layer not looked at.** Coverage counts the
  layers that produced an event, which conflates "nothing is scheduled" with
  "nothing is connected". Telling those apart needs each source to report the
  reach it has, and that is deferred.

- **The movement arrows are a presentation decision.** Whether ▲ means "the
  measurement rose" or "the category improved" has no answer on an undefined
  scale. The report currently shows improvement, which means valuation and risk
  are inverted relative to their raw scores, and catalyst and positioning are
  read as "nearer" and "less crowded". Nothing about the stored score is changed
  by this. When the standard score defines direction, the presentation must
  follow it rather than decide it.

---

End of Backlog
