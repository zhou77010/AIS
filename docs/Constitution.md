# AIS Constitution

Version 0.1 — Vocabulary and semantics

Status: Draft, awaiting approval.

---

## Reading this document

The Constitution is the highest authority in AIS. Where this document, another
document, a comment or an implementation disagree about what something means,
this document wins.

**Version 0.1 defines language, not method.** It says what AIS's words mean and
how its concepts relate to one another. It deliberately does not say how
anything is computed. Everything that would require mathematics is named in
Section 6 and left there on purpose.

The document is intentionally small. It is built up incrementally: v0.1 settles
vocabulary so that later versions can settle method without redefining words
underneath themselves.

**One rule for reading the rest of this file.** If a sentence here begins with
"AIS calculates", it is in the wrong document and should be removed.

---

## 1. Purpose

### 1.1 What AIS is

AIS is an evidence-based investment decision support system.

Its output is a reasoned, traceable judgement of an asset and a recommendation
about it. AIS does not forecast prices and does not emit trading signals.

AIS exists to make a decision **explainable**, so that a person can disagree
with it on the merits. A conclusion a reader cannot trace back to its evidence
has no value here, however accurate it later turns out to be. An unexplained
correct answer teaches nothing and cannot be relied on twice.

### 1.2 What this Constitution governs

- The meaning of every term AIS uses.
- The principles that constrain how AIS reasons.
- The question each category answers.
- The relationships between concepts: what supports what, what produces what,
  and what may not be skipped.
- What is deliberately not yet decided.

### 1.3 What this Constitution deliberately does not govern

- **How anything is computed.** No formulas, no thresholds, no weighting, no
  aggregation, no ranking. Those belong to later versions of this document and
  to nothing else.
- **Which data sources are used, or how they are reached.** That is the Data
  layer.
- **Software structure** — layers, modules, ownership, boundaries. That is
  `docs/Architecture.md`.
- **The shape of a report, and the vocabulary of absence as it is displayed.**
  That is `docs/RecommendationReport.md`, which owns the rendering tokens. This
  document owns what those tokens *mean*.
- **Engineering conventions** — style, testing, commits, configuration. That is
  `AGENTS.md`.

### 1.4 How to use it

- When an implementation and the Constitution disagree about meaning, the
  implementation is wrong.
- When the Constitution is silent, the silence is deliberate. Check Section 6
  before filling it.
- A definition is not a place to add method. Adding methodology means a new
  version of this document, not an edit to a definition.

---

## 2. Core Principles

These are constraints on reasoning. Each one forbids something; none of them
says how to do anything.

**2.1 Evidence Before Opinion.**
No conclusion may appear that evidence does not support. A judgement that cannot
name its evidence is an opinion, and AIS does not publish opinions.

**2.2 Explain Every Decision.**
Every conclusion must be traceable from the conclusion back to the evidence it
rests on, without a missing link. A conclusion whose chain is broken is not a
weak decision, it is not a decision at all.

**2.3 Manage Risk Before Return.**
Risk is established before reward is discussed. A recommendation that cannot
state what would make it wrong is incomplete, regardless of how favourable the
case for it looks.

**2.4 Absence Must Never Become Zero.**
A missing measurement, an unevaluated dimension, and a measured zero are three
different things and must never be presented alike. Zero means "the worst value
measured". It never means "we did not look".

**2.5 Truth Before Precision.**
It is better to say "not available" than to state a plausible number. A false
precise number is worse than an honest gap, because the gap can be seen and the
false number cannot.

**2.6 One Model, Many Renderers.**
There is exactly one report model. Every channel, format and surface is a
projection of it. Two renderings may differ in how much they show and how they
lay it out; they may never differ in what they assert to be true.

**2.7 Simplicity Before Complexity.**
Prefer the simplest thing that satisfies the requirement. Complexity must be
justified by a requirement that exists, never by one that is anticipated.

**2.8 Consistency Before Prediction.**
A method applied consistently is worth more than a method that is occasionally
brilliant. A prediction cannot be validated in advance; consistency can, and it
is what makes results comparable over time.

