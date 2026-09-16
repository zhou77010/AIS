# AIS Constitution

Version 0.2 — Vocabulary, semantics and risk dimensions

Status: Frozen, version 0.2.

Version history:

- **0.1** — vocabulary and semantics. Sections 1 to 4.
- **0.2** — risk dimensions. Adds Section 5, defining the kinds of uncertainty an
  investment thesis can fail from. No method, no evidence, no scale.

---

## Reading this document

The Constitution is the highest authority in AIS. Where this document, another
document, a comment or an implementation disagree about what something means,
this document wins.

**Version 0.1 defines language, not method.** It says what AIS's words mean and
how its concepts relate to one another. It deliberately does not say how
anything is computed. Everything that would require mathematics is named in
Section 7 and left there on purpose.

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
- When the Constitution is silent, the silence is deliberate. Check Section 7
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

**2.11 No Invented Semantics.**
A name carries only the meaning this document has given it. Where a meaning has
not been specified, none may be supplied by inference, by analogy, by what the
name resembles, or by what would be convenient — not in code, not in a report,
and not in commentary about the system.

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

The kinds of uncertainty that risk is about are a separate, fixed set, given in
Section 5. Severity and Likelihood describe *how bad* and *how likely*; the
kinds of uncertainty in Section 5 describe *about what*.

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

**HPO** — If capital were available today, is this one of the highest probability
opportunities worth allocating to? It is a synthesis of the other categories
rather than a reading of the asset. See Section 4.1.

**Earnings** — What have the reported results said, and what are they expected
to say next?

### 4.1 HPO — the category that answers a question about capital

`HPO` is a member of the set like the other eight, and it is unlike them in one
respect: the other eight ask what is true of the asset, and HPO asks whether what
is true of it makes it worth allocating capital to today.

**The question.**

> If capital were available today, is this one of the highest probability
> opportunities worth allocating to?

**What it is not.** It is not a judgement of business quality, which is
Fundamental's question. It is not the overall score, which combines the
categories on a scale that is not defined. It is not a Recommendation, which says
what to do. It is not a measure of how good the asset is; it is a judgement of
whether today is a time to prioritise it.

**It is a synthesis, not evidence.** HPO reads the results the other categories
have already reached. It re-reads no evidence and consults no source. This is the
only category of which that is true, and it is what synthesis means here: a
judgement about judgements, which is only legitimate while the judgements it
reads stay traceable to their own evidence.

**It is never an input to anything.** No other category may read HPO, and it may
not be folded back into the categories it was built from.

**The name is authoritative.** `HPO` is written `HPO` in code, in reports and in
every document. It is not abbreviated, renamed or paraphrased anywhere.

**No semantics beyond this question may be invented.** The question above is
frozen. How it is answered is method, and method is deferred exactly as it is for
every other category: nothing in AIS may settle a weight, a threshold or a scale
for HPO that this document does not state.

**What it shows as an output.** HPO answers a question, so a judgement can be
formed for it and it is shown as judged. When a category it reads has no grade,
it reports that condition as not judged — which is the state of absence from
Section 3.18 — rather than treating it as having failed.

**How it can change.** The question is fixed. Everything about how it is answered
is provisional until the AIS Standard Score defines what a category reading
means.

---

## 5. Risk Dimensions

### 5.1 What a risk dimension is

A **risk dimension** names a kind of uncertainty that can invalidate an
investment thesis.

Risk itself is a category (Section 4) and asks one question. The dimensions are
the kinds of uncertainty that question is about. A judgement of Risk that names
no dimension is incomplete, because it does not say what it is a judgement
*about*.

Dimensions are semantic. They are fixed by what they mean, not by how they are
assessed. The set is closed: implementations do not add to it, remove from it, or
rename its members.

**A dimension is never named for a measurement.** A measurement may later serve
as evidence for a dimension; it is never the dimension. The moment a risk is
defined by the data that happens to observe it, the dependency has run backwards,
and the definition will change whenever the data source does. Which evidence
supports which dimension is an implementation decision, made downward from these
meanings — never upward from what happens to be available.

The order below carries no meaning, and no dimension ranks above another.

### 5.2 The dimensions

**Business Risk** — the possibility that the business does not do what the thesis
assumes it will do. It concerns operating performance: whether the business sells
what it is assumed to sell, competes as it is assumed to compete, and executes as
it is assumed to execute.

**Financial Risk** — the possibility that the business's finances cannot support
it, or cannot support the assumption. It concerns how the business is funded and
whether it can meet what it owes. It is about the money, not about the trade.

