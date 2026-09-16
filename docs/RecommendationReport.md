# AIS Recommendation Report

Design document v1 for every Recommendation output AIS produces.

Status: Design. Nothing in this document is implemented.
Owns: the **report contract** — structure, section responsibilities, required content, how
missing data is expressed, and what is Current versus Future.
Does not own: score methods, confidence methods, decision thresholds, risk methodology.
Those belong to the Constitution.

---

## 1. Purpose

This document is the single source of truth for what a Recommendation Report is.

It is written from the investor's point of view, but it is a **contract**, not a mock-up. It says
what a report must contain and why, so that every renderer produces a view of the same report
rather than inventing its own format.

### 1.1 The principle

> **The report model is authoritative. Renderers are projections of the report model.**

### 1.2 Authority

**This document is not a second Constitution.** It defines a report model, a renderer contract, and
how information is expressed — nothing more. It sits below the models it renders.

```
Constitution            business rules, methods, thresholds     (highest authority)
  -> Models             what AIS knows: evidence, scores, assessment, recommendation
    -> Report Model     this document: structure, responsibilities, expression
      -> Renderers      mobile, console, future surfaces
```

What follows from the chain:

- A renderer may not contradict the Report Model.
- The Report Model may not contradict the Models. Where a report section needs something no model
  carries, that is a **gap to register** (§ Gap Analysis), not a licence to invent the field.
- This document does not define business rules, methods or thresholds. It describes only how their
  results are displayed. Anything that looks like a method here is out of scope by §2.2.

If this document conflicts with the Constitution, the Constitution wins.

---

## 2. Scope

### 2.1 In scope

| This document defines |
| --- |
| The structure of a Recommendation Report, and the order of its sections |
| The responsibility of each section |
| The information each section must contain, and what it must never contain |
| How missing or unevaluated data is expressed |
| How a decision stays traceable back to its market data |
| The difference between what AIS can produce today and what is designed for the future |
| The contract each renderer must satisfy |

### 2.2 Out of scope — belongs to the Constitution

This document must not, and does not, define any of the following. Where a report needs one of
them, the report **displays the result** and states that the method is not yet defined.

| Not defined here | Why the report still needs it |
| --- | --- |
| **Score method** — the AIS standard scale, normalization, aggregation | Every score and grade in a report |
| **Confidence method** — how confidence is derived, and what its bands mean | Confidence appears in the summary, per category, per risk and per evidence item |
| **Decision thresholds** — how a score becomes a decision state | The decision word is the point of the report |
| **Risk methodology** — how severity, likelihood and evidence combine into a risk level or band | Risk is presented as an independent section |
| **Attribution method** — how a rule's contribution to a score is measured | "Top drivers" appears in the summary and in every category |

The report's obligation to these four is the same in every case: **display the raw result, name the
method as not yet defined, and never substitute a plausible number for a missing one.**

### 2.3 Not a specification of AIS as a whole

`docs/Architecture.md` owns layering, folders and dependency rules. This document owns output
design only. It does not restate architecture and must not be used to justify an architectural
change.

---

## 3. Capability status

Every element in this document carries one of four statuses.

| Status | Meaning |
| --- | --- |
| **Current** | The data and the component exist today. A renderer could produce this now. |
| **Future** | Designed here. No component produces this yet. |
| **Blocked** | Requires a Constitution decision before it can be built. Blocked items are also Future. |
| **Frozen** | The design is recorded so it is not lost, but it is deliberately deferred. No work is planned, and no implementation may bind the Report Model to it. |

**A Future or Blocked element is never faked into a Current one.** The report renders it as absent
and says why. A design document that quietly assumes its own prerequisites is how a project ships a
report full of invented numbers.

**A Frozen element may not shape the model.** Frozen sections are recorded for later; they are not
a reason to add a field, a section or an ordering rule to the Report Model today.

### 3.1 Capability status at a glance

| Report section | Document ref | Status | Note |
| --- | --- | --- | --- |
| Executive Summary | §9 | **Current**, partly **Blocked** | Identity, decision, score and provenance render now. Confidence bands and the grade vocabulary are Blocked. |
| Investment Thesis | §11 | **Current**, partly **Blocked** | A thesis is produced today, but it is a placeholder string; a driver-based thesis is Future. |
| Risk | §13 | **Blocked** | No risk evaluator exists. The section renders `UNKNOWN` until one does. |
| Portfolio Recommendation | §14 | **Blocked** | No Portfolio Engine exists. The section renders `NOT APPLICABLE`. |
| Category Breakdown | §10 | **Current** | All nine categories render. Category scores and confidence remain Blocked; the provisional grade is a presentation reading of the measurements. |
| Evidence — ledger | §12 | **Current**, partly **Blocked** | Evidence items render now. Per-item confidence bands are Blocked. |
| Evidence — rule breakdown | §12.2 | **Future** | `EvaluationResult.failures` is discarded before the report can see it. |
| Provenance | §17.1 | **Current**, partly Future | Data source and missing metrics render now. Market as-of time is Future. |
| Limitations | §17.2 | **Current** | Renders now. |
| Mobile Renderer | §15 | **Current**, reduced | Renders now in a reduced form. See §15.5. |
| Full Renderer — worked example | §16 | **Frozen** | No carrier is chosen and none is committed to. The section is recorded, not scheduled. |
| History and trend | §16.1 | **Frozen** | Nothing is persisted and no series exists. Deferred with §16. |

---

## 4. Absence vocabulary

How the report expresses something that is not there. Each token means exactly one thing and may
not be used for anything else.

| Token | Applies to | Means | Rendered as |
| --- | --- | --- | --- |
| `NOT EVALUATED` | a category | No evaluator produced a score for this dimension. | Score position. Never `0`. |
| `UNKNOWN` | a dimension, a risk, any place a finding would go | The dimension was not assessed. | Finding position. Never "no risk", never blank. |
| `UNAVAILABLE` | an input or metric | The source was asked and did not provide it. | Value position, with the reason. |
| `NOT APPLICABLE` | a whole section | The section does not apply — for example no portfolio is configured. | Section body |
| `INSUFFICIENT EVIDENCE` | a decision | No decision could be supported by the available evidence. | Decision position. Never a score. |

Rules:

1. **An absence is always visible.** A blank, an omitted row, or a silently dropped section is a
   defect, not a layout choice.
2. **An absence is never rendered as a number.** `0` means "the worst measured value". It never
   means "we did not look". This is the single most important rule in this document.
3. **An absence carries a reason.** `UNAVAILABLE` states which source and why. `NOT EVALUATED`
   states that no evaluator exists. `UNKNOWN` states that the dimension was not assessed.
4. **Absence is styled normally, not as an error.** A missing input is an expected, ordinary part
   of an honest report, not an exception banner.
5. **Absence is distinguishable from a low value.** `UNKNOWN` risk and `LOW` risk must never look
   alike. Confidence `0.00` on an evidence item means "this is not a finding", and is not the same
   as confidence `0.30`.

---

## 5. Report invariants

These hold for every report and every renderer, without exception.

1. **Report first.** The report model is authoritative. Renderers are projections of the report
   model; no renderer owns a format.
2. **Conclusion first.** The decision appears before its justification.
3. **Nothing appears that no evidence supports.** Every number resolves, through an unbroken chain,
   to at least one evidence item.
4. **The reference chain is never broken and never synthesized.** See §6.
5. **Absence follows §4.** Stated, never implied; never rendered as zero.
6. **Risk precedes Return.** Risk is presented before any position or allocation advice.
7. **Nothing is silently dropped.** Evidence collected but unused, and rules that failed, are
   listed with the reason.
8. **Every claim is falsifiable.** The report states what would change the conclusion.
9. **Same input, same report.** Identical inputs produce an identical report except for the
   generation timestamp.
10. **Provenance is always visible.** Which source answered, what it did not answer, as of when.

---

## 6. Explain Every Decision — the reference chain

A Recommendation must be traceable back to the market data it came from. This is the chain:

```
Recommendation
  → OverallAssessment
    → CategoryScore
      → Rule
        → Evidence
          → Market Data
```

### 6.1 What carries each hop

| Hop | Carried by | Report obligation |
| --- | --- | --- |
| Recommendation → OverallAssessment | The recommendation is derived from one assessment and holds no independent facts | The report presents them together and never shows a decision without its assessment |
| OverallAssessment → CategoryScore | `OverallAssessment.category_scores` | Every category that fed the decision is listed, including the ones that did not |
| CategoryScore → Rule | The category's rule results, in execution order | The report shows which rules produced the score, and which failed |
| Rule → Evidence | The rule result's evidence references | Each rule's references are shown next to that rule, not merged away |
| Evidence → Market Data | `EvidenceItem.source`, `.timestamp`, and the metric carried in its metadata | The report names the source, the capture time, and the market as-of time |

### 6.2 Chain rules

1. **No hop may be omitted from the report.** A score without its rules, or a rule without its
   evidence, is an unexplainable number.
2. **References are never synthesized.** An identifier that no evidence item carries is a broken
   link. The report renders it as broken rather than hiding it, because a plausible-looking
   reference is worse than a visibly missing one.
3. **References are never silently discarded.** Identifiers carried by the analysis must survive to
   the report.
4. **The chain is rendered in both directions.** Decision → evidence answers "why this decision".
   Evidence → decision answers "what did this fact affect", and is the only way to reveal evidence
   that was collected but not used.
5. **Unused evidence is listed.** Evidence collected and then not referenced by any result is
   reported with the reason it was not used.

### 6.3 Where the chain is broken today

These are current implementation facts, not design opinions. They are listed because a report
cannot be built on a broken chain, and they are carried into the Gap Analysis.

| # | Break | Consequence |
| --- | --- | --- |
| CH1 | The placeholder valuation rules return their own rule id as an evidence reference (`valuation.pe`), which no evidence item carries | The Rule → Evidence hop is a broken link in the current path |
| CH2 | A failed rule produces no result, so its references never reach `CategoryScore.evidence_references` | The evidence item that explains the gap is not linked to the decision; the absence is unexplained |
| CH3 | The full evidence collection is not part of `AnalysisResult` | A renderer cannot reach evidence items at all, so hops 4 and 5 are not renderable |
| CH4 | `OverallAssessment` carries no references of its own | The assessment hop is implicit; it must be rendered explicitly rather than inferred |
| CH5 | Category summaries are free text joined from rule reasons | The rule-level structure behind a summary is not recoverable, so the Rule hop cannot be re-rendered |

### 6.4 Disposition

**CH1–CH5 are registered, not scheduled.** They are deliberately left open.

They must not be closed with an interim or temporary design. A stopgap — a synthetic reference id,
a shim that passes the evidence collection alongside the result, a second summary field — would make
the report *look* traceable while the chain stayed broken underneath. A registered gap that is
visible is worth more than a filled-in gap that is not real.

These are properties of the Evidence and Overall layers, not of the report. They are resolved once
the Constitution, the Evidence layer and the overall evaluation are complete, in one pass.

Until then, the report renders the affected hops as missing, using the vocabulary of §4, rather
than filling them in.

---

## 7. Report First — one model, many renderers

### 7.1 The rule

**The report model is authoritative. Renderers are projections of the report model.**

This is the principle of §1.1 stated as a working rule. Bark, the console and any future surface are
renderers of that model.

A renderer may not define its own report format, its own section set, or its own wording for a
decision. A renderer decides only **how much** of the report to show and **how** to lay it out.

Consequences:

- The mobile message is not "the mobile format". It is the Report, projected.
- A full renderer is not "the full format". It is the Report, projected with nothing omitted.
- Two renderers showing different content is not a design choice. It is a defect, unless the
  difference is one of the declared projections in §7.3.
- Adding a renderer later must not change the Report. If it does, the Report was under-specified.

### 7.2 The Report model

The Report has one set of sections (§9–§17), each with a fixed responsibility. Renderers do not add,
remove or reorder them.

The Report model is carrier-neutral. It does not describe any particular surface, and no surface may
shape it. §16 is frozen precisely because it is the one section that comes closest to doing so.

### 7.3 Renderer contract

Every renderer declares three things: what it **must** include, what it **may** omit, and how an
omission is **recoverable**.

| Renderer capacity | Must include | May omit | Recoverability |
| --- | --- | --- | --- |
| Full — console | All sections, in order | Nothing | — |
| Low — mobile push | Decision · confidence and coverage · at least one driver · risk · provenance · generation time | Rule breakdown · evidence ledger · unused evidence · limitations detail | Link to the full report |
| Full — interactive surfaces | All sections | Nothing — collapse is presentation, not omission | Inline drill-down |

The contract is written against **capacity**, not against named products, so that no carrier is
bound to the Report Model. A channel is classified by what it can display, not by what it is.

**The recoverability rule.** A renderer may omit a section only if the omitted content is reachable
from that renderer. An omission with no route back is a permanent information loss.

**A collapsed section is not an omission.** A collapsed category in an interactive renderer is still
present: its warning indicator, its coverage and its status stay visible. Collapsing must never
become a hiding mechanism.

### 7.4 Current limitation

**No route back exists yet.** No report is persisted and nothing serves one, so the mobile renderer
cannot link to the full report. It currently omits sections it cannot recover.

This is a declared, temporary limitation, and it is why §15.5 lists three fields that the mobile
renderer may never omit: they are the parts whose loss would make the short message misleading
rather than merely incomplete.

---

## 8. Overall Report Structure (T1)

### 8.1 Section order

Report positions are numbered `R1`–`R8` to keep them distinct from this document's own section
numbers.

| Position | Section | Question it answers | Document ref | Status |
| --- | --- | --- | --- | --- |
| R1 | Executive Summary | What is the conclusion? | §9 | Current, partly Blocked |
| R2 | Investment Thesis | Why? | §11 | Current, partly Blocked |
| R3 | Risk | What could make this wrong? | §13 | Blocked |
| R4 | Portfolio Recommendation | What should I do about it? | §14 | Blocked |
| R5 | Category Breakdown | How does it look on each dimension? | §10 | Current, mostly Future |
| R6 | Evidence | Show me the receipts. | §12 | Current, partly Blocked |
| R7 | Provenance | What did you not check? | §17.1 | Current, partly Future |
| R8 | Limitations | What in this report is provisional? | §17.2 | Current |

### 8.2 Why this order

**Rule 1 — Answer first, support second, audit last.**

This is a pyramid, not a narrative. An investor who reads one line gets the conclusion; one who
reads a paragraph gets the reasoning; one who reads everything gets the audit trail. A report that
builds up to its conclusion forces the reader to hold five facts in mind before learning whether
any of it mattered.

**Rule 2 — Risk before Return.**

The Constitution requires managing risk before return. In a report this has a concrete
consequence: **Risk (R3) sits above Portfolio Recommendation (R4)**, and both sit above the
Category Breakdown (R5). Sizing advice that appears before the risks constraining it reads as
advice to be followed rather than weighed. This is the most important ordering decision in the
document.

How risk actually constrains a decision — as a veto, a weighting, or a bound on position size — is
**Risk methodology, and belongs to the Constitution.** This document only fixes the order.

**Rule 3 — Detail after decision.**

Category Breakdown, Evidence and Provenance are reference material, read on demand. Placing them
above the summary would bury the decision under its own justification and make the report unusable
on a phone.

**Why Provenance (R7) sits before Limitations (R8) and not last.** Provenance is what makes the
report trustworthy. It belongs after the substance so it does not interrupt the argument, but
before Limitations so a reader who cares about reliability reaches it without reading the appendix.

### 8.3 How the report should be read

| Depth | Report positions | Time | Who |
| --- | --- | --- | --- |
| Skim | R1 | ~15 seconds | Daily check on a held position |
| Read | R1–R4 | ~2 minutes | Considering a change |
| Study | R1–R8 | ~10 minutes | Initial research or a large position |

