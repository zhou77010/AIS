# AIS Portfolio Methodology

Status: **Draft v1, accepted in principle.** Chapters 1 to 7 have been reviewed. This
document is methodology, not Policy and not authority: where it disagrees with the
Constitution, the Constitution wins, and nothing here authorises an implementation on its
own.

**What this document is.** The method of one layer: the Portfolio Layer. It defines the
single question that layer is allowed to answer, the principles that constrain it, what it
may read, how it maps what it reads into a target, what it produces and what it may never
do.

**Why it is not shaped like the Decision Methodology.** The Decision Layer forms a
judgement, so its method needed a chapter on the conditions that must exist before its
question can be answered. The Portfolio Layer forms no judgement: it **maps judgements
that already exist** into an account state. There is therefore no Required Conditions
chapter here, and Chapter 4 (Solve) takes its place as the centre of the document.

**What this document is not.** It contains no threshold, no weight, no priority and no
state vocabulary. Those belong to Policy. The document is written so that changing a
number or a name never means editing the methodology.

---

## 1. Question

> **把所有已经做出的判断放到一起，这个账户整体应该是什么样子。**

Three limits are built into that sentence:

- it concerns **the account as a whole**, not a single asset;
- it is given **all the judgements**, not one;
- it produces a **state**, not a change.

It does not answer: whether an asset is worth holding, what change should happen, or
whether anything has happened.

**Against its neighbours.** The Decision Layer judges one asset. This layer judges the
account. Action answers the difference between the present and the target. Execution
answers what reality did.

---

## 2. Principles

| # | Principle |
| --- | --- |
| **P1** | This layer is allowed to answer the question in Chapter 1, about the account as a whole, and nothing else. |
| **P2** | It owns **no Evidence**: it reads no market data, no financial data, produces no new Reading and no new fact. |
| **P3** | It **never modifies a Decision**. A constraint changes an Action, never a Decision. |
| **P4** | It forms no new investment judgement: everything it produces traces to **judgements + the account as it stands + the holder's rules and preferences**. |
| **P5** | Given complete Policy, its result is **deterministic**. Where it is not determined, the gap belongs to the **rules**, not to a view held by this layer. |
| **P6** | It may never present a rule as a fact about the world; rules and preferences are the holder's **choices** (configuration, §13 of the product principles). |
| **P7** | It never states what an asset is worth, and it never reads HPO. |
| **P8** | Its explainability comes from **constraints** (§3.17: the reason a position is the size it is is the constraint that bound it), never from evidence. |
| **P9** | It answers what the account should be, never what was done — describing reality would be the Execution Layer. |
| **P10** | Same rule as the Decision Layer: **thresholds, weights and priorities do not belong here**. They are Policy, and no number appears in this document. |

---

## 3. Inputs

Three, with fixed roles, and no more than three:

| Input | What it provides | What it does not provide |
| --- | --- | --- |
| **Decisions** | For each asset, whether it is worth becoming a standard position, and the grounds for that — **a warrant only, never a quantity** | No number, no ordering, no account information |
| **Current Portfolio State** | What this account currently is; Policy may be expressed relative to it | It does not decide the target, and it changes no Decision |
| **Portfolio Policy** | Constraints (bounds) and preferences (choices) — **every number and every trade-off lives here** | It is not a fact about the world; it is the holder's choice |

**Rule:** nothing else is read. Facts, evidence, market data and HPO do not enter.

---

## 4. Solve

**The layer has one job: map Decisions into a Target Portfolio.** The process is defined
below. It contains no algorithm, no number and no ranking method.

**S1 — Eligibility.** An asset is eligible if and only if the result of its Decision is
the favourable one. **This layer does not re-derive that result and evaluates nothing
about the asset.**

**S2 — Realisation.** Every eligible asset is placed at Policy's standard unit. Policy's
bounds and preferences are applied **to the account as a whole, once** — so that the result
is one coherent state rather than something accumulated asset by asset.

**S3 — Resolution.** Where Policy's rules conflict, Policy's stated resolution is used.
Where Policy states none, the case is **recorded as unresolved rather than decided here**.
This layer does not search for a compromise and does not pick the best of the options.

**S4 — Carry and complete.** Assets with no favourable result, or with no Decision at all
today, are placed according to **Policy's stated behaviour** — so that the result describes
the **whole** account rather than a difference.

**S5 — Name the binding constraint.** The result records **which constraint limited it**
(§3.17).

**What Solve must not do** — these are boundaries, not style:

- it does not reinterpret the content of any judgement: it only **applies** Policy;
- it **never ranks assets by merit**: Policy may express a preference, but this layer does
  not weigh merit itself (that would be a judgement);
- it does not use the account's present state to alter any Decision;
- it does not invent a bound, a weight or an objective of its own;
- it does not lower the target because reaching it looks hard — **reachability is not this
  layer's question** (it is Action's).

**Property:** with complete Policy the result is determined — the same inputs produce the
same Target Portfolio.

---

## 5. Outputs

The output is a **Target Portfolio**:

1. **a complete account state** — the same kind of thing as the input's account state, in
   another tense; so the next layer can obtain the difference by subtraction, without
   re-judging anything;
2. measured in a base currency;
3. carrying **the constraint that limited it** (S5);
4. carrying a record of any conflict Policy did not cover, as unresolved.

**Absent from the output:** actions, execution method, timing, and any new statement about
what a single asset is worth.

**It is not an Action.** It states what the account should be, not what should change —
the difference is the next layer's to compute.

---

## 6. Constraints

This layer must never:

- modify any Decision (a constraint changes an Action, not a Decision);
- read facts, evidence, market data or HPO;
- form a new investment judgement, or rank assets by merit;
- invent a bound, a weight, a priority or an objective;
- use the account's present state to change a judgement;
- adjust the target because it is hard to reach (reachability belongs to the Action layer);
- emit anything a lower layer must reinterpret;
- place a number in this document — thresholds and weights are Policy.

---

## 7. Deferred

Only items that would block this layer are kept. None of the following blocks it, because
each belongs to Policy's content rather than to this layer's method:

| # | Open item | Belongs to |
| --- | --- | --- |
| **P-D1** | The form of Policy's conflict-resolution rule (S3 depends on it existing, not on its content) | Policy |
| **P-D2** | Policy's default behaviour for holdings with no favourable result, or with no Decision today (S4 requires that such behaviour exists, and does not say what it is) | Policy |
| **P-D3** | The scope of the account, and its base currency | Policy |
| **P-D4** | The magnitude of the standard unit | Paused (Standard Position) |
| **P-D5** | Documentation alignment: the wording that calls a portfolio "state", the purpose wording, and the three-questions wording | Documents |

---

End of Document
