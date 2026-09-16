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

**Every category should answer three questions.** What is the judgement, why,
and what has not been looked at. The intended shape:

1. **The judgement**, as a visual grade rather than a number. An investor should
   not be asked to compare `13.26` against `0.48` against `5.95`, which are
   different units on an undefined scale.
2. **Why**, as one plain sentence — "valuation looks stretched", "cash flow is
   deteriorating". The summary is the reading; the evidence is only support.
3. **What was not looked at**, in the investor's language, not as `3/8`.

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

## Registered blockers

- **AIS Standard Score direction.** Recorded in `docs/Constitution.md`. Until the
  scale exists, scores are raw measurements averaged together, and different
  categories measure in opposite directions: a larger risk measurement currently
  raises the overall score rather than lowering it. Not worked around, because
  inverting or weighting to compensate would be inventing the scale.

---

End of Backlog