Every section must be **skippable without losing the conclusion**. R1 never refers the reader
forward for something required to understand it.

---

## 9. Executive Summary (T2)

The first screen. Everything an investor needs in order to decide whether to keep reading.

### 9.1 Fields

| Field | Why it belongs | Status |
| --- | --- | --- |
| Asset — ticker, name, exchange, currency | Identity. A confident report about the wrong asset is worse than no report. Currency is mandatory: a bare number is not a price. | Current |
| Decision | The one word that is the point of the report. A closed vocabulary, never free text. | Current (vocabulary) · Blocked (thresholds) |
| Confidence | How much to trust the decision. Without it, every decision reads equally strong. | Blocked |
| Evidence coverage | The honesty field. Confidence without coverage is unfalsifiable. | Current |
| Overall score | Magnitude, not only direction. Distinguishes "barely" from "strongly". | Current · Blocked (scale) |
| Grade | A human-scale summary of the score. | Blocked |
| Generated time | Freshness. Distinguishes a report from an archive. | Current |
| Market data as of | **A different time from Generated.** A report generated at 14:00 from 09:30 prices is stale, and must look stale. | Future |
| Data source | Which provider answered. Sources disagree; the reader deserves to know which one spoke. | Current |
| One-line rationale | The thesis compressed to one sentence, so the reader is never left with a verdict and no reason. | Current |
| Change since last report | Decision changes are the events that matter most. | Future |

### 9.2 Rules

- **Confidence and coverage travel together.** Confidence `0.72` over 2 of 14 inputs is a different
  claim from `0.72` over 14 of 14. Showing one without the other is misleading.
- **Two timestamps, always.** Generated and As-of. Collapsing them hides staleness.
- **The decision is rendered in the investor's language**, not as a leaked enum value.
- **An undecidable report is not omitted.** It renders `INSUFFICIENT EVIDENCE` with the reason.
  Silence is not an option.
- **A field whose method is undefined shows its raw value plus a marker** that the method is not
  yet defined. It is never given an invented band, grade or label.

### 9.3 What must never appear here

- Prose longer than one line beyond the rationale.
- Disclaimers and legal boilerplate — those belong in one fixed footer, identical on every report.
- Methodology. "The mean of normalized category scores" is a developer's sentence.
- Raw evidence identifiers. The summary cites counts; identifiers belong in §12.
- Any field that is the same on every report. Repetition trains the reader to skip the section.

---

## 10. Category Breakdown (T3)

### 10.1 The nine categories

The Constitution defines **nine** categories:

`VALUATION`, `FUNDAMENTAL`, `EARNINGS`, `TREND`, `MARKET`, `RISK`, `CATALYST`, `HPO`,
`POSITIONING`.

> **Discrepancy to resolve.** The sprint brief for this document listed eight categories and
> omitted `EARNINGS`. The Constitution's `Category` enumeration contains it, and the report renders
> it. Silently dropping a Constitution category would make a whole dimension invisible. If
> `EARNINGS` is genuinely not reportable, the Constitution must say so.

`HPO` is the name rendered. See §10.6: its meaning was frozen by an explicit design
decision, and the name is still written `HPO` everywhere rather than expanded.

### 10.2 Fields per category

| Field | Show? | Rationale | Status |
| --- | --- | --- | --- |
| Score | Yes | The category's headline. Without it the section is prose. | Current · Blocked (scale) |
| Confidence | Yes | A category scored from one input is not the same as one scored from nine. | Blocked |
| Coverage — collected / used / unavailable | Yes | The single most useful field in the section. It is what makes a thin category look thin. | Current |
| Summary | Yes | One clause per driving rule. Where Explain Every Decision is enforced at category level. | Current |
| Top drivers | Yes | The investor needs to know *what* moved the score, not only that it moved. | Future |
| Warnings | Yes, mandatory | Missing inputs, failed rules, stale evidence, conflicting sources, unevaluated dimensions. | Current, partly Future |
| Evidence count | Yes, split | A single count invites the reader to assume all collected evidence was used. | Current |

### 10.3 Presentation template

Every category — implemented or not — uses the same skeleton, so a report can be diffed and scanned:

```
<VALUATION>                                       [evaluated]
  Score        62.4 / 100          confidence 0.78   [scale undefined]
  Coverage     4 of 5 inputs retrieved; 4 used
  Drivers      P/E 26.8         (weight 0.31)
               EV/EBITDA 25.1   (weight 0.26)
               FCF yield 0.82%  (weight 0.22)
  Warnings     DCF fair value UNAVAILABLE — model parameters undefined
  Summary      P/E of 26.8 for NVDA; EV/EBITDA of 25.1 for NVDA; FCF yield of 0.82% for NVDA
  Evidence     NVDA.market_data.pe … NVDA.market_data.fcf_yield  (see §12)
```

and for a category with no evaluator:

```
<RISK>                                       [NOT EVALUATED]
  No evaluator is implemented for this category.
  This dimension was not assessed. It is not neutral and it is not low risk.
  Evidence collected: 0
```

### 10.4 Rules

- **An unevaluated category renders `NOT EVALUATED`.** Never `0`, never a blank. See §4.
- **Partial coverage is stated in the section itself**, not only in a global footnote. A category
  scored from two of nine inputs must look different from one scored from nine of nine.
- **Warnings are never suppressed.** A report that looks clean because its warnings were hidden is
  the most dangerous output this system can produce.
- **Drivers are shown in a defined order, and the report states which method produced that order.**
  The report does not define the ordering method. Until one exists, drivers are listed in rule
  order and the list is explicitly marked as unordered, so that an arbitrary order is never
  presented as a ranking.
- **Summaries are mechanical.** The category summary is assembled from the reasons the rules
  themselves produced. It is never prose written for the occasion. A poor summary is a rule bug,
  not a report bug.
- **Category scores are not comparable to each other** until the standard scale exists. The report
  says so once, in §17.2, rather than letting the reader assume 62 in Valuation means the same as 62
  in Trend.

### 10.5 Category-specific presentation notes

| Category | What makes its presentation different | Status |
| --- | --- | --- |
| Valuation | Quantitative, market-data driven. Drivers are the valuation rules. Warnings are dominated by unavailable inputs, which are normal rather than exceptional. | Current |
| Fundamental | Filing-driven. Every fact needs a **fiscal period**, not only a timestamp: a 10-Q and a 10-K are not interchangeable. Currency is carried per fact, not per asset. | Future |
| Earnings | Event-driven. Needs a date axis and a proximity marker — "results in 6 days" changes the meaning of every other number. Staleness is the dominant failure mode. | Future |
| Trend | Depends entirely on the window. A trend score without its window is meaningless, so the window is displayed with the score rather than stored silently. | Future |
| Market | Regime and context. Its value is explanatory, so it belongs next to the categories it explains. | Future |
| Risk | Presented twice: as a category here, and independently in §13. | Blocked |
| Catalyst | Rendered from its **event layer**, not from a measurement. Events are grouped by the layer they bear on — company, industry, macro — and every line carries why that kind of event matters. The grade reads how near the nearest event is and never how many there are. See §10.7. | Current, partly Future |
| HPO | Not a category reading but a synthesis of the other categories. Rendered as named conditions and a sentence; it carries no score of its own. See §10.6. | Current |
| Positioning | Holdings and crowding are stated as facts. A large holding is not called a good one: no scale says so yet. | Current |

### 10.7 Catalyst — the event block

**Status: Current**, partly Future for the layers with no connected source.

Catalyst answers what could change the investment case, not when something
happens. A date on its own is a reminder; an event with a reason is information.

```
催化因素  ★★★☆☆
 近期暂无明确催化，未来一段时间主要等待美联储议息会议。
 公司
 · 10月30日 季度财报 — 业绩与指引改变增长预期
 宏观
 · 10月28日 美联储议息会议 — 利率路径影响估值分母
 · 12月9日 美联储议息会议 — 利率路径影响估值分母
```

