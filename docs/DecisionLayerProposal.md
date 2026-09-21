# AIS Decision Layer Proposal v1

**Status: draft, not ratified, no authority.** This document proposes method. Until it
is accepted it changes nothing: the Constitution remains the highest authority, the
Runtime remains frozen, and no implementation may read a sentence here as a
specification. Its purpose is to be disagreed with on the merits.

**What it contains.** Method only. No code, no thresholds to be implemented, no file
names except where the Constitution already names them. Section 7 of the Constitution
lists six decisions as deliberately deferred; this proposal answers each of them
directly and says which of its own answers cannot be settled without Observation data.

---

## 0. Why a Decision Layer, and why it is not the current score

The Runtime today produces a number called an overall score by averaging raw measurement
values twice — once inside a category, once across categories — and maps that number onto
a decision state through a table whose thresholds start at 40. Measured on real runs:

| What was measured | Result |
| --- | --- |
| Overall scores recorded | min **-119.11**, max **25.25**, median **4.62** |
| Decision states recorded | **444 of 444 were `watch`** |
| Why | the lowest non-`watch` threshold is 40, which the scale cannot reach |

The Constitution already records why: §7 states the scale is undefined, and records as a
blocker that "a measured risk currently raises the overall score rather than lowering
it". The score is therefore not a weak judgement; it is **not a judgement at all** — it
is arithmetic standing where a method will go.

**So the Decision Layer is not an improvement to the score. It is the replacement of an
aggregate number by a stated method.** Two consequences follow, and both shape everything
below:

1. **The answer is not a better formula.** The Constitution forbids AIS to publish a
   conclusion that cannot name its evidence (§2.1) or explain itself without a missing
   link (§2.2). A weighted sum can name neither the weight's justification nor the
   disagreement it discarded.
2. **No weights may be invented here.** §1.3 puts computation — formulas, thresholds,
   weighting, aggregation, ranking — outside what the Constitution currently governs, and
   §7 defers it explicitly. This proposal does not fill that gap by convenience: where it
   proposes a rule, it says so, and where it needs a number, it says what that number
   would have to be justified by.

---

## 1. How the AIS Standard Score is produced

### 1.1 What the Standard Score is

**The Standard Score is a scale, not a calculation.**

The Constitution's §3.13 says a score "has meaning only on a defined scale", and that
scores from different categories are not comparable "unless the scale says they are".
That sentence is the whole requirement: what is missing is not a formula that combines
numbers, it is **a definition of what the numbers mean**.

So this proposal defines the AIS Standard Score as:

> A **five-step ordinal scale**. Each step has a name and a stated meaning. Every
> measurement AIS reads is mapped onto that scale by a **stated rule with named anchors**
> and a **declared direction**. Every judgement above a measurement — a category reading,
> a risk dimension, a decision state — is expressed using those steps and their names, and
> never as an unlabelled number.

Three properties are required of it by the Constitution, and each one closes something
currently open:

| Property | Which Constitution rule requires it | What it closes |
| --- | --- | --- |
| **Ordinal, with named steps** | §3.13 a score's scale must be defined | The overall score's undefined scale |
| **Direction declared per measurement** | §7 blocker: risk currently lifts the score | The blocker, rather than working around it |
| **Comparable across measurements** | §3.13 comparability must be stated, not assumed | Any cross-category aggregation |

### 1.2 The three layers of the score

**Layer 1 — the measurement reading.** One measurement, one stated mapping onto the five
steps. Two kinds of anchor, and the difference matters:

- **Ordinal anchors with a stated reason**, where the number has a meaning independent of
  whom it is compared to. A trailing multiple, a margin, a leverage ratio, an annualised
  volatility: these read the same in any universe, and the anchors are argued from what
  the number measures.
- **Relative anchors against a declared population**, where no such meaning exists. How
  crowded a position is, how large an earnings surprise is, how a sector moved against the
  market: each of these is only meaningful *relative to something*, and that something
  must be named — which population, which window, and why.