**2.9 Single Responsibility.**
Each component answers one question. A component that answers two cannot be
reasoned about, tested, or replaced.

**2.10 No Double Counting.**
The same fact is never counted twice in one judgement, and the same definition
never lives in two places. Duplication is how a system comes to disagree with
itself.

---

## 3. Vocabulary

Each term below is defined by what it is, what it is not, and how it relates to
the others. Nothing here is computed.

### 3.1 Evidence

A single checkable fact about an asset, together with where it came from and
when.

Evidence states what is. It never states what should be concluded. The moment a
statement contains a judgement, it has stopped being evidence and become a
conclusion.

Evidence that could not be retrieved is still evidence: it is recorded as
absent, with the reason it is absent. "We asked and the source did not answer"
is a fact about the world and belongs in the evidence.

### 3.2 Evidence Reference

A lightweight identifier pointing at a piece of evidence.

A reference is a handle, not the evidence itself. References are what travel
with a conclusion through the system, so that the conclusion can be traced back
without carrying the evidence along with it.

A reference must never be dropped silently. A reference that points at nothing
is a broken chain, and a broken chain is worse than an openly missing one
because it cannot be seen.

### 3.3 Confidence

How much a claim should be trusted, given the evidence behind it.

Confidence qualifies a **claim**, not an asset. The same asset supports
high-confidence claims about its recent price history and low-confidence claims
about its five-year outlook; that difference is a property of the claims, not of
the company.

Confidence is not certainty, and low confidence is not a negative judgement. It
is a statement about how much weight the claim can bear.

### 3.4 Coverage

How much of what a judgement needed was actually available.

Coverage and Confidence answer different questions and are not substitutes.
Confidence says how much a claim should be trusted; Coverage says how much of
the ground it claims to cover was actually examined. A confident claim over thin
coverage is a weaker claim than the same confidence over complete coverage, and
a reader who sees one without the other is being misled.

Coverage is a statement about completeness, never about quality: full coverage
of poor evidence is still poor evidence.

### 3.5 Severity

How much harm a risk would cause if it came to pass.

Severity describes the consequence alone. It says nothing about whether the
consequence is likely, and it must not be read as doing so.

### 3.6 Likelihood

How probable a risk is.

Severity and Likelihood are two separate questions — how bad, and how probable —
and AIS keeps them separate. They are not interchangeable, and neither one
substitutes for the other.

### 3.7 Driver

The part of the evidence that most affects a conclusion.

A driver is always attributable: given a conclusion, its drivers can be named,
and each names the evidence behind it. Something that cannot be attributed to
evidence is not a driver, however much it feels like the reason.

A driver explains *why* a judgement came out as it did. It is not the judgement
itself and not its size.

### 3.8 Category

One of the fixed angles from which AIS assesses an asset.

The set of categories is defined by this document. Implementations do not add to
it, remove from it, or rename its members. Each category answers exactly one
question, given in Section 4.

A category is a perspective, not a method. Two categories may look at the same
evidence and reach different conclusions, because they are answering different
questions.

### 3.9 Assessment

The structured judgement of an asset.

An assessment is composed of the judgements reached for each category, together
with an overall view of the asset. It is supported by evidence and it is an
opinion about the asset.

An assessment is not advice. It says what AIS thinks of the asset, not what
anyone should do about it.

### 3.10 Recommendation

The position AIS reaches for an asset, together with how confident it is, the
reasoning behind it, and the evidence it rests on.

A recommendation concerns exactly one asset. It never concerns a portfolio, a
person, or a person's circumstances, because AIS does not know them.

### 3.11 Decision

The position chosen for an asset, as expressed by a Recommendation.

A Decision is about an **asset**. It is distinct from an Action (Section 3.17),
which is about a **portfolio**. The same asset can carry the same Decision in two
portfolios while calling for different Actions in each, because the portfolios
hold it differently.

### 3.12 Risk