**Rules.**

- **Every event carries why it matters.** The reason is a property of the kind of
  event, never of the instance: AIS states what this sort of event does to an
  investment case and never what this particular one will do, because that is not
  known before it happens.
- **Events are grouped by layer**, in the order company, industry, macro. A layer
  with no events is not written at all; a layer with no source is named in the
  `尚未评估` block.
- **How many events there are is never shown as a judgement.** It shapes the
  wording — a busy month reads as a busy month — and never a star.
- **Only the window is written out.** Events within 90 days are listed, at most
  six; anything beyond is counted on one line rather than listed.
- **A date the source has not confirmed is marked** `（未确认）`.
- **`近期暂无明确催化。` is an answer, not a gap.** It is written as a sentence in
  the category's own block, and the category is never listed among things nothing
  was done about.
- **No event is ranked, scored, or given a probability**, and no news is
  summarised to produce an event.

---

### 10.6 HPO — the opportunity block

**Status: Current.** HPO answers one question: *if capital were available today, is this one of the
highest probability opportunities worth allocating to?* It is not a quality score, not the overall
score and not a recommendation.

It is a **synthesis**, not a ninth reading of the data. It reads the grades the other categories
already reached; it never re-reads evidence and never consults a source.

**Named conditions, not a number.** HPO is decided by a small set of named conditions, each reading
exactly one category and reporting one of three states:

| State | Meaning |
| --- | --- |
| Satisfied | The condition holds. |
| Not satisfied | The condition was judged and does not hold. |
| Unknown | The category it reads had no grade. **This is not a failure.** |

Nothing is weighted, nothing is normalized and no scale is invented. The star count is a **count of
the conditions that hold among those judged**; a condition that could not be judged is left out of
the count and named separately. Those belong to the future AIS Standard Score project.

**Presentation template.**

```
<HPO>                                              [opportunity]
  ★★★★☆
  当前属于值得优先配置的机会：估值具备吸引力、趋势向好；但暂无近期催化。
  未评估的条件：资金不拥挤。
```

The third line appears only when a condition could not be judged. The block carries no score, no
confidence and no coverage figure, because none of those exist for it.

**Rules.**

- **No number is ever shown for HPO.** A combined figure would be a score on a scale nobody defined.
- **An unknown condition is never written as a failure.** Not judged and judged false are different
  states and must read differently.
- **HPO is never listed as an unevaluated dimension.** It reports its own gaps by name inside its block.
- **HPO never produces a recommendation.** What to do belongs to the Recommendation; HPO only says
  whether the opportunity is worth allocating to.
- **The conditions are provisional** and are thresholds on a presentation grade. They change together
  with the grade they read, never separately.

---

## 11. Investment Thesis (T4)

### 11.1 Summary versus Investment Thesis

Two different things. Conflating them is the most likely design mistake in this document.

| | Summary | Investment Thesis |
| --- | --- | --- |
| Scope | One category | The whole asset |
| Produced | Mechanically, by joining the reasons the rules produced | Interpretively, by the Recommendation Engine |
| Contains interpretation | No | Yes |
| May cite evidence ids | Yes | Yes |
| Length | One clause per rule | Bounded prose |
| Reads as | A record | An argument |

**The Summary is the raw material; the Thesis is the argument built from it.**

- The Thesis **must not be a concatenation of the Summaries.** That is duplication, and it produces
  a paragraph nobody reads. If the Thesis reads like the Summaries joined by semicolons, it failed.
- The Thesis **must be consistent with** the Summaries. It may not claim what they contradict.
- The Thesis is the **only** place the report explains tension between categories — for example
  that Valuation looks stretched while Trend looks strong. Summaries cannot, because each sees one
  category.
- The Thesis must never introduce a fact that appears in no Summary and in no evidence item.

### 11.2 Length

| Renderer | Length |
| --- | --- |
| Mobile | One sentence, ≤ 25 words. May be omitted if the driver block carries it. |
| Console | 3–5 sentences, ≤ 90 words. The default. |
| Full renderer | ≤ 180 words, plus a structured driver list. |

Longer is not more thorough. A thesis that needs 300 words has not decided what matters.

### 11.3 Writing style

- **Declarative, present tense.**
- **Attributed.** Every quantitative claim names its value and its evidence: "P/E of 26.8", not
  "rich valuation".
- **Ordered by importance**, not by category order.
- **Balanced by construction.** It states the strongest counter-consideration. A thesis with no
  counter-consideration is marketing.
- **Falsifiable.** It ends with what would change the conclusion.
- **Plain language.** No jargon without a definition, no acronyms beyond the asset's own ticker.

Pattern:

> The evidence currently supports **X**, primarily because **A** and **B**. The main consideration
> against this is **C**. This would change if **D**.

### 11.4 What must be included

- The decision, restated in plain language.
- The two or three dominant drivers, with their values.
- The single strongest counter-consideration.
- The falsifier: what would change the decision.
- A pointer to the evidence supporting each claim.

### 11.5 What must never appear

- **Numbers with no evidence behind them.** Every figure resolves to an evidence id.
- **Price predictions.** AIS supports decisions; it does not forecast prices.
- **Imperatives directed at the reader.** "You should buy" is advice; "the evidence supports" is
  analysis.
- **Certainty language.** "Guaranteed", "certainly", "cannot fail".
- **Hedging without a stated reason.** "May potentially appear somewhat expensive" communicates
  nothing. If uncertainty exists, name its source.
- **Restated methodology.** The reader does not need the mean of normalized scores.
- **Disclaimers.** They belong in one fixed footer, identical on every report, so their absence
  elsewhere is not read as reassurance.
- **Restatement of the category summaries.**
- **Language implying the score is the decision.** The score is an input to the decision.

---

## 12. Evidence Presentation (T5)

The Constitution requires that every decision be explainable. This section is where that
requirement is either satisfied or quietly broken. It is also where the reference chain of §6
becomes visible.

### 12.1 What to expose

| Item | Expose? | Rationale | Status |
| --- | --- | --- | --- |
| Rules | Yes, Tier 1 | The rule is the unit that produced a measurement. Without it, a score is unattributable. | Current |
| Rule outcome — raw and normalized | Yes, Tier 1 | Both matter: the raw value is the fact, the normalized value is what the score used. Showing only one makes the other look arbitrary. | Current |
| Rule reason | Yes, Tier 1 | The rule's own explanation. The primary carrier of Explain Every Decision. | Current |
| Evidence items | Yes, Tier 2 | The facts. Too bulky for the main flow, essential for audit. | Current |
| Sources | Yes, both tiers | A fact with no named source is not evidence. | Current |
| Evidence confidence | Yes, Tier 2 | Not all evidence is equally reliable. | Current · Blocked (scale) |
| Timestamps | Yes, both tiers | When the fact was captured, and the as-of time it describes. These differ. | Current · Future (as-of) |
| Metadata | Yes, Tier 2, filtered | Fiscal period, units, currency and derivation are part of the fact. Raw vendor payloads are not. | Current |
| **Unavailable inputs** | Yes, Tier 1 | A missing input is an explanation. Recording only what succeeded makes an incomplete analysis look complete. | Current |
| **Rule failures** | Yes, Tier 1 | A rule that raised is a hole in the analysis. Hiding it makes the score look better supported than it is. | Future |
| **Unused evidence** | Yes, Tier 2 | Evidence was collected and then not used. Not saying so hides a decision. | Future |

### 12.2 Two tiers, one rule

**Tier 1 — Reasoning trace.** Always rendered. Per category, the rules that produced the score:

```
VALUATION
  rule                 raw          normalized   reason
  valuation.pe         26.80        26.80        P/E of 26.80 for NVDA
  valuation.peg        0.46         0.46         PEG of 0.46 for NVDA
  valuation.ev_ebitda  25.14        25.14        EV/EBITDA of 25.14 for NVDA
  valuation.fcf_yield  0.0082       0.0082       FCF yield of 0.82% for NVDA
  valuation.dcf        —            —            FAILED: no source can supply it
  references           NVDA.market_data.pe, NVDA.market_data.peg, …
```