**The rule that makes this honest.** An anchor is a claim about what a number means, so it
must be arguable. Every anchor carries: the step it defines, the value, and the reason it
sits there. An anchor without a reason is a preference, and a preference is what the
Constitution's §2.11 forbids AIS to smuggle in as a meaning.

**Layer 2 — the category reading.** A category's measurements read together. **Not an
average.** This proposal replaces the mean with a rule of the form:

> A category's reading is a pair — its **middle** and its **weakest** — and its step is
> **capped by what the weakest allows**.

The reason is not taste. The current implementation averages, and the effect is visible:
a category can read well while holding a measurement that disqualifies it, which is
exactly the failure `evaluation/reading/conditions.py` was written to stop — a valuation
whose multiples are generous averages out to attractive beside a cash flow that does not
support it. A cap makes the sentence and the step agree by construction: **nothing can
read better than its worst member permits.**

**Layer 3 — the overall view. This proposal recommends there be no overall number.**

The Constitution says categories are peers and that "where two disagree, the disagreement
is information and must not be silently resolved by discarding one" (§6.2). Any single
aggregate does exactly that: it discards which categories disagreed. It also requires
weights, and a weight is a statement about how much one category matters relative to
another — a statement the Constitution does not make and this proposal will not invent.

What replaces it is a **structured overall view**:

- the step reached by each category, named;
- the **named disagreements** — which categories point differently, stated rather than
  averaged away;
- the **risk verdict** (Section 3 below);
- the **decision state** reached from those, by the rules in Section 2.

A reader of that view can disagree with a specific part of it, which is the whole point of
§1.1: "so that a person can disagree with it on the merits".

### 1.3 What the Standard Score still needs, and cannot be given now

Two of the three layers can be specified without data. The anchors in Layer 1 cannot be
finalised for the relative measurements until Observation says where the values actually
fall — an anchor placed before seeing the distribution is a guess wearing a table.

---

## 2. The decision states, and the logic that reaches them

### 2.1 What a decision state is, and what it is not

§3.11: a **Decision** is the position chosen **for an asset**. §3.17: an **Action** is a
proposed change to a **portfolio**. §1.1: AIS "does not forecast prices and does not emit
trading signals".

So a decision state is **a statement about the asset**, never about a portfolio, a
quantity, a price level or a moment to trade. This has one consequence that has to be
settled before the states can be defined:

> **BUY and ACCUMULATE cannot mean "start a position" and "add to a position",** because
> that difference is portfolio state, and a Decision does not know the portfolio.

This proposal therefore defines them as **two intensities of the same asset-level
statement**, and flags the alternative in Section 6.

### 2.2 The six states

| State | Meaning as an asset-level position | What must be true |
| --- | --- | --- |
| **BUY** | The asset currently merits a position, on the strongest reading AIS reaches: the case is established, the risk is acceptable, and nothing about the entry is being waited for. | Every required condition holds **and** no disqualifier applies **and** no risk dimension blocks |
| **ACCUMULATE** | The asset merits a position and merits it being built rather than taken at once: the case is established but something about it is still forming — a condition that holds weakly, or a stated event still ahead. | The required conditions hold, at least one of them weakly, with a named reason for the gradual reading |
| **HOLD** | The asset merits a position at the weight it has, and nothing warrants changing it. This is the state of a case that is intact and unremarkable. | The case stands and the risk is acceptable, with no reason to build or reduce |
| **TRIM** | The asset no longer merits the position it is likely to carry: the case is weaker than it was or the price already assumes more, but it has not failed. | A named deterioration in a condition that previously held, **not** a price move |
| **SELL** | The case for holding the asset is gone, and the reason is nameable. | A named disqualifier: the thesis the position rests on no longer holds, or a risk dimension reads as unacceptable |
| **WATCH** | No position is warranted, and the reason is that the evidence does not reach a position — including "we have not looked" and "what we have cannot support any position". | §3.18's state of absence: not a failure, an outcome |

