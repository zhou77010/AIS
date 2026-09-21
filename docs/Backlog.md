# AIS Backlog

Deferred work, recorded so it is not lost and not repeated. Nothing here blocks
current development.

This is a list of pending items, not an authoritative document. Meaning lives in
`docs/Constitution.md`, available evidence lives in `docs/EvidenceSurvey.md`, and
structure lives in `docs/Architecture.md`.

---

## Confirmed development order

Agreed direction, in order:

| Phase | Work | Depends on |
| --- | --- | --- |
| **A** | **Reading Layer** — one owner for what a reading means, so the grade, the insights and HPO stop disagreeing. | Nothing. Highest priority. |
| **B** | **Watch Universe** — membership sets, replacing the flat ticker list. | A. |
| **C** | **Market Layer** — what the current environment means for this stock. | New evidence (industry, style, flows). Shares its data with the Theme watchlist. |
| **D** | **Runtime** — the three triggers: Pre-Market Brief, Live Morning Brief, and the intraday alert with its runtime priority. | **C** for the environment half, which is done; the Pre-Market Brief also needs the **Company Layer**, and that is the work that is open. |
| **E** | **IBKR Portfolio Layer** — the fourth question, how much. | An IBKR connection. |

The journal records why A comes before B even though B looks cheaper, and why the
Brief could not be built before the Market Layer: without market-level evidence it is
the same analysis sent at a different hour. The half of that which is still missing is
the Company Layer — per-asset pre-market prices, overnight news and realised macro
results — which is what the 21:00 report waits for now.

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

**Partly built.** Market used to report the broad market's change over a year, and
every asset therefore reported the same thing. The first market-level evidence is now
connected, and the category answers a question about the asset: what the environment
means for this one.

### What is connected, and where it goes

The environment is a separate input from the asset's own market data, because it is
not about an asset: the equity futures, the volatility index and the ten year yield
are the same facts for every asset in the market. It is retrieved **once per pass** and
shared, filed as evidence under the **Market** category like everything else, and read
through the same reading layer. Its evidence identifiers carry no ticker, which is how
a reader can tell a shared fact from one of the asset's own.

| Measurement | Source | What it answers |
| --- | --- | --- |
| S&P 500 futures since the last close | `ES=F` | Is risk being taken right now |
| Nasdaq 100 futures since the last close | `NQ=F` | Which end of the market it is being taken in |
| Volatility index level | `^VIX` | How turbulent the conditions are |
| Volatility index change | `^VIX` | Whether they are settling or deteriorating |
| Ten year yield change, in basis points | **United States Treasury** | Which way the cost of money is going |
| The ten year less the two year, in basis points | **United States Treasury** | The shape of the curve, and whether it is inverted |
| The same spread's change, in basis points | **United States Treasury** | Whether the curve is steepening or flattening |
| The asset's own sector against the market | the sector instruments | Is the part of the market this asset is in being bought |

**Rates have one authority: the Treasury's own daily curve.** The vendor quotes a ten
year yield too, and it is deliberately not read — not as a fallback either. Two
slightly different ten year yields in one report are two versions of one fact, and a
reader has no way to tell which one a sentence was written from. The composite refuses
to carry one measurement twice, so the rule is enforced rather than remembered, and a
source that cannot answer leaves a gap saying rates could not be read rather than a
number from somewhere else.

**And one definition of the curve.** The file carries the three month bill as well as
the two year, and AIS reads the ten year less the two year, which is what the market
quotes as "the curve". Holding both spreads would be the same defect as holding two ten
year yields: one concept, two versions.

**What the curve let the report say, and what it replaced.** The sentence about a
financial used to end by admitting the direction could not be judged, because a bank's
margin moves with the shape of the curve and only one yield was connected. It now says
which way the margin environment is moving, and names an inverted curve whether or not
it moved that day.

**The sector is measured against the market and never on its own.** "Technology moved
1%" says nothing when the market moved 0.9%; what a reader holding a technology
company needs is the difference, so that is the number, computed over one session and
reported as one value. Only the sectors the watch universe is actually in are read —
six for the current seven assets, not eleven — because a pass should cost what the
universe costs.

**Which sector an asset is in is stated, not inferred.** It is declared in the
watchlist beside the profile, for the same reason the profile is: it decides which
comparison AIS makes and therefore which sentence it can write, and a guessed label
changes what AIS is able to say without the change being visible in the output. The
vendor does publish a sector for most symbols and it was used to fill the current
entries in, but the file is where it lives, because a file that states a fact can be
corrected by a person and a vendor's taxonomy cannot be argued with. An asset with no
stated sector — an exchange-traded fund holds a style rather than a sector — is told
nothing about one.

**A relative move is not a flow.** Where a sector is trading against the market is
consistent with money moving in or out of it, and it is not a flow figure: AIS states
the comparison and never claims the flow.

The aspects of the environment question did not change when the evidence arrived:
**direction**, **risk appetite**, **volatility** and **rates** are the same four the
category already declared, two of which were listed as unmeasured so that the gap was
visible in the report. Coverage now reads 4 of 4 on a live run, and a placeholder —
which is what a run with no source produces — no longer counts as an examined aspect.

### How the sentence is built

Market's first sentence is about **this asset**, because that is the sentence a phone
shows. It is read from a pair: an environment measurement and one of the asset's own,
in the same sentence, with both named in its references.

| Exposure | Read from | Sentence |
| --- | --- | --- |
| The asset's own sector | the sector's move against the market, and the stated sector | 所属板块（科技）跑输大盘，本标的短期承压。 |
| A weak tape against a high beta | overnight tape, volatility change, beta | 盘前走弱、波动抬升，本标的贝塔偏高，波动可能放大。 |
| A weak tape against a low beta | the same, on the other side of the beta scale | 盘前走弱，本标的贝塔很低，相对抗跌。 |
| Rising rates against a dear valuation | yield change, P/E, EV/EBITDA, cash flow yield | 利率上行而估值很贵，分母端承压。 |
| Growth lagging for a growth company | the two futures, the declared profile | 成长风格弱于大盘，本标的属成长型，短期相对承压。 |
| Rates moving, for a financial | yield change, the declared profile | 利率上行，本标的属金融机构，息差与资产质量直接受利率影响，方向还需要收益率曲线的形状，目前判断不了。 |