**Tier 2 — Evidence ledger.** Rendered in the full report; collapsed by default in an interactive
renderer.
One row per evidence item, grouped by category, in a stable order:

```
id                          category    source        captured            conf  description
NVDA.market_data.pe         valuation   market_data   2026-09-16 02:45    1.00  Trailing P/E 26.80 retrieved from Yahoo Finance
NVDA.market_data.dcf        valuation   market_data   2026-09-16 02:45    0.00  DCF fair value is not retrieved: it is the output of a valuation model…
NVDA.valuation              valuation   system        2000-01-01          1.00  Placeholder evidence for NVDA in the valuation category
```

### 12.3 The rule that makes this work

**Every number displayed anywhere in the report resolves, through the §6 chain, to at least one
evidence identifier.**

A number that cannot be traced this way must not be displayed. This is not a stylistic preference;
it is what makes the report auditable. It also has a practical benefit: an implementation that
cannot produce the trace has a real modelling gap, and the report surfaces it rather than hiding it.

### 12.4 Presentation rules

- **Stable ordering.** Rules in execution order; evidence grouped by category and sorted by id. A
  report that reorders itself between runs cannot be diffed.
- **Missing before successful, within warnings.** The reader sees the holes first.
- **Absent evidence is not hidden behind a clean layout.** The `UNAVAILABLE` block is a normal,
  expected part of the report, styled like the rest rather than as an error banner.
- **Do not expose vendor payloads.** Raw responses couple the report to a vendor and bury the fact
  in noise. The reason string carries the derivation instead.
- **Confidence is displayed but not interpreted** until its scale is defined. The report shows the
  value and marks the band as undefined rather than inventing labels.
- **Placeholder evidence is labelled.** Evidence whose source is the system itself is visibly
  different from evidence a real source produced. A reader must never mistake scaffolding for a
  finding.
- **The evidence ledger is filterable** by category and by source in renderers with room for it.

---

## 13. Risk Presentation (T6)

### 13.1 Should Risk be independent?

**Yes — as presentation, in three separate senses.** This follows from the Constitution's rule
that risk is managed before return.

1. **As a category.** `RISK` is one of the nine categories and carries its own score, confidence
   and warnings.
2. **As a top-level section.** Risk is presented in its own section (§13), independent of the
   category breakdown.
3. **As a constraint presented before the action.** Risk is shown before any position or allocation
   advice.

How risk actually enters the decision is **Risk methodology, and belongs to the Constitution.**
This document does not decide whether risk vetoes a decision, weights it, or bounds position size.
It decides only that **the reader encounters risk before the action**, and that the report never
relies on a single aggregate number to convey it.

> **Aggregation concern, for the Constitution.** If the overall score is an average over
> categories, a severe risk score can be diluted by eight other categories and disappear from the
> decision. Whatever the Constitution decides, the report must not depend on the aggregate alone
> to convey risk. This document does not resolve it.

### 13.2 Ordering

- The Risk section sits **after the Investment Thesis and before the Portfolio Recommendation**.
- Within the section: **major findings first**, then minor, then unevaluated dimensions.
- Within a band: ordered by confidence, highest first, so the best-supported finding leads.

### 13.3 Major versus minor

The report displays, per risk: severity, confidence and the evidence behind it, as **separate
fields with their own values**.

**How those fields combine into a band, and where the boundary between major and minor lies, is
Risk methodology and belongs to the Constitution.** Until it is defined:

- the report sorts by the displayed severity value,
- and labels the band as **undefined**, rather than inventing a cut-off.

Rules that hold regardless of the banding:

- **A major finding is promoted into the Executive Summary** whenever it could change the decision.
  A risk buried in §13 has not been managed before return.
- **Every risk carries its own confidence and its own evidence references.** A risk stated without
  evidence is an opinion and is labelled as one.
- **Unquantified risks are still listed.** Not being able to size a risk is not a reason to omit it.

### 13.4 Confidence display

- Per-risk confidence, plus the aggregate confidence of the Risk category.
- A **coverage line**: how many risk dimensions were assessed out of how many exist.

This is the field that prevents the most dangerous misreading in the report.

### 13.5 The hard rule

> **An unassessed risk dimension renders as `UNKNOWN`. It never renders as "no risk".**

Absence of a finding is not a finding. A report that shows a clean risk section because the risk
evaluator does not exist converts an unexamined dimension into apparent safety. Until risk
evaluation is implemented, the Risk section states **in the report itself** that this dimension was
not assessed.

---

## 14. Portfolio Recommendation (T7) — Future Design

Design only. The Portfolio Engine does not exist; the `Portfolio` model and the `PortfolioEngine`
contract do.

### 14.1 The distinction that must not be blurred

| | Decision | Action |
| --- | --- | --- |
| About | The asset | This portfolio |
| Produced by | Recommendation Engine | Portfolio Engine |
| Example | `ACCUMULATE` | "increase 4.0% → 6.0%" |
| Depends on | Evidence | Decision + current holdings + constraints |

The same asset can be `ACCUMULATE` in one portfolio and `TRIM` in another, because the second is
already overweight. **The report presents these as two separate, clearly labelled things.** A
recommendation that silently becomes an action — or an action that appears to be the analysis —
breaks the architecture's separation and misleads the reader about what was decided.

The Portfolio Engine **consumes** the Recommendation and returns portfolio state. It never modifies
the analysis.

### 14.2 Fields

| Field | Why | Status |
| --- | --- | --- |
| Suggested Action | The one thing to do. Closed vocabulary. | Blocked |
| Suggested Weight | The target. `NOT APPLICABLE` when no portfolio exists. | Blocked |
| Current Weight | Without it the target is meaningless — 6% is very different from 0% and from 20%. | Future (`Portfolio` model exists) |
| Delta | The actionable quantity, in the portfolio's base currency. | Blocked |
| Constraints Applied | Which limit bound the result: position cap, concentration, liquidity, risk budget. | Blocked |
| Position Rationale | Why this size and not more or less. | Blocked |
| Why not more / why not less | The two questions a reader always has. | Blocked |

### 14.3 Rules

- **Never invent a portfolio.** With none configured the section renders
  `NOT APPLICABLE — no portfolio configured`, explicitly. Omission would let the reader assume the
  recommendation was portfolio-aware.
- **Never present an action without its binding constraint.** "Increase to 6%" is uninformative if
  the real reason was a 6% cap.
- **Weights carry the base currency and an as-of date.** A weight is a snapshot of a portfolio that
  moves.
- **The analysis is not restated here.** The section references §9 rather than repeating the
  decision, so the two can never disagree.
- **Ordering inside the section:** Action → Suggested Weight → Current Weight → Delta →
  Constraints → Rationale.

### 14.4 When no action is warranted

The report must be able to say **"no change"** as a first-class outcome, with a reason. A system
that speaks only when it wants a trade trains its user to trade.

### 14.5 Status

Entirely Future. The Portfolio Engine, and every method behind the fields above, must exist before
this section renders anything other than `NOT APPLICABLE`.

---

## 15. Mobile Renderer (T8) — Current, reduced

The projection of the Report for Bark and every future push channel. Target: readable in under 30
seconds, ≤ 25 lines, plain text.

This is **not** a separate report format. It is the Report of §9–§17, projected under the contract
of §7.3.

### 15.1 Line budget

| Block | Lines | Purpose |
| --- | --- | --- |
| Identity | 3 | Asset, plus separators |
| Decision | 3 | Decision, confidence + coverage, score + grade |
| Why | 5 | Header plus up to three drivers |
| Risk | 2 | Level and the single most important finding |
| Portfolio | 2 | Current → suggested, or `NOT APPLICABLE` |
| Provenance | 4 | Source, coverage, as-of, unavailable inputs |
| Footer | 2 | Generated time, link to the full report |
| Separators | 4 | |
| **Total** | **≤ 25** | |