**`WAIT` is in the code today and in no document's vocabulary.** It is either folded into
WATCH or defined as "the case is forming and a named event will settle it". It needs a
ruling (Section 6).

### 2.3 The logic: three gates, no weights

Every state is reached through three gates, applied in order. No gate has a weight, and
none of them computes a total.

**Gate 1 — Is there enough evidence to hold any position at all?**
If the coverage of the judgements a state depends on falls below a stated floor, the
answer is **WATCH**, with the missing inputs named. This is `§3.18`'s "insufficient
evidence for a decision", and it is where **43.8% of measured runs currently land**: they
judge nothing at all, and under the current placeholder they are reported as `watch`
anyway — by accident rather than by rule.

**Gate 2 — Does any risk dimension block?**
A risk dimension judged unacceptable **blocks the favourable states** (BUY, ACCUMULATE)
and permits the unfavourable ones (HOLD, TRIM, SELL). It does not by itself force a
SELL, and it does not size anything.

> **This answers the Constitution's open question** — "whether risk may override a
> Decision rather than merely qualify it" — with: **risk may block, and may not size.**
> §2.3 ("Manage Risk Before Return") is satisfied because risk is consulted before the
> favourable states are considered; §3.17 is satisfied because sizing stays with the
> portfolio layer. Risk that could size a position would be the Portfolio Optimization
> decision §7 defers, arriving through a side door.

**Gate 3 — Do the required conditions hold?**
Each state names a **stated set of conditions** that must hold for it. This is where the
current design has to change in kind rather than degree:

> **The favourable states must not require every condition to hold.** A design that does
> is not strict, it is inert: measured over 272 real judgements, the top grade — every
> judged condition holding — occurred **zero times**, and the conditions hold at wildly
> different rates (risk 62.7%, trend 24.0%, valuation 21.0%). A bar nothing can clear is
> not a high standard; it is a design that says nothing.

What each state requires is a **named subset**, with the pairing argued rather than
counted, e.g. "BUY requires valuation and trend, or valuation with risk and a near-term
catalyst" — and every such pairing is a Constitution-level statement, not a tuning knob.

### 2.4 Disqualifiers

A single named fact may disqualify a state outright, with the reason recorded. Candidates,
each needing ratification:

- **Evidence risk** — the measurement a condition rests on is stale, or was never
  retrieved, or contradicts another. A condition that holds on evidence that is not
  current does not hold (§2.5 "Truth Before Precision").
- **Liquidity risk** — the position cannot be entered on the terms the thesis assumes
  (§5.2). A thesis that cannot be acted on is not an available thesis.
- **Non-applicability** — a question that does not arise for this asset (§3.18) must not
  be read as a condition that failed, nor as one that passed.

---

## 3. How the Decision Layer relates to the other four

### 3.1 Opportunity (HPO)

HPO asks whether this asset is worth prioritising **today**, among the things AIS looks
at. It is the ordering question, and it is what Today Priority is.

**This proposal recommends that the Decision Layer not read HPO.** §4.1 is explicit: HPO
"is never an input to anything. No other category may read HPO". A decision derived from
HPO would make HPO an input, and would also make the decision inherit the ordering policy
— which is an editorial choice about attention, not a judgement about an asset.

**What the Decision Layer may share with HPO is its inputs, not its answer.** HPO reads
the category judgements; so does the decision. Two consumers of one set of judgements is
not double counting (§2.10); one consumer reading the other's conclusion is.

### 3.2 Risk

Risk is both a category and a property of every conclusion (§3.12). The proposal gives it
two distinct roles and keeps them apart:

- **as a category**: it is judged like any other and can hold or fail like any other
  condition;
- **as a property of the decision**: Gate 2, where an unacceptable dimension blocks the
  favourable states.

