# AIS Decision Methodology

Status: **Draft v1, accepted in principle.** Amendments from the review of 2026-09-23 are
applied. This document is methodology, not Policy and not authority: where it disagrees
with the Constitution, the Constitution wins, and nothing here authorises an
implementation on its own.

**What this document is.** The method of one layer: the Decision Layer. It defines the
single question that layer is allowed to answer, the principles that constrain it, the
conditions that must exist before its question can be answered at all, what it may read,
what it does, what it produces, and what it may never do.

**What this document is not.** It contains no threshold, no weight, no priority and no
state vocabulary. Those belong to Policy, and they are deliberately absent here so that
changing a number or a word never means editing the methodology.

---

## 1. Question

> **今天，这个资产是否值得成为一个标准仓位。**

Three limits are built into that sentence:

- it concerns **one asset**, not an account;
- it is **anchored to now**, not a timeless rating of the company;
- it asks about the **warrant to hold** — the target — and never about the path: not how
  much, not how, not how many times, not how long.

It does not answer: quantity, method, timing, or anything about an account.

The definition of the unit the sentence refers to (标准仓位) is deferred and is not
required for this chapter: the question names a unit, and defining that unit's magnitude
is Policy's work.

---

## 2. Principles

| # | Principle |
| --- | --- |
| **P1** | The Decision Layer is allowed to answer the question in Chapter 1 and nothing else. |
| **P2** | Its inputs are **already-formed judgements**. It never reads a fact, a measurement or a piece of evidence, and it never re-interprets anything below it. |
| **P3** | **Every semantic interpretation happens exactly once.** A meaning has one owner; the Decision Layer owns none of the meanings it consumes. |
| **P4** | The layer neither performs a **second synthesis** of the categories (that would be a second Assessment) nor applies a **boolean filter** to another layer's conclusion. It **generates** the warrant; it does not re-judge, and it does not re-filter. |
| **P5** | It **never reads an account** — holdings, cash, execution — and no account constraint may ever modify a Decision. |
| **P6** | Its answer changes **only when the facts behind the judgements change**. Price moving is not, by itself, a reason for the answer to change. |
| **P7** | **Risk is expressed dimension by dimension** and is never aggregated. Risk does not decide size. |
| **P8** | HPO is never an input (§4.1). Today Priority is an ordering of attention, not a judgement. |
| **P9** | Evidence that has not been promoted to graded may not influence a Decision: the Evidence Maturity Rule may not be bypassed by a layer that reads judgements. |
| **P10** | A Required Condition states **only what must exist**. It never states whether the answer is favourable, never contains a threshold, and never contains a veto. |

---

## 3. Required Conditions

A Required Condition is admitted when it satisfies all of the following, and is rejected
otherwise:

1. it is **semantically derivable from the question** — and the derivation names which
   part of the question would fail without it;
2. **deleting it makes the question unanswerable** — not "less reliable", but unanswerable;
3. it **does not overlap** another condition;
4. it **does not cross a layer boundary**.

**Necessity is judged on the set, not one condition at a time.** Where two conditions
cover each other, deleting either one still leaves the question answerable, so a pairwise
deletion test would remove both — while their combination was what answered the question.

### 3.1 The Necessary Set

| # | Condition | Which part of the question requires it |
| --- | --- | --- |
| **C1** | **A judgement exists about what is given and what is received.** | "值得" — the whole content of worth is the legitimacy of an exchange |
| **C2** | **A judgement exists about how it could go wrong, dimension by dimension.** | the other half of "值得": a worth that cannot say what would make it fail is an unfinished judgement (§2.3) |
| **C3** | **Those judgements belong to the moment of this judgement.** | "今天" — answering today's question with last week's judgements answers a different question |

### 3.2 Rejected candidates

Recorded with the rule that rejected each, so that they are not re-proposed.

| Candidate | Rejected by | Why |
| --- | --- | --- |
| Whether the business is excellent (company quality) | rule 2 | The counterexamples settle it: a mediocre company at a very low price can still be worth a standard position. Quality is not necessary. |
| Liquidity / whether it can be traded | rule 3 | Overlaps C2: §5.2 already defines "cannot be entered on the terms the thesis assumes" as a risk dimension. It enters as C2's content, not as a condition. |
| Whether now is a good moment | rule 4 | No layer owns a timing judgement, and it conflicts with P6. `今天` produces C3, not timing. |
| Anything about the account (cash, limits, concentration) | rule 4 | Crosses the Portfolio boundary. |
| An overall view, a composite, or an opportunity grade | rules 1 and 4 | A synthesis is not derivable from the question, and HPO may not be an input (§4.1). |
| Whether the evidence is sufficient (a coverage or confidence threshold) | P10 | "How much is enough" is a threshold, therefore Policy. Those attributes exist and are carried (Chapter 4); as a condition they would become a number. |

**The Necessary Set never produces the answer by itself.** It states what must already
exist before the question can be answered at all.

---