The exposure to loss, or to being wrong.

Risk has two independent dimensions — Severity and Likelihood — and is supported
by evidence like anything else, so it also carries Confidence and Coverage.

Risk is not only a category. It is also a property of every conclusion: any
conclusion that could be wrong carries risk, and a conclusion presented without
its risk is incomplete.

### 3.13 Score

A number expressing a judgement.

A score has meaning only on a defined scale. A score whose scale is not defined
has no meaning and must be labelled as such wherever it appears; it may still be
displayed, but only with that label.

Scores from different categories are not comparable with one another unless the
scale says they are. Displaying them side by side does not make them comparable,
and a reader is entitled to assume they are.

### 3.14 Report

The complete, structured statement of an assessment and its recommendation.

There is exactly one report model. Everything a reader sees is a projection of
it. A report is not a format; it is the thing formats are made from.

### 3.15 Renderer

A component that turns a Report into text for a particular kind of reader.

A renderer decides how much of the report to show and how to lay it out. It does
not decide what is true, and it does not reach for facts the report does not
carry. If a renderer needs something the report lacks, the report is
incomplete — that is a gap to be closed, not a licence to fill it locally.

### 3.16 Transport

A component that carries an already rendered report to a destination.

A transport does not know what a report is. It moves text, reports whether the
text arrived, and does nothing else. A transport that builds content has stopped
being a transport.

### 3.17 Portfolio, Action

A **Portfolio** is a set of holdings with their weights, measured in a base
currency. A portfolio is state: it describes what is held, not what should be.

An **Action** is a proposed change to a portfolio. Actions are about portfolios
the way Decisions are about assets. An Action without a stated constraint is not
explainable, because the reason a position is the size it is is usually the
constraint that bound it.

### 3.18 States of absence

AIS distinguishes several kinds of "not there". They are different facts and
must never be collapsed into one another, nor into a number.

- **An unevaluated dimension** — no judgement was formed. Nothing is known about
  it, not even that it is safe.
- **An unknown dimension** — the dimension exists and was not examined. This is
  not the same as a dimension found to be acceptable.
- **An unavailable input** — the source was asked and did not provide it. The
  reason is part of the record.
- **A non-applicable question** — the question does not arise for this asset or
  this portfolio. This is not a gap.
- **Insufficient evidence for a decision** — the evidence available cannot
  support any position. This is an outcome, not a failure.

The words used to display these states are owned by
`docs/RecommendationReport.md`. What they mean is owned here.

---

## 4. Category Definitions

Each category answers exactly one question. Defining the question is the whole
of what this document does for a category; how the question is answered is
method, and method is deferred.

The order below carries no meaning. Presentation order is defined once, for
every renderer, in `models/category.py`.

**Market** — What is the environment in which this asset is being judged?

**Fundamental** — What is the business, and is it financially sound?

**Valuation** — What is being paid, relative to what the business delivers?

**Trend** — What has the price actually been doing, over a window that is
stated?

**Risk** — What could make this judgement wrong, and how badly?

**Catalyst** — What identifiable event could change this picture, and when?

**Positioning** — Who else holds this asset, and how crowded is that?

**HPO** — *Not yet defined.* See Section 6. Until this document defines it, the
name is carried verbatim and no meaning is assigned to it.

**Earnings** — What have the reported results said, and what are they expected
to say next?

---

## 5. Relationships

This section states how the concepts connect. It contains no implementation and
no ordering rules beyond what the meaning of the concepts requires.

### 5.1 The chain

```
Evidence
  → Rules
    → Scores
      → Assessment
        → Recommendation
          → Report
            → Renderer
              → Transport
```

Each link has one meaning:

- **Evidence supports Rules.** A rule reads evidence. A rule that reads anything
  else is not a rule.
- **Rules produce Scores.** A rule states a measurement; a score is that
  measurement on a scale.
- **Scores support Assessment.** An assessment is formed from the judgements of
  the categories, and category judgements are formed from scores.