The eight risk dimensions of §5.2 are the vocabulary for both. **Severity and Likelihood
remain two questions** (§3.5, §3.6) and are not merged into one risk number by this
proposal — §7 defers how they combine, and this proposal does not answer that.

### 3.3 Portfolio

The Portfolio layer owns **Actions and size** (§3.17, and §7's deferred Portfolio
Optimization). The Decision Layer therefore:

- **never states a quantity**, a percentage, or a number of shares;
- **never reads the portfolio** to decide a state — otherwise one asset would carry
  different Decisions in two portfolios, which §3.11 forbids;
- hands the portfolio layer a state plus its constraints, and the portfolio layer decides
  the Action.

**The position limit the interim strategy referred to is therefore an Action constraint**,
and it belongs in the Portfolio layer's configuration, not in the decision state.

### 3.4 Market

Market answers "what is the environment in which this asset is being judged" (§4). It is a
category like the others: it may hold or fail as a condition, and it may **qualify** a
judgement's confidence and coverage. It may **not** veto a Decision on its own — no
category outranks another (§6.2), and a market-level veto would be exactly that.

That deliberately leaves one question open, flagged in Section 6: whether a hostile
environment may **cap** the favourable states for an asset whose own reading is strong.
The argument for capping is that a decision made in a hostile environment has a different
failure mode; the argument against is that it lets one category outrank those it is a peer
of. It is a Constitution-level question, not an implementation one.

---

## 4. What belongs to the Constitution, and what belongs to the Runtime

The dividing line already exists in the Constitution, and this proposal only applies it.

**The Constitution owns** (as a version 0.3, since §1.4 says method arrives as a new
version and never as an edit to a definition):

1. **The Standard Score's properties and step meanings** — that it is a five-step ordinal
   scale, what each step means, and that direction is declared per measurement.
2. **The decision state vocabulary and the meaning of each state** — including the ruling
   that BUY and ACCUMULATE are intensities rather than portfolio operations.
3. **The three gates and their order**, the rule that risk blocks but does not size, and
   the requirement that a disagreement between categories is stated rather than averaged.
4. **What each state requires**, as named conditions — because a threshold or a condition
   list is method, and method is the Constitution's (§1.3).
5. **The absence mapping** — which of §3.18's states produces which decision state.

**The Runtime owns** (and may not extend):

1. **Retrieval and sequencing** — which source, when, in what order.
2. **The anchor values themselves**, implemented verbatim from the ratified table, with a
   test asserting the code and the table agree. The code is the implementation of the
   Constitution's table, never the place the table is decided.
3. **Rendering** — how much of the report a reader sees, and in what layout. Never what is
   true.
4. **Operational policy** — when reports are sent, retries, state files, schedules.

**The rule that keeps the line honest.** A Runtime component may not introduce a meaning.
Every anchor, every condition list and every state boundary must be traceable to a
ratified sentence. Where the Runtime needs something the Constitution does not state, the
correct output is a gap in the report and an entry in the Backlog — which is what the
current code does with the DCF fair value and with guidance, and it is right to.

**Where the ratified anchors physically live.** Proposal: an **Annex to the Constitution**
(a table of measurement, step, value, reason), versioned with it, and implemented in the
Reading Layer. One owner, one copy, and a test that fails if the two drift. The
alternative — writing every anchor into the Constitution's prose — is rejected: the
Constitution stays small on purpose (§"Reading this document"), and an annex is citable
without being prose.

---

## 5. What Observation can settle, and what can be decided now

### 5.1 Decidable now, with no data