The environment itself is the **second** sentence, and the brief states it once for the
whole universe at the top, before any asset: 市场环境 盘前偏强、成长股领先、波动平静、
利率上行，环境对风险资产偏友好。

The sector sentence comes first, because it is the most specific thing the environment
can say about a holding, and it is graded rather than described: where the asset's own
part of the market is going is a condition of the environment it is judged in, so two
assets in different sectors get different Market grades and that is correct.

**Two of the five environment measurements are described and never graded.** Risk
appetite and volatility are graded, because a tape being bought and a market that is
calm are favourable conditions for owning risk and the direction scale already grades
exactly that. Rates and the change in volatility are not: a rise in the cost of money
is not better or worse in itself, and it is not worse for a bank than for a software
company until an asset is named. Nothing else was invented to fill the gap.

### What is still not connected

This round filled the gaps in the order they change a judgement, and stopped where the
next one stops being worth what it costs. Priority one was the industry the asset is in
and the style the market is paying for, and that is built. The other two are recorded
with what was found about them.

| Input | State |
| --- | --- |
| The asset's own sector | **Connected.** The sector's move against the market, once per sector the universe is in. |
| Market style | **Partly connected.** Growth against the broad market, read from the two index futures. A value and growth pair of sector instruments would say it in the same asset class rather than across two, and is not connected. |
| The shape of the yield curve | **Connected.** Ten year less two year, level and change, from the Treasury's own daily file. The three month bill is published beside it and is not read: two definitions of "the curve" would be the same defect as two ten year yields. |
| Realised macro releases — CPI, payrolls, growth readings | **Not connected, and there is no source AIS can read.** The vendor publishes no economic calendar, and the central bank provider publishes meeting dates that are still ahead: it was checked, and its next event is a month away with nothing behind it. So "what the important overnight release said" is not obtainable today, and the market's own response to it is what the futures, volatility and yields already record. |
| Industry environment — policy, competition, cycle | Not connected. Named as a gap in the report. |
| Flows — where money is actually moving | Not connected. The sector's relative move is a proxy and is stated as a comparison, never as a flow. |
| Currency — what the dollar is doing to a company | **Declared out of reach.** The dollar's move is retrievable, but AIS does not know where any asset earns its revenue, so it cannot state an effect. Describing the move without an effect would be a fact with no consequence in a category that exists to state consequences. |

**Market's question is "what does the current environment mean for this stock"**, and
it now answers about the asset in four ways: the part of the market it is in, the tape
against its own beta, what the cost of money does to what it costs, and which kind of
business is in or out of favour. What it still cannot do is say what is happening
*inside* an industry rather than to its price, and it says so rather than guessing.

**The boundary with Catalyst still holds.** Catalyst lists what is coming; Market
explains what the environment means and what has already happened to it. A separate
market brief section was not created, and the environment's one user-visible line is a
line of the brief rather than a section of it.

**The environment does not reach the opportunity judgement.** HPO reads five named
conditions and Market is not one of them, so a hostile environment does not by itself
lower an asset's opportunity count. Whether it should is a Constitution-level question
about which categories HPO reads, and it is not decided here.

---

## Company Layer — what is connected, and what it is not

**The phase that is open.** Everything AIS has read per asset has been about the asset
as a thing to value: what it costs, what it earns, how the price has behaved. Two facts
about the company *itself*, as of now, are connected in this round, and they are the
first of the layer the 21:00 report and half the Report Model have been waiting for.

| Fact | State | Where it comes from |
| --- | --- | --- |
| **The move price made before the session opened** | **Connected.** The premarket price against the previous close, one number, read as a band and written into a sentence. | The vendor's quote summary, `price` module. Both legs are named in the evidence reason, so the size of the move can be checked against the two prices it came from. |
| **What the last report did against what was expected of it** | **Connected.** The most recent reported quarter's surprise, read as a band and written into a sentence. The quarters before it are logged and never read. | The vendor's quote summary, `earningsHistory` module. One source carries both the reported figure and the estimate it was held to, so the surprise cannot be a comparison between two authors. |
| **What the company said about its own next quarter** | **Not connected, and it is not obtainable.** Recorded as absent, with the reason, in the evidence for every asset. | Nothing AIS reads publishes it. What is published is what analysts expect, which is a different fact about a different author. |
| **Premarket volume** | **Not connected.** Deferred as P1.5, and it may never be obtainable from this source. | The quote summary publishes no premarket volume at all, and the intraday chart returns premarket bars with their volume reported as zero — measured against the live endpoints, not assumed. Connecting it would cost one extra request per asset per pass for a number that currently arrives empty. |
| **Company news** | **Deferred by decision.** The quality of the free headline feed is far below that of a reported result or a traded price. | — |
| **Insider transactions and buybacks** | **Deferred to P2.** Low frequency, high explanatory value, low immediacy. | The vendor's share purchase activity, and the filings themselves. |

### New evidence is connected before it is trusted

**Both facts arrive described and not graded**, and that is the whole of the design rather
than an unfinished part of it. They are filed under the category whose question they
answer, they are read against a scale in the reading layer, and they are written into the
report's sentences. They carry no score, so they do not move a category's mean, do not
meet or fail an opportunity condition, and do not reorder the brief.

**Why it stops there.** A graded measurement does not only appear in the report: it enters
its category's mean, and a grade that moved is a change, and a change is what makes an
asset lead the brief. Grading is therefore a change to what AIS concludes, and a
conclusion changed by connecting a data source is exactly the kind of change that would
never be reviewed. So the promotion is its own decision, taken once real runs have shown
what the measurement reads as — whether its bands separate anything, whether a month of
values has ever left the middle of the scale.