### 15.2 Rules

- **Plain text only.** No Markdown, no HTML, no tables. Push channels render them inconsistently or
  not at all.
- **Never truncate a number.** If space is short, drop a driver, not a digit. A truncated number is
  a wrong number.
- **Prose is truncated with an explicit ellipsis**, never silently.
- **URLs must stay ASCII.** The body may carry any UTF-8 text; a URL may not. This is a real
  constraint discovered during the MVP, not a theoretical one.
- **The decision word is uppercased** so it is findable at a glance without reading the line.
- **A degraded report looks degraded at a glance.** When market data is unavailable the data block
  says so, and the score position renders `INSUFFICIENT EVIDENCE` — never a zero.

### 15.3 Complete example — normal case

Illustrative values. Grade vocabulary and confidence bands are Blocked; they appear here to show
the layout, not to define them.

```
--------------------------------
AIS | NVDA | NVIDIA Corporation
--------------------------------
DECISION    ACCUMULATE
CONFIDENCE  0.72   coverage 11/14
SCORE       62.4 / 100      B+
--------------------------------
WHY
 + Valuation    P/E 26.8, FCF yield 0.82%
 + Trend        above 50d and 200d
 - Risk         valuation needs growth
--------------------------------
RISK        MODERATE   3 major, 2 minor
PORTFOLIO   4.0% -> 6.0%   ADD
--------------------------------
DATA        Live market data (Yahoo)
            valuation 4/5 inputs
            as of 2026-09-16 02:45
DCF         UNAVAILABLE - model undefined
--------------------------------
Generated 2026-09-16 02:47
Full report: ais://report/NVDA/...
--------------------------------
```

23 lines.

### 15.4 Complete example — degraded case

The same projection, with the data source unavailable. No score is shown.

```
--------------------------------
AIS | NVDA | NVIDIA Corporation
--------------------------------
DECISION    INSUFFICIENT EVIDENCE
REASON      no market data retrieved
--------------------------------
WHY
 - No market data was retrieved
 - No category could be evaluated
--------------------------------
RISK        UNKNOWN   risk not assessed
PORTFOLIO   NOT APPLICABLE
--------------------------------
DATA        UNAVAILABLE (Yahoo)
            0 of 5 valuation inputs
            as of 2026-09-16 02:45
--------------------------------
Generated 2026-09-16 02:47
Full report: ais://report/NVDA/...
--------------------------------
```

20 lines. The decision position carries `INSUFFICIENT EVIDENCE` rather than a score, because a
score of zero would be a fabricated measurement.

### 15.5 What this renderer may never omit

The mobile renderer omits the Evidence Ledger, the rule trace and per-risk confidence. That is
acceptable in principle because §7.3 requires a route back to them — but **no such route exists
yet** (§7.4).

Until it does, three fields are non-negotiable, because losing them turns a short message from
incomplete into misleading:

1. **the provenance block** — which source answered and when,
2. **the unavailable-input line** — what could not be retrieved,
3. **the coverage figure** — how much of the input set answered.

Everything else may be cut. These three may not.

### 15.6 Chat channels

PushPlus, ServerChan, the WeChat group webhook and the WeCom app are renderers too. They use the
same projection and differ only in the transport and in the length they tolerate. A channel that
supports markup may render the Report as formatted text, but the **content must not differ** from
the plain-text projection: a channel is a transport, not a report format.

---

## 16. Full Renderer (T9) — Frozen

**Status: frozen.** This section is recorded so the design is not lost. No work is planned, and
nothing here may be used to bind the Report Model to a particular surface.

This section is **carrier-neutral**. It describes what a renderer with unlimited space and
interactive affordances would project from the Report Model. The layout below uses a dashboard-like
arrangement only because a worked example needs some arrangement. **AIS does not commit to a
dashboard.** A dashboard is one possible future carrier among several, and no carrier has been
chosen.

What the freeze means in practice:

- The Report Model must not gain a field, a section or an ordering rule that exists only to serve
  this layout.
- The only thing this section may rely on is the renderer contract of §7.3.
- The `dashboard/` package exists and is empty. That is not a plan; it is a placeholder folder.
- Choosing a carrier is a prerequisite decision and is not made here (§16.5).

### 16.1 Panels

| Panel | Content | Expanded by default | Status |
| --- | --- | --- | --- |
| Header | Asset identity, decision, generated and as-of times, data source | — | Frozen |
| Executive summary | §9, verbatim | Yes | Frozen |
| Investment thesis | §11 | Yes | Frozen |
| Risk panel | §13, with per-risk confidence and coverage | Yes | Frozen |
| Portfolio panel | §14 | Yes | Frozen |
| Category accordions | One per category, collapsed to score + coverage + warnings | No | Frozen |
| Rule breakdown | Per category, the Tier 1 table from §12.2 | No | Frozen |
| Evidence ledger | §12.2 Tier 2, filterable by category and source | No | Frozen |
| History | Score, decision and data coverage over time | No | Frozen |
| Limitations | §17, plus provenance | Yes | Frozen |

### 16.2 Panel to data source mapping

The mapping is included because it is what makes the freeze concrete: it shows which panels could be
built today and which cannot, without proposing any work.

| Panel | Would be built from | Status |
| --- | --- | --- |
| Header | `AnalysisResult.asset`, `.market_data`, decision | Current |
| Executive summary | `OverallAssessment`, `Recommendation` | Current |
| Investment thesis | `Recommendation.investment_thesis` | Current (placeholder text) |
| Risk panel | Risk category, `RiskProfile` | Blocked |
| Portfolio panel | `Portfolio`, Portfolio Engine output | Blocked |
| Category accordions | `OverallAssessment.category_scores` | Current |
| Rule breakdown | `EvaluationResult.results` and `.failures` | Future — failures are discarded today |
| Evidence ledger | `EvidenceCollection.items` | Future — not reachable from `AnalysisResult` today |
| History | Persisted report snapshots | Future — nothing is persisted |
| Limitations | `MarketDataSnapshot.missing_points`, gap notices | Current |

### 16.3 Complete example