## 4. Inputs

The input is **the set of judgements that satisfies the three conditions** — never facts,
never an overall score.

| Condition | Input | Note |
| --- | --- | --- |
| C1 | The judgement about what is paid and what is received, including its forward half | Taken from whichever judgement flow carries it |
| C2 | The risk judgements, dimension by dimension | Liquidity is one of those dimensions; it is not a separate input |
| C3 | The moment each of the above judgements belongs to | An attribute of the judgement, not a new judgement |

Every input arrives carrying **its evidence references, its coverage and its confidence**.
Those are attributes and are carried through; their thresholds are Policy.

**What does not enter:**

- facts, measurements and evidence;
- HPO (§4.1);
- the account's state;
- evidence that has not been promoted to graded.

**Assessment is not an input.** Ruled: the Decision Layer does not read the Assessment.
It is a synthesis of judgements that are already inputs, so reading both it and its parts
would count the same judgement twice (§2.10). The Assessment remains a **display object
for the Report**, not an input to a Decision.

**Two judgement flows exist today** (Measurement → Reading, and Evidence → Evaluators).
The Decision Layer is not restricted to one of them, but it may not read across a layer
boundary to shorten the path.

---

## 5. Process

1. **Evaluate each Required Condition using the applicable Policy.** The methodology
   requires that each condition is evaluated; *how* it is evaluated — the bar, the
   threshold, the rule — belongs to Policy and is not owned here. This layer applies what
   Policy provides and records what came out.
2. **Combine the outcomes into the Decision Result** (Chapter 6). No weighting, no
   ranking, no merging of judgements, no re-scoring of anything. Where a condition is not
   satisfied, the result **names which one**; where a condition could not be evaluated,
   the result says so and names the gap (§3.18: that is an outcome, not a failure).
3. **Produce nothing else.** The single product is the warrant, its grounds and its gaps.
   No new meaning is created: no category is re-questioned, no quality is re-estimated, no
   judgement is modified.

**Why this is not a boolean filter.** A filter re-screens a conclusion somebody else
reached. Here the conjunction is over **this layer's own required conditions**, and the
answer is generated rather than screened.

---

## 6. Outputs

The output is a **Decision Result**, containing:

1. **the result itself** (whose vocabulary is deliberately deferred — Chapter 8);
2. **the grounds**: the outcome of each Required Condition, naming any that is not
   satisfied and any that could not be evaluated;
3. **the judgements it rests on, with their evidence references**, so that the conclusion
   can be traced without the layer holding a private copy of anything;
4. **the attributes it was given**: coverage and confidence, carried through without a
   threshold being applied.

**Absent from the output:** quantity, method, timing, account information, any word that
names an action.

**Outward form.** The Decision is expressed to consumers as the same semantic object under
its consumer-facing name. That expression adds no field, no rule and no lifecycle: if it
ever contained anything the Decision does not contain, it would be a second Decision Layer.

---

## 7. Constraints

The Decision Layer must never:

- read a fact, a measurement, or evidence;
- re-synthesise the categories, or re-screen another layer's conclusion;
- read an account, a holding, cash, or an execution;
- decide a quantity, a method or a moment;
- aggregate risk, or invent a threshold of its own;
- change because price moved, without the underlying judgements changing;
- admit evidence that has not been promoted to graded;
- emit anything that a consumer must reinterpret: what it produces is applied, not
  re-judged.

---

## 8. Deferred Items

Items that are open but **do not block this chapter**. From here on, a new item may enter
this list only if it blocks the chapter being written; everything else is recorded where it
arose and settled when it is needed.

| # | Open item | Belongs to |
| --- | --- | --- |
| **D1** | How far "today" reaches — this morning, the last hour, the latest session. If it needs a boundary, the boundary is a threshold and moves to Policy, leaving C3 as a statement of existence. | Policy |
| **D2** | Who owns the bar each condition is evaluated against — and the rule that this layer may not invent one. | Policy / ownership |
| **D3** | Whether an `unknown` risk dimension satisfies C2, and how "could not be evaluated" is kept distinct from "not satisfied". Waits on observation data. | Ruling, pending data |
| **D5** | The vocabulary of the Decision Result. | Naming, last |
| **D6** | The definition of the unit the question refers to (标准仓位), and its magnitude. | Paused |
| **D7** | Risk's blocking rules (Policy), and whether risk may ever produce a reduction (Exit Methodology). | Policy / Exit |
| **D8** | The thresholds for coverage and confidence — their existence is already handled in Chapter 4. | Policy |
| **D9** | Documentation alignment: the three places that say a Recommendation says what to do; the chain's node naming; the three-questions wording; the statement that AIS does not tell anyone what to do with their money; Today Priority reading HPO. | Documents |
| **D10** | Completeness of the Necessary Set: when Policy meets a case it cannot express, a condition is missing. | With Policy |

*(D4 — whether the Assessment could be an input — was ruled and is recorded in Chapter 4.)*

---

End of Document
