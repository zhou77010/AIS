# AIS v1.0 — Release Notes

Released: 2026-09-16
Version: 1.0.0

AIS v1.0 is the first version of AIS that runs continuously and delivers a
recommendation to a phone without anyone asking it to.

This document states what AIS does, what it does not do yet, and what it
deliberately left undone. The limitations section is longer than the
capabilities section on purpose: a reader who only reads one of them should read
that one.

---

## What v1.0 does

### Data

- Retrieves live market data from a public source with no API key, no account
  and no third-party dependency. The standard library is enough.
- Retrieves five valuation measurements: trailing P/E, PEG ratio, EV/EBITDA,
  free cash flow yield and DCF fair value.
- Records every measurement as evidence, whether or not it was retrieved. A
  measurement that could not be obtained is recorded as absent, with the reason
  it is absent. No value is ever invented to fill a gap.

### Evaluation

- Runs each measurement through a rule, the score normalizer, and the category
  assembler, in the order the architecture defines.
- Produces a Valuation category score, an overall assessment and a
  recommendation, carrying evidence identifiers the whole way so a conclusion
  can be traced back to the measurement it came from.
- Isolates a failing rule: one measurement that cannot be assessed does not stop
  the others, and it is recorded rather than silently dropped.

### Runtime

- Runs continuously from a single command. The first cycle runs immediately, so
  the first report never waits for an interval to elapse.
- Follows a configurable interval, 30 minutes by default, without polling.
- Shuts down cleanly on Ctrl+C.
- Declines to evaluate while the market it analyses is closed, and says so in
  the log instead of repeating a stale conclusion.
- Watches several symbols per cycle, each decided on its own. One symbol failing
  does not stop the others.

### Delivery

- Sends a recommendation to a phone through Bark. Four further transports
  (PushPlus, ServerChan, a WeChat group webhook and the WeCom app) are
  implemented and configured the same way; channels are additive, so adding one
  never replaces another.
- Sends nothing when the recommendation has not changed. What changed is decided
  per symbol, so one asset moving does not cause a message about the others.

### The mobile report

The report is the product. Every block answers one of three questions, and
nothing that answers none of them is included:

| Block | Question |
| --- | --- |
| Decision, confidence, score | What AIS concluded |
| Why, with the evidence beneath it | Why AIS reached it |
| Categories | What we know, and what we do not |
| Missing | What we do not know |
| Data line | How much of the picture the figures rest on |

The report lists every category the Constitution defines, including the ones
that could not be assessed. An unevaluated category is shown as unevaluated and
never as a score of zero, because zero would read as the worst measured value
rather than as an absent measurement.

---

## Known limitations

These are not oversights. Each one is a consequence of a decision that has not
been made yet, and each is visible in the product rather than hidden behind it.

### The score does not mean anything yet

There is no defined scale. Raw measurements pass through the normalizer
unchanged, so the overall score is an average of raw numbers on incompatible
scales. The report labels it `(scale undefined)` everywhere it appears. **A
reader should ignore the number and read the evidence.**

### Every asset currently receives the same decision

The decision thresholds are placeholders, and the placeholder score never comes
near them. Every symbol AIS watches reports `WATCH`, whatever its evidence says.
The decision output has no discriminating power today.

### The thesis is a placeholder

The reasoning behind the recommendation is a fixed sentence that states the
scoring belongs to the Constitution. It is not an argument about the asset, and
it is the weakest part of the report. It is shown anyway, because a report that
hides its reasoning is worse than one that admits it has none.

### One of nine categories is evaluated

Valuation is assessed. Fundamental, Earnings, Trend, Market, Risk, Catalyst,
Positioning and HPO all render `NOT EVALUATED`. The analysis covers one angle of
nine.

### Risk is not assessed at all

No risk evaluator exists. The Risk category renders as unevaluated. A reader
must not read that as an absence of risk: nothing has been examined.

### DCF fair value can never be retrieved

A discounted cash flow fair value is the output of a valuation model, not a
datum a market data source publishes. It is reported as unavailable by nature,
and no placeholder number stands in for it. This is permanent, not a defect.

### Confidence carries no information

Confidence is a fixed value. It is displayed because a report without it would
imply more certainty than exists, not because it has been computed.

### Coverage is limited by the asset, not by AIS

Some measurements do not exist for some assets, permanently:

| Asset | Measurements available | Why |
| --- | --- | --- |
| AAPL, APP, BABA, MNST | 38 / 38 | — |
| RKLB | 34 / 38 | Loss-making, so there are no positive earnings to divide by |
| HSBC | 30 / 38 | A bank, so ratios that assume an operating business do not apply |
| CGDV | 4 / 38 | An exchange-traded fund, so there is no business to describe |

Treating these as data outages would mean reporting a defect where there is
none. See `docs/EvidenceSurvey.md`.

### Market holidays are not handled

The market clock knows weekdays and session hours. It does not know holidays, so
on a holiday it will evaluate and report on data that has not moved. Holidays
are deliberately out of scope for v1.0.

### Nothing survives a restart

There is no persistence. The change detector lives in memory, so restarting AIS
re-sends every symbol's report once, whether or not anything changed. There is
also no history, so the report cannot say what has changed since last time.

### The evidence chain has registered breaks

Five breaks in the reference chain are documented, not fixed. The most visible
consequence is that the report cannot yet explain, rule by rule, which evidence
produced which part of a category score. They are registered in
`docs/RecommendationReport.md` and are deliberately not patched with temporary
designs.

---

## Deferred work

Deliberately not done, with the reason each is safe to defer.

### Methodology

| Deferred | What it will settle | Why it is safe to defer |
| --- | --- | --- |
| AIS Standard Score | The scale scores live on | Measurements can be recorded on their own scale now and normalized later; the reverse is not possible |
| Decision Thresholds | Where decision states begin and end | A decision can be stated and shown while its thresholds are still provisional, as long as the reader is told |
| Risk Methodology | How each risk dimension is assessed and combined | v1.0 does not assess risk at all, so nothing depends on it yet |
| Confidence Aggregation | How confidence in parts becomes confidence in a whole | Per-claim confidence is meaningful alone; only the aggregate is deferred |
| Driver Attribution | How a driver's contribution is measured and ordered | Drivers can be named before they can be ranked |
| Portfolio Intelligence | How an action is derived from a decision and a portfolio | Decisions are useful without actions |
| The definition of HPO | What question the HPO category answers | Intentionally undefined. Nothing may be assumed about it in the meantime |

### Framework

Recorded in `docs/Architecture.md`, each with the trigger that would justify it:
a `NotificationPolicy`, a `Renderer` interface, a trigger strategy, dependency
injection for the analyzer, and a health status endpoint. None is scheduled.

### Next

**Risk Evaluator is the first feature of v1.1.** It is the highest-value
capability because risk is the one question a decision support system cannot
leave blank. It is not started in v1.0.

---

## Architecture status

**Frozen.** Phases 1 to 3 of the architecture review are complete and the
architecture is approved. Framework work is in maintenance mode: no subsystem is
to be rewritten, and no framework expansion is to be done unless an
architectural defect is discovered.

The boundaries between components are documented in `docs/Architecture.md` and
enforced structurally by `tests/test_architecture_boundaries.py`. A change that
crosses a boundary fails that test. That is the intended behaviour, and the test
is right rather than the change.

Frozen designs: the domain models, the rule engine, the category assembler, the
evidence pipeline, the analyzer, the scheduler, the provider abstraction, the
renderer to transport separation, and the configuration strategy.

---

## Constitution status

**Frozen at version 0.2.** `docs/Constitution.md` is the highest authority in
AIS.

- **v0.1** defines the language: 11 core principles, 18 vocabulary terms, the
  nine categories and the question each answers, and the relationships between
  concepts.
- **v0.2** defines the eight risk dimensions: the kinds of uncertainty that can
  invalidate an investment thesis.

The Constitution defines meaning only. It contains no formula, no threshold, no
weighting and no method. Everything of that kind is listed in its Section 7 as
deliberately deferred, so that its absence is a recorded decision rather than an
oversight.

Two rules from it shape the product more than any other: **absence must never
become zero**, and **no invented semantics** — a name carries only the meaning
the Constitution has given it.

---

## Running it

```bash
python main.py
```

Configuration is environment driven. The settings that matter most:

| Variable | Meaning | Default |
| --- | --- | --- |
| `AIS_TICKER` | Symbols to watch, comma separated | `AAPL` |
| `AIS_ANALYSIS_INTERVAL_MINUTES` | Minutes between cycles; 0 runs once and exits | `30` |
| `AIS_BARK_URL` | Bark device URL or key | unset |
| `AIS_LOG_LEVEL` | Log level | `INFO` |

The full analysis is written to `logs/ais.log`; the phone receives the mobile
projection of the same report.

---

End of Release Notes