| Decision | Why it does not need Observation |
| --- | --- |
| The Standard Score is an ordinal scale with named steps | It is a definition, not a distribution |
| Direction is declared per measurement | The §7 blocker is a defect of assumption, not of data |
| A category is capped by its weakest measurement | It closes an observed contradiction, not a statistical question |
| There is no overall number; disagreements are stated | It follows from §6.2 and from the absence of ratified weights |
| The three gates and their order | Reorders existing judgements; adds no threshold |
| Risk blocks and does not size | It is the Constitution's own open question, answerable by principle |
| Insufficient evidence produces WATCH | §3.18 already defines the state of absence |
| The Constitution/Runtime split and the annex mechanism | Structural, not empirical |
| The Decision Layer does not read HPO | §4.1 already forbids it |

### 5.2 Needs Observation before it can be settled

| Question | What the data has to show | What exists today |
| --- | --- | --- |
| **Every anchor for a relative measurement** | Where the values actually fall, and whether the steps separate anything | Nothing. The two newly connected measurements are ungraded and unobserved |
| **The coverage floor for Gate 1** | How much of the required evidence is normal, and how often it is absent | **43.8% of runs judge nothing at all** — so the floor is currently the most consequential unknown |
| **Which conditions can hold together** | Co-occurrence, so that the required subsets are reachable | Risk holds 62.7%, trend 24.0%, valuation 21.0%; the full set never holds |
| **Whether the scale discriminates** | Whether assets spread across the steps, or cluster in the middle | Unknown. A scale that never leaves the middle has not been read |
| **Stability across days** | Whether a step means the same thing in two weeks | Unknown, and the reason the Evidence Maturity Rule exists |
| **The base rate of each decision state** | Whether a state is reachable at all, and how often | Only the placeholder's `watch` has ever been produced |

### 5.3 What this means for the sequence

**The interim paper-trading plan is correctly postponed.** It would have measured a
hand-written trigger against thresholds that do not exist yet, and its result could not
have been attributed to AIS. The order that follows from the above is:

1. **Observation continues, unchanged** — it is the input to Section 5.2.
2. **The methodology in this proposal is argued and frozen** — Sections 1 to 4.
3. **The anchors are placed from the observed distributions** and ratified into the annex.
4. **Then** the paper-trading validation, which by that point measures a method rather
   than a placeholder.

---

## 6. What this proposal does not answer, and where it needs a ruling

Numbered so they can be answered one at a time. Each is a Constitution-level decision, not
a preference to be settled in code.

1. **BUY versus ACCUMULATE.** Defined here as two intensities of one asset-level
   statement. The alternative — that they differ by whether a position exists — requires a
   Decision to read the portfolio, which §3.11 forbids. Confirm the intensity reading, or
   propose the amendment that makes the alternative constitutional.
2. **`WAIT`.** Folded into WATCH, or given a meaning (a named event will settle the case)?
3. **May a hostile Market cap the favourable states?** Section 3.4 sets out both sides. As
   written, no category outranks another; capping would be an exception, and an exception
   should be stated as one.
4. **How Severity and Likelihood combine.** §7 defers this; the proposal deliberately does
   not answer it, and Gate 2 needs an answer before it can be implemented as more than
   "a dimension is unacceptable".
5. **What "unacceptable risk" means.** A step on the scale? A named dimension? An
   aggregation of several? This is the Risk Methodology item §7 defers, and Gate 2 gates
   everything on it.
6. **The required condition sets for each state** (§2.3, Gate 3). Named subsets, argued
   pairings. This is the substance of the method and belongs to you.
7. **The coverage floor** (§2.3, Gate 1) — the one number this proposal knows is needed
   and refuses to guess, because 43.8% of current runs would fail any floor above it.
8. **TRIM and SELL must be reachable without a price trigger.** AIS does not forecast
   prices and does not emit trading signals (§1.1), so "it went up 20%" may not be a
   reason. What *is* a reason — a condition that stopped holding, a risk dimension that
   became unacceptable, a valuation that moved to the bottom step — needs to be named
   before these states can be implemented at all.

---

## 7. Summary of what changes, and what deliberately does not

**Changes, if ratified:**