**What is deliberately not done to force the effect.** No measurement is weighted, given
an extra score, or sorted on in the brief because it seems important. The order of the
brief is decided by the table it was always decided by, and a fact that should change it
earns that by being graded through the reading layer, with a scale somebody approved.

### What the two facts change, and what they do not

| | Now | After a promotion decision |
| --- | --- | --- |
| The evidence stream | Carried, with the reason it was retrieved or why it is missing | unchanged |
| The category reading | Read, with a word and no score | Same reading, now with a score |
| The report's sentences | Said, with the size and the band's own words | unchanged |
| The category's grade | **Unchanged** | Would move with the reading |
| The opportunity conditions | **Cannot be read from either category** — the four measured conditions and the catalyst window are the same five they were | Would move only if the category is one a condition reads, which is a separate decision |
| The order of the brief | **Unchanged** | Would move, because a grade that moved is a change |

**The gap that this leaves, stated rather than hidden.** Neither fact can change Today
Priority yet. That is the price of connecting evidence without concluding from it, and it
is paid deliberately: the alternative was to grade a scale nobody has looked at a real
month of, which would have decided what a premarket move is worth on the day the field
was first read.

---

## Reading Layer — done, and it is now one layer

**Completed.** The conventions AIS uses to read its own numbers were written down in
three places that did not know about each other, and they disagreed in public:

- HPO said **"有近期催化"** while the catalyst block said **"近期暂无明确催化"** — the
  condition counted ninety days as near, the sentence counted thirty.
- HPO said **"估值具备吸引力"** beside a valuation insight saying **"自由现金流为负，
  估值缺少现金收益支撑"** — the condition read a rounded star, the sentence read the
  measurements.

There is one owner now, `evaluation/reading/`:

| Module | What it owns |
| --- | --- |
| `bands.py` | One scale per measurement: the direction it runs, where its bands fall, the word each band is called, and the score its position carries. |
| `windows.py` | The time windows, so "near term" means one thing wherever it is said. |
| `category.py` | What a category's measurements mean together — the mean and the weakest reading. |
| `conditions.py` | The bar each opportunity condition is decided at. |

The grade is a view of the reading (`analysis/category_grade.py` holds no threshold
of its own), the sentences read the bands rather than numbers of their own, and HPO
reads a reading rather than a rounded star. The revised catalyst condition and the
weakest-reading bar closed both known contradictions, and
`tests/test_report_consistency.py` now checks a rendered report for new ones.

**What is unified, and what is still provisional.** The *rules* are unified: one
place decides what a number means, and moving a threshold moves everything that
reads it. The *values* are as provisional as they were — conventional rules of
thumb, not the AIS Standard Score, replaced as a whole when it exists. Two things
remain outside the layer and are recorded rather than hidden:

- **The lookback windows themselves** — a 120 day average, a 20 day volatility, a
  14 day RSI — are implementation choices in the Data layer, not readings. If they
  change, the bands they feed should be checked with them.
- **The wording of a sentence is still chosen by the sentence.** A builder decides
  which clause to write; the reading layer only decides what the reading is called.
  A clause can therefore still be keyed to the wrong band, which is what the
  consistency test exists to catch.

**A consequence worth knowing.** The bars are stricter than they were, because a
condition now needs the category to read well *and* to hold nothing in the bottom
two bands. Measured across the seven watched assets, HPO reads 1 for six of them
and 3 for the seventh. That is the honest output of the conditions as stated — an
attractive valuation, a trend with nothing weak in it, a catalyst inside a month
and an acceptable balance sheet are all demanding — but it is worth deciding
whether that is the intended shape before the report is read by anybody else.

---

## Report first impression and density — done, and now enforced

**Completed.** The report is a projection with three asserted budgets: 32 lines,
42 columns, and the first 20 lines answering the whole question — which stock,
whether it is worth attention, what to do, what changed, what to watch. Measured
across the seven watched assets: 23–29 lines, and no line over 42 columns. What
the phone leaves out is in the expanded report that `generate_report` writes.

**What is not finished about it.** The budgets are asserted against four
representative shapes rather than against every possible input, so a shape nobody
thought of could still exceed them. Width is the only budget that holds
universally, because it is enforced line by line as the text is written.

**A trade that was made deliberately.** The sub-dimensional gaps — the risk
dimensions that were not assessed, the measurements that could not be retrieved —
now appear only in the expanded report, which a reader sees only in the log. That
is what the density rule asks for, and it is recorded here so that it stays a
decision rather than becoming a surprise later. Putting them back on a phone is a
new feature, and it would have to earn its lines.

---

## Watch Universe — membership sets, not tiers

**Built.** The universe is configuration; the monitor that reads it is not, and the
two are deliberately decoupled.

| Built | Where |
| --- | --- |
| The sets, an entry, and the collection with its lookups. | `models/watch_universe.py` |
| Reading a watchlist, validating it, and the fallback. | `config/watchlist.py` |
| The path, on `AIS_WATCHLIST`. | `config/config.py` |
| The universe deciding what is evaluated, and supplying each asset's identity. | `app/application.py` |
| The watchlist AIS runs on today, with real names, exchanges and profiles. | `config/watchlist.json` |

**The fallback.** A watchlist wins when it can be used. When it is absent, empty or
unusable the configured tickers are used instead, as a universe whose only set is
the core watchlist — which is what a watchlist listing the same symbols would
produce. `AIS_TICKER` is therefore still the way to run without a file, and the
change that introduced the file did not make any watched asset disappear.

**`AssetProfile` is live.** It was declared, carried through the model, and never
set: `Application._asset` built every asset as unknown. The watchlist states the
kind, and the kind now reaches the analyzer. A profile that cannot be recognised is
left unknown rather than guessed, because a guess about the kind of an asset
silently changes what AIS is able to say about it.