- **Assessment produces Recommendation.** A recommendation is drawn from an
  assessment and introduces no fact the assessment does not contain.
- **Report expresses Recommendation.** The report is the complete statement of
  the assessment and its recommendation.
- **Renderer projects Report.** A renderer shows part or all of the report,
  arranged for a reader.
- **Transport carries the rendered report.** Nothing downstream of a renderer
  changes what was rendered.

The chain is directional. No link may reach forward to a later one, and no link
may bypass an earlier one.

This is the asset-level chain, and it is what this document governs. Two details
of the business rule pipeline in `docs/Architecture.md` are consistent with it
and are named here so that the two documents cannot be read as disagreeing: a
category judgement stands between a score and the assessment that contains it,
and the chain continues beyond this document into the portfolio dimension, where
a Decision leads to an Action. That continuation is deferred (Section 6).

### 5.2 Standing relationships

- **A category is answered from evidence.** No category may be answered from
  another category's conclusion.
- **Categories are peers.** No category ranks above another in authority. Where
  two disagree, the disagreement is information and must not be silently
  resolved by discarding one.
- **A Recommendation belongs to exactly one asset.** Any statement about more
  than one asset is a different kind of statement and must not be presented as a
  Recommendation.
- **A Decision is about an asset; an Action is about a portfolio.** Neither
  substitutes for the other, and a reader must always be able to tell which one
  they are looking at.
- **Risk attaches to conclusions, not only to a category.** Any conclusion can
  be wrong, so risk is not something that only the Risk category carries.
- **Confidence and Coverage qualify a claim.** Both may attach to a claim, and
  neither replaces the other.
- **Evidence References are what survive.** A conclusion travels through the
  system carrying references, never carrying a private copy of the evidence.

### 5.3 What may not be skipped

- A conclusion with no evidence behind it.
- A score with no rule behind it.
- A recommendation with no assessment behind it.
- A claim presented without the coverage that qualifies it.
- A missing input presented as a value.
- A dimension that was not examined presented as one that was found acceptable.

---

## 6. Deferred Decisions

The following are **intentionally deferred, not missing**. Each is named here so
that its absence is a recorded decision rather than an oversight, and so that no
implementation fills the gap locally and silently.

While these are open, the corresponding outputs are labelled as undefined
wherever they appear. That label is not a placeholder for future polish; it is
the honest state of the system.

| Deferred | The question it will settle | Safe to defer because |
| --- | --- | --- |
| **AIS Standard Score** | What scale scores live on, and what makes two scores comparable. | Measurements can be recorded on their own scale now and normalized once the scale exists; the reverse is not true. |
| **Decision Thresholds** | Where the boundaries between decision states lie. | A decision state can be reached and shown without the boundaries being final, as long as the reader is told they are provisional. |
| **Risk Methodology** | How Severity, Likelihood and evidence combine into a risk judgement, and how risk constrains a Decision. | Risk can be described by its dimensions first. What remains deferred is how those dimensions are combined and how far risk may override a conclusion. |
| **Confidence Aggregation** | How confidence in parts becomes confidence in a whole. | Per-claim confidence is meaningful on its own; only the aggregate is deferred, and an aggregate that is not yet defined must not be invented. |
| **Driver Attribution** | How the contribution of a driver is measured, and how drivers are ordered. | Drivers can be named before they can be ranked. Until ranking exists, drivers are listed in a stated order and never presented as ranked. |
| **Portfolio Optimization** | How an Action is derived from a Decision, a portfolio and its constraints. | Decisions are useful without Actions, and an Action derived from an undefined rule would be worse than none. |
| **The definition of HPO** | What question the HPO category answers. | Nothing may be assumed about a category whose question is unknown. It is carried verbatim and assigned no meaning until this document defines it. |

Two further questions are known to be open and are not yet mature enough to list
with the above. They are recorded so that they are not discovered again as
surprises: whether risk may override a Decision rather than merely qualify it,
and how results are compared across assets that are not measured in the same
currency.

---

End of Document