- The undefined overall score is **retired rather than repaired**: no aggregate number,
  no weights, the disagreements stated instead.
- A category's step is **capped by its weakest measurement** rather than averaged.
- Decision states are reached through **three gates** with no weights, and risk **blocks**
  rather than sizes.
- The favourable states require **named subsets** of conditions, not unanimity — because
  unanimity was measured at zero occurrences.
- Thresholds, condition lists and step meanings become **Constitution content**, with the
  Runtime implementing a ratified annex verbatim.

**Deliberately unchanged:**

- No new Category, no new evidence, no new source, and no change to the Runtime while the
  Observation Phase is running.
- The Evidence Maturity Rule stands: nothing enters the score that has not first been
  observed, graded, and reviewed.
- The Runtime's freeze in force today is not lifted by this document. It is a proposal to
  be argued, and the argument comes before the code.

## 8. Rulings in force, and what stays open

Recorded after discussion. **A ruling binds implementation; it is not a frozen
methodology.** Nothing in this section may be treated as settled method until the Decision
Layer is frozen, and no code may implement any of it while the Observation Phase is
running.

| # | Item | Status | Ruling |
| --- | --- | --- | --- |
| 1 | **Overall Score** | **Ruled: freeze the discussion, implement nothing** | The current aggregate is not used as a judgement and is not restored. It stays in the code as the labelled placeholder it is, and it is neither retired nor replaced. **A Decision is the final conclusion. An Overall, if one ever exists, is an expression of a Decision and never a source of one.** What Overall should be is decided after the Decision Layer exists. |
| 2 | **BUY / ACCUMULATE** | **Open: the intensity reading is rejected, a new one is not yet found** | Rejected: that the two states express whether the case has formed — the state of a case is already expressed by evidence, Catalyst and Confidence, and a state that repeats them says it twice (§2.10). Retained as direction: the Decision Layer judges the asset; execution belongs to the Portfolio Layer. **A Decision never knows what is held; an Action does.** The question stays open and needs more work. |
| 3 | **Confidence** | **Ruled in part, open in part** | Ruled: no overall confidence is invented now (§7 defers its aggregation). Open, and named as the next question: AIS must eventually answer **"why do I believe this judgement?"**, not necessarily as a percentage, possibly as a structured explanation — and that answer is a **core part of the Decision Layer rather than an attachment to it**. But Confidence is not to remain a property of local evidence only. **First step: define the sources that lower Confidence. No algorithm, no threshold, no number.** |
| 4 | **Portfolio Layer boundary** | **Ruled: accepted as a candidate Constitution principle** | The Decision Layer answers **what the world is like**; the Portfolio Layer answers **what to do in this account**. **A constraint may never modify a Decision.** Insufficient cash, a position limit, a currency or any other constraint changes the Action and leaves the Decision standing, with the obstacle recorded against the Action. |

### 8.1 Candidate Constitution wording for the Portfolio boundary

Offered as text for a future version of the Constitution, since this was ruled to belong
there rather than in a design document:

> **A constraint changes an Action, never a Decision.**
>
> A Decision states what an asset warrants. It is reached without knowledge of any
> portfolio, so the same asset carries the same Decision whatever holds it.
>
> An Action states what to do in a portfolio. It is reached from a Decision, that
> portfolio, and that portfolio's constraints.
>
> Where a constraint — cash, a position limit, a currency, a tax, a restriction — prevents
> the Action a Decision calls for, **the obstacle is recorded against the Action and the
> Decision is left as it stands.** A constraint that changed a Decision would make the
> same asset carry two different judgements about itself, and would hide a limitation of
> the account inside a statement about the world.

### 8.2 What this section does not do

- It does not freeze the Decision Layer, and it does not authorise any implementation.
- It does not reopen the four items; item 2 and the open half of item 3 are the work.
- It does not change the Observation Phase, the frozen Runtime, or the pause on paper
  trading.

---

End of Document