**A gap the enum has.** `AssetProfile` has no member for a consumer staples
business, so MNST is honestly left unknown. Adding one is a small change with a
real decision behind it — what different treatment the kind implies — and it belongs
with the work below rather than with the file.

**Tiers were rejected.** A tier is an ordered, exclusive thing, and what AIS
actually has is membership: NVDA is in the M7, in AI and in Semiconductor at the
same time, and asking which tier it is in is a question with no good answer.
Every later operation — what the daily report shows, what the intraday scan
considers, what gets pushed — would have had to invent its own answer.

Membership sets, all of them unordered and allowed to overlap:

```
Watch Universe
  Portfolio
  Core Watchlist
  Growth Watchlist
  Theme Watchlist
  Temporary Watchlist
```

**A Theme is an investment logic, not a list of stocks.** AIS holds
`Theme → representative assets` — AI points at NVDA, AMD, AVGO, MSFT; Space at
RKLB, LUNR. A theme is never itself a report object; what changes about a theme
reaches the reader through its representative assets.

**The Theme watchlist must be derived, not listed.** If themes are maintained as
`Theme → assets`, then the Theme watchlist is their union. Writing it twice — once
as the mapping and once as a list of members — is how the two drift apart.

### Five sets, and only three of them are configuration

This is the boundary that keeps the universe from arguing with the portfolio and
with the runtime. The five sets are one concept, but their members come from three
different places, and only one of those places is a file.

| Set | Where its members come from | Written in the file |
| --- | --- | --- |
| Portfolio | The Portfolio Layer, from the broker. Phase E. | **No** |
| Core Watchlist | Configuration. | Yes |
| Growth Watchlist | Configuration. | Yes |
| Theme Watchlist | Derived from `Theme → representative assets`. | **No** |
| Temporary Watchlist | Added and expired by the runtime, from the calendar. | **No** |

**Portfolio is a fact, not a choice.** Whether AIS holds something is decided by a
broker, not by a person editing a file. If the file could say `"portfolio": true`,
the configuration would start asserting a position before there was anything to
assert it from, and nothing would ever correct it — the file would quietly become a
second, wrong portfolio. Until the Portfolio Layer exists, the Portfolio set is
empty, and being empty is the truth.

**Temporary is a result, not a choice.** Its members are put there by the calendar
and removed when the event passes, which is the runtime's job. A hand-written
temporary list would be a list nobody removes from.

So the file carries three things and nothing else: the core members, the growth
members, and the theme mapping.

**A set is a relation, not an attribute.** An asset does not have a set; it belongs
to some. So the model holds one entry per asset carrying the sets it belongs to,
and the same symbol may not appear twice — two entries for one symbol would be two
copies of its name, exchange, currency and profile, and the two could disagree.

### Confirmed boundaries

| Question | Answer |
| --- | --- |
| Tiers or sets? | **Sets.** Unordered and overlapping. |
| Is the Theme watchlist maintained? | **No, derived** from the theme mapping. |
| Where does the loader live? | **`config/`** — a watchlist is AIS's own configuration and not data collected from the world. |
| Is Portfolio a set in the file? | **No.** It comes from the Portfolio Layer. |
| Is Temporary a set in the file? | **No.** The runtime fills it. |
| Does the universe decide when things run? | **No.** Scanning frequency, per-set polling and push priority are the runtime's, and are deferred. |
| Does it enter the judgement chain? | **No.** It decides what is looked at, never what is concluded. |

### What would have to change

| Module | Change | Size |
| --- | --- | --- |
| `models/watch_universe.py` | New: the sets, an entry, and the collection with the lookups over it. | Small, additive |
| `config/watchlist.py` | New: reads the file, validates it, returns the model. | Small |
| `utils/constants.py` | One environment variable for the file path. | One line |
| `config/config.py` | The path, the same way the curated catalyst calendar has one. | One field |
| `app/application.py` | Iterates the universe instead of `config.tickers`, and stops inventing asset metadata. | Small |
| Everything else | **Nothing.** Evaluators, pipeline, report model, contracts and scheduler are untouched. | — |

That last row held when the work was done: **membership is configuration and
orchestration, and it does not enter the judgement chain.**

**What is still not built, and whose job it is:**

| Set | Filled by | When |
| --- | --- | --- |
| Portfolio | The Portfolio Layer, from the broker. | Phase E |
| Temporary | The runtime, from the calendar. | Phase D |
| Theme | It is derived once the file carries a `themes` mapping. The file ships with an empty mapping, so the set is empty because nobody has stated a theme yet — not because anything is missing. | Any time |

**Not this phase either.** The daily report sends one message per asset, so a
universe of forty names is forty pushes a day. A digest is a **report model**
change — the backlog records that "a single combined daily message would be a new
report structure" — and it has to be decided before the universe grows much beyond
what it is now.

---

## Priority — a runtime result, not configuration and not analysis

**Confirmed as future design. Not built.**

The intraday engine's question is not which set an asset belongs to. It is:

> Is this worth interrupting the user for, right now?

Priority answers it on five levels — `CRITICAL`, `HIGH`, `NORMAL`, `LOW`,
`IGNORE` — and it is **computed at runtime from state, never configured**.

**It cannot live in the analysis chain**, and the reason is not that it is
produced late. It is that the inputs it needs are not there. "Relevance" means how
much this matters *to this user*: what they already hold, what they have already
been told today, how many times they have been interrupted. `AssetAnalyzer`
evaluates one asset at a time, with no portfolio, no history and no sight of any
other asset. Computing Priority inside it would force the analysis layer to read
runtime state, which is what Architecture rules 8 and 11 forbid.

So Priority belongs to the runtime, and its inputs are **an analysis result plus
runtime context**. Two consequences to hold on to:

- **It is not a tenth category and it does not feed HPO.** If it entered the
  chain it would put a scale nobody has defined into the chain itself, which is
  the blocker the Constitution already records.
- **What it needs does not exist yet**: a cross-asset view, thresholds, and a
  record of what the user has already been told. Its impact input also wants the
  environment evidence that Market and the themes are waiting for.