```
+------------------------------------------------------------------------------+
|  NVDA - NVIDIA Corporation            NASDAQ - USD                            |
|  DECISION  ACCUMULATE         CONFIDENCE 0.72 (coverage 11/14)                |
|  SCORE  62.4 / 100   Grade B+          Generated 2026-09-16 02:47             |
|  Data  Live market data (Yahoo Finance, 4/5 valuation)   as of 02:45          |
+------------------------------------------------------------------------------+

+-- EXECUTIVE SUMMARY ---------------------------------------------------------+
| The evidence supports accumulating a position: valuation is not stretched     |
| relative to growth, and the price trend is intact. The main consideration     |
| against is that the valuation depends on growth continuing, which is the      |
| least certain input. This view would change if growth estimates were cut       |
| materially or the trend broke.                                                |
|                                                                               |
| Coverage  11 of 14 inputs retrieved   1 rule failed   1 category unevaluated  |
+-------------------------------------------------------------------------------+

+-- INVESTMENT THESIS ----------------------------------------------------------+
| Trailing valuation is moderate for the growth being priced in, and the        |
| balance sheet supports it: free cash flow covers the multiple. Trend and      |
| market context agree, so the entry is not fighting the tape.                  |
|                                                                               |
| The counter-consideration is concentration of the thesis in one assumption:   |
| the growth rate. Everything favourable here rests on it holding.              |
|                                                                               |
| This would change if the growth estimate fell, or free cash flow coverage     |
| deteriorated below the level the multiple assumes.                            |
|                                                                               |
| Drivers    Valuation  (P/E 26.8, FCF yield 0.82%)      weight 0.31            |
|            Trend      (above 50d/200d)                 weight 0.24            |
|            Risk       (growth dependence)              weight -0.29           |
+-------------------------------------------------------------------------------+

+-- RISK ------------------------------------------------------------ MODERATE ---+
| Coverage  4 of 9 risk dimensions assessed                                     |
|                                                                               |
| MAJOR                                                                         |
|  ▲ Growth dependence        severity 0.74  conf 0.68  ev NVDA.valuation.pe    |
|  ▲ Concentration            severity 0.61  conf 0.55  ev NVDA.positioning...  |
|  ▲ Multiple compression     severity 0.59  conf 0.61  ev NVDA.market_data...  |
| MINOR                                                                         |
|  . Liquidity                severity 0.21  conf 0.80                          |
|  . FX                       severity 0.14  conf 0.72                          |
|                                                                               |
| UNKNOWN                                                                       |
|  ? Regulatory  ? Geopolitical  ? Execution  ? Technology  ? Governance        |
|  These dimensions were not assessed. They are not low risk.                   |
+-------------------------------------------------------------------------------+

+-- PORTFOLIO -------------------------------------------------------------------+
| DECISION (about the asset)      ACCUMULATE                                    |
| ACTION   (about this portfolio) ADD                                           |
|                                                                               |
| Current 4.0%  ->  Suggested 6.0%    Delta +2.0%  (+18,400 USD)                |
| Binding constraint  single position cap 6.0%                                  |
| Rationale  The decision supports adding, and the position cap binds before    |
|            the risk budget does. Raising the cap is not proposed here; it     |
|            would require the risk dimension to be assessed first.             |
+-------------------------------------------------------------------------------+

+-- CATEGORIES ------------------------------------------------------ 1 / 9 open -+
| > VALUATION    62.4  conf 0.78  coverage 4/5   ! DCF UNAVAILABLE       [open] |
|   rule                 raw      norm     reason                               |
|   valuation.pe         26.80    26.80    P/E of 26.80 for NVDA                |
|   valuation.peg        0.46     0.46     PEG of 0.46 for NVDA                 |
|   valuation.ev_ebitda  25.14    25.14    EV/EBITDA of 25.14 for NVDA          |
|   valuation.fcf_yield  0.0082   0.0082   FCF yield of 0.82% for NVDA          |
|   valuation.dcf        -        -        FAILED: no source can supply it      |
|                                                                               |
| > FUNDAMENTAL  NOT EVALUATED - no evaluator implemented                       |
| > EARNINGS     NOT EVALUATED - no evaluator implemented                       |
| > TREND        71.0  conf 0.64  coverage 3/3   window 50d/200d                |
| > MARKET       NOT EVALUATED - no evaluator implemented                       |
| > RISK         see RISK panel above                                           |
| > CATALYST     NOT EVALUATED - no evaluator implemented                       |
| > HPO          NOT EVALUATED - no evaluator implemented                       |
| > POSITIONING  NOT EVALUATED - no evaluator implemented                       |
+-------------------------------------------------------------------------------+

+-- EVIDENCE LEDGER --------------------------------------- 5 items   [filter] ----+
| id                      cat   src          captured          conf  desc       |
| NVDA.market_data.pe     val   market_data  2026-09-16 02:45  1.00  P/E 26.8   |
| NVDA.market_data.peg    val   market_data  2026-09-16 02:45  1.00  PEG 0.46   |
| NVDA.market_data.ev..   val   market_data  2026-09-16 02:45  1.00  EV/EBITDA  |
| NVDA.market_data.fcf..  val   market_data  2026-09-16 02:45  1.00  FCF yield  |
| NVDA.market_data.dcf    val   market_data  2026-09-16 02:45  0.00  absent     |
+-------------------------------------------------------------------------------+

+-- HISTORY ----------------------------------------------------------- 30 days --+
|  score  |                     .-.                                             |
|   70    |              .------' '-'--                                          |
|   60    |      .-------'                                                      |
|   50    |------'                                                              |
|         +---------------------------------------------------                  |
|  decision    WATCH -> HOLD -> ACCUMULATE       (2 changes in 30 days)         |
|  coverage    9/14 -> 10/14 -> 11/14            (improving)                    |
+-------------------------------------------------------------------------------+

+-- LIMITATIONS ----------------------------------------------------------------+
| Not evaluated   fundamental, earnings, market, catalyst, hpo, positioning     |
| UNAVAILABLE     DCF fair value (no source publishes a model output)           |
| Failed rules    1 of 5 valuation rules                                        |
| Scale           The standard score is undefined. Category scores are shown    |
|                 on their raw scale and are NOT comparable with each other.    |
| Placeholder     Overall score, grade, confidence and thresholds are           |
|                 placeholders. This report is a rendering contract, not a      |
|                 finished methodology.                                         |
+-------------------------------------------------------------------------------+
```

### 16.4 Rules for a full interactive renderer

These are the general obligations of any renderer with room to collapse and expand. They are not
dashboard-specific, and they follow from §7.3 rather than from any carrier.

- **Collapsed categories still show warnings.** A collapse that hides a warning turns the collapse
  itself into a hiding mechanism.
- **`NOT EVALUATED` categories appear in the list**, in Constitution order. Removing them would make
  the surface look more complete than the analysis is.
- **History shows coverage alongside score.** A score that rose while coverage fell is not an
  improvement, and the chart must not be readable as one.
- **The Limitations section is open by default and never truncated.** It is what keeps the rest
  honest.
- **Every panel links to its evidence**, which is what makes the "omit nothing but collapse
  everything" contract workable.

### 16.5 Prerequisites — not scheduled

Recorded so that the freeze is unambiguous, not as a plan.

A full interactive renderer cannot exist before: a report model exists, reports are persisted, a
route serves them, and a carrier is chosen. AIS has no rendering surface of its own; the web GUI
available during development belongs to the harness, not to AIS.

**Choosing a carrier is a prerequisite decision, and it is deliberately not made in this
document.** Until it is made, §16 stays frozen and the Report Model stays carrier-neutral.

---

## 17. Provenance and Limitations

### 17.1 Provenance — Current, partly Future

| Content | Status |
| --- | --- |
| Source name and what it answered | Current |
| Inputs it could not provide, with reasons | Current |
| Capture time | Current |
| Market as-of time | Future |
| Capture method and version of the retrieval logic | Future |

### 17.2 Limitations — Current

Rendered near the end of the report, before the footer. It states:

- which categories were not evaluated,
- which inputs were unavailable and why,
- which rules failed,
- that the standard scale is undefined, and that category scores are therefore not comparable,
- that overall score, grade, confidence and thresholds are placeholders.

> **The Limitations section is the report's honesty guarantee.** It must be present in every
> renderer that has room for it, and it must be open by default wherever it can be collapsed.

---

# Gap Analysis

What is still missing before the designed report can exist. Documentation only; nothing below is
implemented.

The first table blocks the report outright. Everything after it degrades it.

## Blocking gaps

| # | Gap | Why the report cannot exist without it |
| --- | --- | --- |
| B1 | **AIS Standard Score undefined** | Every score, driver order and grade assumes a defined scale. Today the normalizer passes raw measurements through unchanged, so "62.4 / 100" cannot be produced honestly. |
| B2 | **Confidence semantics undefined** | Confidence appears in the summary, per category, per risk and per evidence item. Nothing defines what the number means or where a band begins. |
| B3 | **Decision thresholds undefined** | The decision word is the point of the report. Today's thresholds are explicitly placeholders and the grade vocabulary does not exist. |
| B4 | **No report model** | `analysis/report.py` returns a plain `str`. Without a structured report, "Report First" cannot hold: renderers have no model to project. See M1. |

## Chain breaks

Carried from §6.3. The reference chain must be unbroken before the evidence sections can be built.

**These are registered, not scheduled.** They are not to be closed with an interim or temporary
design; a stopgap would make the report look traceable while the chain stayed broken underneath.
They are resolved in one pass, once the Constitution, the Evidence layer and the overall evaluation
are complete. See §6.4.