**Valuation Risk** — the possibility that the price already assumes more than
will be delivered. A sound business bought at a price that requires everything to
go right carries this risk, and no other dimension on this list has to
materialise for the thesis to fail.

**Market Risk** — the possibility that the asset moves against the holder for
reasons that have nothing to do with the business. It concerns the environment
the asset is held in rather than the asset's own merits, so it can invalidate a
correct thesis without the thesis being wrong.

**Event Risk** — the possibility that a discrete occurrence changes the picture.
It is distinct from the dimensions above because it is a step change rather than
a drift: something happens, at a time, and afterwards the situation is different.

**Liquidity Risk** — the possibility that the position cannot be entered or
exited on the terms the thesis assumes. A thesis that cannot be acted on is not an
available thesis, however sound its reasoning.

**Evidence Risk** — the possibility that what the thesis rests on is wrong, no
longer current, or insufficient to support it. This is the dimension that
separates a thesis that is uncertain from a thesis that is unfounded, and it is
the one AIS is uniquely placed to be honest about.

**Horizon Risk** — the possibility that the thesis is right, but not within the
time it is needed. To whoever must hold the position in the meantime, being early
is indistinguishable from being wrong.

### 5.3 Rules

- **A dimension is never asserted without evidence.** A named risk is a claim,
  and a claim follows Section 2.1 like any other.
- **A dimension not examined is unknown, never absent.** A dimension that was not
  assessed is not a dimension found to be acceptable (Section 3.18).
- **A dimension that does not apply is not a gap.** Some dimensions do not arise
  for some assets. Non-applicability is a state, not a missing value.
- **A source of uncertainty is not a dimension.** Many things can go wrong within
  one dimension. Naming each of them would turn a closed set of meanings into an
  open list of topics, and an open list cannot be reasoned about.
- **Severity and Likelihood apply to every dimension.** They describe how bad and
  how likely; they do not merge one dimension into another.
- **How dimensions are assessed, combined, or permitted to constrain a decision
  is not defined here.** See Section 7.

---

## 6. Relationships

This section states how the concepts connect. It contains no implementation and
no ordering rules beyond what the meaning of the concepts requires.

### 6.1 The chain

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
a Decision leads to an Action. That continuation is deferred (Section 7).

### 6.2 Standing relationships

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

### 6.3 What may not be skipped

- A conclusion with no evidence behind it.
- A score with no rule behind it.
- A recommendation with no assessment behind it.
- A claim presented without the coverage that qualifies it.
- A missing input presented as a value.
- A dimension that was not examined presented as one that was found acceptable.

---

## 7. Deferred Decisions

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
| **Risk Methodology** | How Severity, Likelihood and evidence combine into a judgement of each risk dimension, and how risk constrains a Decision. | Version 0.2 fixed *which* kinds of uncertainty exist (Section 5), so a dimension can now be named and described. What remains deferred is how each is assessed, how they combine, and how far risk may override a conclusion. |
| **Confidence Aggregation** | How confidence in parts becomes confidence in a whole. | Per-claim confidence is meaningful on its own; only the aggregate is deferred, and an aggregate that is not yet defined must not be invented. |
| **Driver Attribution** | How the contribution of a driver is measured, and how drivers are ordered. | Drivers can be named before they can be ranked. Until ranking exists, drivers are listed in a stated order and never presented as ranked. |
| **Portfolio Optimization** | How an Action is derived from a Decision, a portfolio and its constraints. | Decisions are useful without Actions, and an Action derived from an undefined rule would be worse than none. |

**Recorded blocker on the AIS Standard Score.** Until the scale exists, scores
are aggregated as raw measurement values, and different categories measure in
different directions: a valuation rule reports a larger number for a more
expensive asset, while a risk rule reports a larger number for a riskier one.
The overall score treats a larger number as more favourable, so a measured risk
currently raises the overall score rather than lowering it.

This is recorded as a blocker rather than worked around. Normalizing, weighting
or inverting any measurement to compensate would be inventing the scale this
entry defers, and an invented scale is harder to detect than a known-broken one.
The report labels every affected score as undefined until the scale is defined.

HPO is no longer a special case of this table. Its question was fixed by an
explicit design decision and is recorded in Section 4.1; what remains deferred
about HPO is the same thing that is deferred about every category, which is how
its question is answered.

Two further questions are known to be open and are not yet mature enough to list
with the above. They are recorded so that they are not discovered again as
surprises: whether risk may override a Decision rather than merely qualify it,
and how results are compared across assets that are not measured in the same
currency.

---

End of Document