**A document will be needed at that point, and not before.** Every principle AIS
has written describes *the report* — something a reader chooses to open. An alert
is a different surface: it interrupts, and it has to be worth interrupting for.
What makes an interruption legitimate is a product question nobody has answered
yet, so it is recorded here rather than written into
`docs/ProductPrinciples.md`.

---

## Runtime — three triggers, three times

**The 09:00 brief is built.** The other two are defined and are not.

| Trigger | State | Where |
| --- | --- | --- |
| **Live Morning Brief** — 09:00 Beijing | **Built** | `app/morning_brief.py`, scheduled by `app/scheduler.py` |
| **Pre-Market Brief** — 21:00 Beijing | Defined, **not implemented and not scheduled**; the Environment layer it needs is complete and the Company Layer is not | — |
| **Intraday Alert** | Defined, not built | — |

**How it is built.** The scheduler no longer runs one cycle on an interval. It runs
**schedules**, each of which answers "when am I next owed", and sleeps to the
earliest answer. Two are wired: the evaluation cycle on its interval, and the brief
at an hour of the day. Adding 21:00 later is another schedule and nothing else.

### Nothing fires at 21:00, and a missing report there is not a fault
**Two schedules exist: `cycle` and `morning-brief`.** Those two are what
`app/application.py` registers and there are no others; the scheduler sleeps to the
earliest moment either of them is owed. **The 21:00 Pre-Market Brief is defined and
not implemented** — there is no schedule for it, so nothing wakes at that hour and no
message is owed.

**A report that never arrives at 21:00 is the recorded state of the system, not a
bug.** It is not the scheduler failing to wake, not the state file holding a day it
should not, not the notifier dropping a message, and not the market gate refusing at
that hour. A report cannot be missing when none was ever scheduled: the absence has
exactly one cause, and it is this paragraph. Read it before looking anywhere else, and
before believing that 21:00 was ever built.

**What "built" would require, so that its absence is checkable.** A schedule with its
own id, its own runtime-state key, its own attempts and its own delivery state. A
report shares none of those with the morning brief: two reports sharing one state
record would each read the other's day as their own, and would then either send a
second copy or stay silent, which is the failure the state record exists to prevent.
The state file is already shaped for that — one bucket per report under `reports` —
and no second report is written into it.

**It arrives as one message.** The brief covers the whole watch universe and is
delivered as a single digest; see "The brief is one message" below. The evaluation
cycle is unchanged and still sends one message per asset whose conclusion moved,
because that message is news about one asset rather than a report over all of them.

**What the brief does not consult.** It does not consult the market clock, because
the hour it is owed at falls outside the United States session by definition and a
report that waits for a market to open never arrives at the hour it was asked for.
It does not consult the change detector, because it is expected: "nothing has
changed" is what most days look like, not a reason to say nothing. And it is
computed at the hour it is sent, so there is no earlier result delivered late.

**What it remembers is a state, not a flag.** `state/runtime.json` holds, under
`reports`, one bucket per report, and in each bucket **where that report's day
stands**: `owed`, `sent` or `abandoned`, how many times it has been attempted, and when
the last attempt was. It is written by replacement, so a process killed mid-write
leaves the previous state intact, and it is read at startup, so a restart neither
repeats a report nor loses one. `AIS_STATE_FILE` moves the file; the path is in the
configuration like every other path. The day is a field of the record rather than a key
of its own, so a record about yesterday says nothing about today. Two earlier shapes
are still read: the record written at the top level of the file under the report's
name, and before that the single key naming the day the brief was sent. Both name a day
the runtime recorded, and forgetting either would send the reader a second copy.

**One bucket per report is the whole of the multi-report design.** A report is any
message the runtime owes on a schedule, and each one has its own day, its own attempts
and its own delivery state. Two reports sharing a bucket would each read the other's
day as their own and would then either send a second copy or stay silent, and neither
is visible from outside. The morning brief is the only report there is; the pre-market
brief gets a bucket of its own when it exists, and the file already has the shape for
it. What a report is *named* in the state file is its own identity and not the
scheduler's: the scheduler logs a job, the state file holds a bucket.

**Why a state rather than a flag.** "A brief was sent at some point" cannot tell a
brief that reached a reader from one that reached nobody, and that difference is the
whole question. See the delivery policy below.

**A delivery that reached nobody is not a delivery.** An attempt ends one of two ways.
If at least one channel carried the message the day is **sent**, and nothing more is
owed. If every channel failed — the message reached nobody at all — the day stays
**owed**, and it is tried again.

**A partial failure is not a failure.** A channel that fails while another delivers is
a degraded delivery, not a missing one. Resending it would send a second copy to
whoever the first attempt reached, which is the outcome the original rule existed to
prevent, so only a delivery that reached nobody leaves anything owed.

**A retry is spaced and capped.** It is spaced by 30 minutes, because the hour the
brief was owed at is already behind and an attempt that failed would otherwise be
immediately due again — a loop costing a full analysis of the universe each time round.
It is capped at three attempts, because a report the reader opened the morning for
stops being that report if it arrives at noon, and because an outage that does not end
must not keep the runtime busy until midnight. An abandoned day is logged as an error;
the reader is not told, because the channel that would tell them is the one that just
failed.

**This was decided from a real failure.** The log shows the brief firing at 09:00 on
three consecutive days and delivering nothing: the machine had no route to the network
at that hour, both the market data source and the notification channel were refused,
and every asset was reported as failed. The trigger was right every day and the reader
has still never received a brief. The rule that a failure is not retried was written for
a partial failure; a total one had no rule at all, and recording the day as sent spent
the whole report on an outage that lasted a minute.

### Only one of the two scheduled reports is active, and it is the morning one

**Confirmed.** **Only the 09:00 Live Morning Brief runs.** The 21:00 Pre-Market Brief
stays defined and stays off, and what it is waiting for is the Company Layer rather
than the Market one — see "The gap at 21:00 is one layer wide" below.