| # | Break | Consequence |
| --- | --- | --- |
| CH1 | Placeholder valuation rules return their own rule id as an evidence reference | Rule → Evidence is a broken link |
| CH2 | Failed rules contribute no references to `CategoryScore` | The evidence explaining the gap is unlinked from the decision |
| CH3 | `AnalysisResult` does not carry the evidence collection | Evidence → Market Data hops are not renderable |
| CH4 | `OverallAssessment` carries no references | The assessment hop must be inferred rather than rendered |
| CH5 | Category summaries are free text | The rule-level structure behind a summary is unrecoverable |

## Models

| # | Gap | Impact |
| --- | --- | --- |
| M1 | No `RecommendationReport` model | No structured report exists for a renderer to project. Blocks the whole design. |
| M2 | No report schema version | Reports cannot be compared over time or replayed if their shape is unversioned. |
| M3 | `CategoryScore.summary` is a flat string | Cannot carry per-rule structure, drivers, warnings or coverage. §10 needs all four. |
| M4 | No driver/contribution model | "Top drivers" in §10 and the `WHY` block in §15 have no data source. |
| M5 | No warning model | Warnings live in free-text logs, so they cannot be rendered per category. |
| M6 | `EvidenceItem.metadata` is `Mapping[str, str]` | Cannot carry a fiscal period, a unit, a currency or a structured derivation. §10 and §12 need these. |
| M7 | No currency or unit on evidence | A number without a currency is not a price, and cross-market comparison is unsafe. |
| M8 | No market as-of time | Only the capture timestamp exists, so staleness cannot be shown. §9 requires it. |
| M9 | `OverallAssessment.grade` has no vocabulary | The report renders a grade everywhere. |
| M10 | `Recommendation.summary` is optional and unused | §11 depends on the Summary/Thesis distinction being real. |
| M11 | No risk item model | `RiskProfile` describes an asset, not a scored, evidence-linked risk. §13 needs severity, confidence and evidence per risk. |
| M12 | No falsifier model | Invariant 8 requires "what would change this"; nothing produces it. |
| M13 | No report persistence or snapshot model | History (§16) and "change since last report" (§9) are impossible. |
| M14 | No Decision/Action distinction in the models | §14 requires it and there is nowhere to put it. |
| M15 | `AssetProfile` under-dimensioned | §10.5 varies by asset type; the profile cannot currently drive that. |
| M16 | No absence marker in any model | `NOT EVALUATED` / `UNKNOWN` / `UNAVAILABLE` are report tokens with no representation in the domain. |

## Evaluation

| # | Gap | Impact |
| --- | --- | --- |
| E1 | Only `VALUATION` is implemented | Eight of nine categories render `NOT EVALUATED`. |
| E2 | **No risk evaluator at all** | §13 and the risk-before-return ordering have nothing behind them. Highest-value evaluation gap. |
| E3 | `EvaluationResult.failures` is discarded by `ValuationEvaluator` | Failed rules cannot reach the report, so §12's failure block and §10's warnings are unreachable. |
| E4 | No attribution method | Drivers cannot be ordered; rule order is not an order. Blocked on the Constitution. |
| E5 | `OverallEvaluator` is a plain mean with hardcoded confidence | Dilutes risk (§13.1) and makes the overall confidence figure meaningless. |
| E6 | No evidence freshness policy | Staleness cannot be detected, so it cannot be warned about. |
| E7 | No source-agreement handling | Where two sources disagree, nothing records it. |
| E8 | No coverage metric | §10's `collected / used / unavailable` counts and §9's coverage line have no producer. |
| E9 | Normalizer discards scale information | §12 shows raw and normalized side by side; the distinction is currently a no-op. |
| E10 | No mapping from "insufficient evidence" to a decision state | §15.4 assumes such a state exists. Nothing defines it. |
| E11 | No per-rule reference separation | Rule references are merged into the category set, so the Rule → Evidence hop cannot be shown per rule. |

## Recommendation

| # | Gap | Impact |
| --- | --- | --- |
| REC1 | Thesis is a placeholder string | §11's design has no producer. |
| REC2 | No thesis generation from drivers | The thesis must name its dominant drivers and cannot, because drivers do not exist. |
| REC3 | No falsifier generation | Invariant 8 unenforceable. |
| REC4 | No cross-category conflict resolution | Summaries cannot explain tension; the thesis must, and nothing decides how. |
| REC5 | No confidence derivation | Recommendation confidence is copied from the assessment's placeholder value. |
| REC6 | No Decision/Action separation | §14 needs it. |
| REC7 | No "no change" outcome | §14.4 needs it; a decision is always emitted today. |
| REC8 | No plain-language rendering of decision states | The report must not leak enum values; nothing maps them to investor language. |

## Communication

| # | Gap | Impact |
| --- | --- | --- |
| COM1 | One fixed text format shared by five channels | §7.3's renderer contract has no implementation; every channel gets the same string. |
| COM2 | No channel capability model | Bark, PushPlus, ServerChan, WeChat and WeCom differ in length, markup and link support. Nothing encodes this. |
| COM3 | No deep link to a full report | §7.3 requires an omission to be recoverable, and no route exists. |
| COM4 | No truncation or length policy | §15.2's rules are unenforceable today. |
| COM5 | No message schema version | A delivered notification cannot be interpreted later. |
| COM6 | Delivery failures are only logged | The report cannot state whether it was delivered. |
| COM7 | No footer/disclaimer mechanism | §9.3 requires a fixed footer on every report. |
| COM8 | No archive of sent notifications | "Change since last report" has no baseline on the mobile side. |

## Dashboard — frozen

Design deferred. These are recorded so the freeze is explicit and so nothing here is mistaken for
planned work. **No item in this group is scheduled.** See §16.

| # | Gap | Impact |
| --- | --- | --- |
| D1 | `dashboard/` is an empty package | No UI exists, and none is planned. |
| D2 | No report API or route | Panels would have nothing to fetch. |
| D3 | No history store | §16's history panel and §9's change field are impossible. |
| D4 | No chart/trend data model | Score over time needs a series model that does not exist. |
| D5 | No drill-down contract | Panel-to-evidence navigation has no interface. |
| D6 | No persistence of `AnalysisResult` | Each run is discarded; nothing accumulates. |
| D7 | **No carrier chosen, and none to be chosen now** | AIS has no product surface of its own. This is a prerequisite decision, deliberately deferred. Until it is made, the Report Model stays carrier-neutral. |

## Cross-cutting

| # | Gap | Impact |
| --- | --- | --- |
| X1 | No Constitution document | The highest authority referenced throughout does not exist as a file. Every `Blocked` tag resolves here. |
| X2 | No glossary | Confidence, coverage, driver, severity and band are used here with no agreed definition. |
| X3 | No localization decision | The report mixes system values with English prose; the output language is undecided. |
| X4 | No responsible-use policy | What the report may imply to a reader, and what it must disclaim, is unaddressed. |

## Suggested order of work

Two tracks, kept apart on purpose so that the report is not built ahead of the foundations.

### Track 1 — foundations

Nothing in the report can be final until these exist.

| # | Work | Resolves |
| --- | --- | --- |
| 1 | `docs/Constitution.md` | B1, B2, B3, X1 — unblocks the largest number of fields |
| 2 | Evidence layer completed | Supplies the facts, fiscal period, currency and source agreement the report depends on |
| 3 | Overall evaluation completed | Supplies a defined scale and a defensible aggregate |

### Track 2 — the report

| # | Work | Resolves |
| --- | --- | --- |
| 4 | Structured report model plus renderer contract | B4, M1, D2 — turns this document into something that can be built against |
| 5 | Coverage, as-of time and structured warnings | E8, M8, M5 — delivers the three fields §15.5 identifies as non-negotiable |
| 6 | **Resolve CH1–CH5 in one pass**, after Track 1 is complete | The reference chain, with no interim design |
| 7 | Risk evaluator | E2 — gives §13 substance |

Items 6 and 7 come after Track 1 deliberately. Closing the chain breaks early would require exactly
the temporary design §6.4 rules out.

Nothing in the frozen group (§16) appears in this list, and nothing should be added to it until a
carrier is chosen.

---

End of Document