The reason it is off is not caution, it is that the two would be the same report. AIS
reads per-asset evidence — a quote summary and a year of daily bars — and that evidence
changes about once per trading day. At 09:00 Beijing the latest completed US session
is D-1 and the latest daily bar is D-1's; at 21:00 Beijing the session has not opened
yet, so the latest completed session is **still D-1** and the bar is the same bar.
Same evidence, same readings, same sentences, same conclusion.

Two scheduled reports on one piece of evidence is not two reports. It is one report
sent twice, with the second copy arriving when the reader has already read the first
— and if the source happens to tick a price in between, the second copy will report
that tick as though it were news.

**What makes 21:00 a report of its own is Phase C.** A pre-market brief answers what
changed overnight: pre-market prices, futures, volatility, yields, the dollar, the
morning's macro releases, overnight news. **Futures, volatility, yields and the curve
are now connected** — they are what the Market category reads and what the 09:00 brief
leads with — and the rest is not: there are no pre-market prices per asset, no realised
macro releases and no overnight news.

**The gap at 21:00 is one layer wide, and it is the Company Layer.** This is the
sentence to keep, because the wrong one has been written twice: 21:00 is not
"not worth doing" and it is not "waiting for the Market Layer". The Market Layer is
**done**. What is missing is the layer under it:

| Layer | State at 21:00 today |
| --- | --- |
| **Environment** | **Complete** — futures, volatility, yields and the curve are retrieved once per pass, shared across assets, and read beside each one |
| **Company premarket** | **Unavailable** — there is no per-asset pre-market price, so the newest per-asset fact is still the previous session's close |
| **News** | **Unavailable** — no overnight news is read, and no macro release is read as a realised result |

**So the report is buildable and would be thin, and it is off until it is not.** The
order of work, and nothing else, is:

| # | Work | Ends with |
| --- | --- | --- |
| **P1** | Build the **21:00 Pre-Market Brief** as its own schedule and its own state, labelled for what it holds: **Environment complete / Company premarket unavailable / News unavailable**. It states which of its three layers answered rather than waiting for all three. | A second scheduled report that is honest about being thin |
| **P2** | **A per-asset pre-market quote**, read against a ±1.3% band: inside the band the quote says nothing and gets no line, outside it the asset has an overnight fact of its own. | Company premarket answers |
| **P3** | **Overnight news, one sentence per asset.** | News answers |
| **P4** | **The morning's macro result** — CPI actual against expected, and one line on the Fed — read as a realised result rather than as a calendar entry. | Releases stop being calendar-only |

**P1 is a report, not a layer.** It is written from what exists, and its labels are the
part that matters: a reader told that the company layer is unavailable knows why the
message is about the market and not about their holdings. Waiting for P2 and P3 before
sending anything is the alternative, and it is the one that leaves the reader with
nothing at 21:00 for no stated reason.

**The band in P2 belongs to the Reading Layer when it is built.** 1.3% is recorded here
as the plan; every threshold in AIS has exactly one owner, and that owner is
`evaluation/reading/bands.py`, not this document.

**What is not being added.** **No more market indicators, no more yields, no more
futures, no more sectors.** The Environment layer is finished: it already answers what
the market is doing, and every measurement added to it makes the report longer without
making it truer. The next work in AIS is the **Company Layer**, which is what P2 and
P3 are, and what the company half of the Report Model still lacks.

**E is done, and it did not make 21:00 its own report by itself.** The evidence the
Market Layer needed turned out to be a smaller set than the pre-market brief needs:
what the environment is doing is not the same as what the next session is being priced
at. That is why the work left is the Company Layer and not more Environment.

So the order holds: **the Company Layer first, then 21:00 becomes a report worth
reading.** Until then, one scheduled report, at the hour when the data is freshest —
five hours after the session it describes, with the after-hours results already in.

**What this does not mean.** It does not mean a second trigger was built. Nothing fires
at 21:00: the brief is owed once a day at 09:00, and adding 21:00 is another schedule
and nothing else — which is the point of it being a schedule rather than a special case.

**A report has two times, and they are chosen for different reasons.** The
**evaluation anchor** is set by the data: an analysis is worth computing once the
information behind it is complete. The **send time** is set by the reader: a
report is worth sending when somebody can read it. Neither may be inferred from
the other, and conflating them is what produced the assumption this section now
removes.

**And a scheduled report is computed when it is sent.** It is built from
everything available at that moment, not from a snapshot taken earlier and
delivered late. A report that is only a delayed copy of an earlier computation is
the same report, and sending it again asks for attention without giving anything
back.

### The two reports sit at the two ends of the US day

The US extended session runs 04:00–20:00 Eastern. In Beijing time, one US trading
day looks like this:

| Eastern | Beijing | State |
| --- | --- | --- |
| D 04:00 | D 16:00 | Pre-market opens |
| D 09:30 | D 21:30 | Regular session opens |
| D 16:00 | D+1 **04:00** | Regular session closes |
| D 20:00 | D+1 **08:00** | Extended session fully ends |
| D 21:00 | D+1 **09:00** | ← **Live Morning Brief** |
| D+1 09:00 | D+1 **21:00** | ← **Pre-Market Brief**, for the next session |

So the two reports are not a preview and a review of the same thing:

- **21:00 Beijing** is thirty minutes before the next open, with that morning's
  macro releases already out and five hours of pre-market already traded.
- **09:00 Beijing** is one hour after the entire US day has ended — regular and
  extended — and while Asia is trading.

Twelve hours separate them, and those twelve hours contain the Asian session, the
European session and the whole US pre-market. **Each carries information the other
cannot.**

### The three triggers

| Trigger | Fires when | Answers | Send time |
| --- | --- | --- | --- |
| **Pre-Market Brief** | 30 minutes before the US open | What matters before the open today | **21:00 Beijing** |
| **Live Morning Brief** | A fixed morning time | What the state is right now, and what changed to get there | **09:00 Beijing** |
| **Intraday Alert** | An event happens | Whether this is worth interrupting for | Not scheduled |

**Pre-Market Brief.** Forward-oriented: what changed overnight and what is on the
calendar, never which way the market will go. **Confirmed: its market half is built and
its company half is not.** The environment it leads with — futures, volatility, yields
and the curve — exists and is shared across assets; per-asset pre-market prices,
overnight news and realised macro results do not. That is the Company Layer, and it is
what P2–P4 in "The gap at 21:00 is one layer wide" are. Status: **defined, not
scheduled.**

**Live Morning Brief.** *Not* a recap of the previous session, and not to be
described as one. **Confirmed.** It is computed at 09:00 Beijing from the freshest
state available at that moment, and it covers everything between the previous
report and this one: the session that has just finished, the after-hours move,
anything announced since, and the Asian session trading while it is written. Its
question is **what the state is now, and what changed to get there** — never what
yesterday's close was. Unlike the Brief, this one is not conditional on new
evidence: most of what it needs, AIS already gathers.

**Intraday Alert.** Triggered by an event, never by a clock. It carries Priority,
which is a runtime result, and it needs a threshold, a rate limit and a record of
what the reader has already been told — none of which exist. See the Priority
section below.

### A drafting error, recorded so it is not repeated

An earlier draft of this section described the morning report as close to a subset
of the pre-market brief's content. **That was wrong.** It assumed both reports
describe the last closed session, so the later one could only repeat the earlier
one.

They do not. The 21:00 brief is sent **seventeen hours before** that session
closes; the 09:00 report is sent **five hours after**. The morning report carries an
entire trading day the brief could only have anticipated — and AIS does not
anticipate anything.

### The assumption this removes

**04:00 Beijing is not a send time.** It is the US regular close, the moment the
regular session's data becomes complete. Nothing is ever pushed at 04:00, and
nothing is defined to be.

### A consequence of reports being live

A report that says **what changed** needs something to compare against, and AIS
holds its two baselines in memory only. `RatingTracker` forgets every standing when
the process stops, and `ChangeDetector` forgets every fingerprint with it. Today
that is a small annoyance: a restart makes the next report read "first rating"
everywhere. With two scheduled reports whose whole job is to say what changed, it
becomes a defect — a restart erases exactly the thing the reports exist to say.

**The baseline has to survive a restart.** Whether that baseline is the previous
report, a close-anchored evaluation, or both, is a decision that belongs with the
runtime design and is not made here.

### What the runtime would have to change

The five things below were the prerequisites for the morning brief. What is done is
marked; **B and E belong to the pre-market brief and the intraday alert** and are
still open.

| # | Change | Where | State |
| --- | --- | --- | --- |
| A | The cadence stops being an interval and becomes **moment-anchored**. The phase used to come from when the process started, which has nothing to do with a clock. | `app/scheduler.py` | **Done** — schedules answer when they are next owed |
| C | The **market-open gate moves off the cycle** and onto the triggers that need it. It used to guard every cycle, which is why nothing could ever fire at 09:00 ET. | `app/application.py` | **Done** for the brief; the cycle still keeps its own gate, which is what an alert should do |
| D | **Notification policy becomes an owned concept.** There used to be one policy, hardwired into the per-asset cycle. The brief is the second, and it lives with the brief. | `app/morning_brief.py`, `analysis/brief.py` | **Done** — the brief owns both when it speaks and what it shows |
| F | **The baseline survives a restart**, so that "what changed" means something after the process is restarted. | `app/runtime_state.py` | **Partly** — what is *owed* survives a restart; what AIS *concluded* still does not |
| B | The market clock gains **transition queries**: when the next open and close are, and whether a session has closed since a given moment. | `utils/market_clock.py` | Open — needed by the close-anchored part of F |
| E | **Market-level evidence appears.** Futures, volatility, yields and the dollar are not measurements of one asset; they are fetched once per cycle and shared. | `contracts/`, `pipeline/` | **Done** — futures, volatility and yields are retrieved once per pass and read beside each asset |

**E is done.** The market's own measurements are retrieved once per pass and shared,
and the Market category reads them beside each asset's own. What the pre-market brief
still needs is the other half: pre-market prices per asset, realised macro releases,
and overnight news.

**F is half done and the other half matters.** The runtime now remembers the day the
brief was sent. It still does not remember what the brief *said*, so a restarted
process cannot tell a reader what changed since — `RatingTracker` and
`ChangeDetector` remain memory only, and a restart still makes the next report read
"first rating" everywhere. That is a smaller problem now than it was, because the
brief's own content does not depend on it, but it is not fixed.

**The two that are easy to underestimate.** D turned out to be answerable, and it was
answered with the brief: the brief owns both when it speaks and what it shows, which
is the projection rule recorded below. What still has no owner is an *alert's*
policy — a threshold, a rate limit and a record of what the reader has already been
told — and that is a different question, listed under Still open. E is the same work
the Market Layer needs, which is why the Brief and the Market Layer should be designed
together rather than twice.

### The brief is one message, and it is a projection of the whole universe

**Built.** The 09:00 brief used to be one message per asset. It is now one message
over the whole watch universe: `analysis/brief.py` holds the brief model and the rule
that decides which assets earn a line, `analysis/brief_report.py` renders it for a
phone, and `app/application.py` sends it once.

**Why this is a report model and not a format.** The report model described one
asset, which is why seven assets could only ever be seven reports. A digest is a
different document: it answers *what should I look at first today*, where the
per-asset report answers *what does AIS know about this asset*. Producing the second
and shortening its lines does not produce the first, so a second model was added
rather than a format changed. What the two do share is the projection rules — how
wide a line may be, how a sentence is broken, and how small a movement is too small
to mention — and those now live in `analysis/projection.py` so that the brief and the
report cannot describe the same reading two ways.

**Analysis coverage and notification projection are different sets.** Everything in
the watch universe is analysed, because AIS cannot know what matters without looking
at all of it. At most three assets are written into the message. The brief states
both numbers and names the assets it left out, so a short message can never be read
as a narrow one, and the watchlist can grow without the message growing.

**What earns a line is a named reason, not a score.** The first slot that applies:

| Slot | Reads as | Applies when |
| --- | --- | --- |
| held, and something moved | 持仓变化 | in the portfolio, and a category grade or its measurement moved |
| held | 持仓 | in the portfolio |
| something moved | 变化 | a category grade or its measurement moved |
| standing | 风险, or no tag | a risk condition does not hold, or an opportunity was judged |
| seen | no tag | it was analysed and nothing above is true of it |

The slots are an editorial ordering, stated once, in the same sense as the attention
an event kind is worth: a reader can disagree with it and can see what was decided.
Within the standing slot the number of opportunity conditions that hold decides,
because that is a judgement AIS has already reached; ties then fall to how near the
nearest event that could change a view is, and then to the order the universe holds.
Nothing is combined into a new number, because a weighted sum of those judgements
would be a new scoring method.

**Risk and opportunity share one slot, and that was learned from real data.** They
answer the same question — where does this asset stand — and ranking risk strictly
above opportunity was tried first, on the reading that AIS manages risk before
return. On a run of the watched universe the risk condition does not hold for six
assets of seven, so the brief filled with the same warning three times and left the
asset whose judgement read best among the ones it did not write out. Risk is still
managed before return; that rule governs the decision, which the evaluators make, and
it does not order the lines of a brief.

**A tag is stated only where a judgement supports it.** The asset whose risk
condition does not hold is flagged. The asset that leads on standing is not:
"opportunity" would be a claim its own judgement does not make — the sentence beside
it reads that the opportunity is ordinary and not a priority.

**The same conclusion is written once.** Assets that reached the same conclusion are
written under one statement of it, labelled, with their own headings beneath it. Three
assets reading alike are one thing to say, and writing it three times costs the reader
the lines that could have differed. What is shared is the conclusion; each asset keeps
its own standing, its own reason tag and its own event.

Two assets reached the same conclusion when their opportunity judgements hold the same
number of conditions, which is what the sentence is written from: equal counts are
equal words. Grouping does not reorder the brief — a group sits where its most
important member sat and its members keep their order — so an asset whose own standing
is lower can appear above one that outranks it, which is the price of not repeating
the sentence, and every heading still states its own standing. Conclusions that differ
are never merged, however similar they read.

**Whether a rating moved is decided in one place**
(`analysis.projection.is_a_change`), so the brief and the per-asset change block
count the same movements: a grade moving, a movement accumulating inside a grade,
and neither a first rating nor a movement too small to read.

**What the brief leaves out, and where it went.** The per-asset report, the
opportunity conditions, the measurements, the category grades and the coverage gaps
are all rendered in full and written to the log for every asset the brief covers.
The brief names the asset; the log holds the run. Nothing is dropped by being left
out of a phone message.

**What it can say about the market, and what it cannot.** The events that bear on
every asset — a central bank meets on the same date whichever symbol is asked about —
are reported once at the top, deduplicated by kind and date, and are not repeated
beside each entry.

**The market state is reported now.** It is one line at the top of the brief, before
anything about an individual asset, read from the environment the whole universe is
judged in: what the futures have done since the last close, how turbulent the market is
and whether that is settling, and which way the cost of money moved. It says what the
market is doing and what it amounts to for risk; what it means for one asset is a
sentence in that asset's own report, and it is not repeated here.

### Still open

- **Whether the environment should reach the opportunity judgement.** HPO reads five
  named conditions and Market is not one of them, so a hostile environment does not by
  itself lower an asset's opportunity count. Changing that is a Constitution-level
  question about which categories HPO reads, and it is not decided.
- **The style reading sits across two asset classes.** Growth against the broad market
  is read from the Nasdaq and S&P futures, which mixes style with where technology sits
  in the index. A value and growth pair of sector instruments would answer the style
  question in one asset class, and the sector instruments are already being fetched.
- **The sector a person states and the sector a vendor publishes can disagree.** The
  file is the authority and the vendor is not consulted, which is the right way round
  and leaves no way to notice a disagreement. Whether a watchlist should be checked
  against a source is open.
- **The industry environment, flows, and the currency exposure.** Named as gaps in the
  report and not connected. The currency one is a decision rather than a missing
  source: the dollar's move is retrievable, and AIS does not know where any asset earns
  its revenue, so it cannot state an effect.
- **The Weekly report** is unclassified. It was one of the three older items and
  none of the three triggers covers it: it is neither event-driven, nor a
  pre-market offset, nor a morning report.
- **The scope of each trigger** — portfolio, watch universe, or both. This decides
  what each report is actually about, and it is not yet decided. The brief's ordering
  already puts a held asset first, so the portfolio half of this is answered as soon
  as the Portfolio Layer exists to fill the set.
- **Who owns notification policy** for an alert, and what counts as material, which
  needs the threshold that is deferred with the AIS Standard Score. The brief's own
  policy is built; an alert's does not exist.
- **Where the baseline lives**, now that it has to outlive the process.
- **What to do when a day is abandoned.** Three attempts that all reached nobody leave
  the day given up on and the reader told nothing all day. Sending a message to say the
  brief failed is close to useless — the channel that would carry it is the one that
  failed — so the runtime logs it and stops there. Whether there is anything better is
  open.

**Settled in this round.** The judgement line repeating when the universe reads alike
is answered in the projection: a conclusion several assets reached is written once,
under a label, with their own headings beneath it. Loosening the reading bars to make
HPO read differently was considered and **declined**: the Reading Layer is strict
because it is internally consistent, and adjusting it to produce more variety in a
report would put the contradictions back that the one-reading work removed. HPO reading
1 for six assets is the reading, not a defect.

**A single combined daily message is built, and it was a decision for the product
review.** It was deferred here as a new report structure rather than a formatting
choice, because the report model described one asset. That review has now been held
and the decision is recorded above.

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
