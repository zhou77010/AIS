# AIS Development Journal

Why AIS became what it is.

This document records decisions and the reasons behind them. It is not a
changelog: what changed is in the commit history, and how the system is
organised is in `docs/Architecture.md`. What is here is the reasoning, so that
anyone arriving later can tell a deliberate choice from an accident.

Entries are appended. An entry is never rewritten to match a later decision —
if a decision is reversed, a new entry says so and says why.

## Format

```
Date

Context     what was in front of us
Decision    what was chosen
Reason      why that choice and not another
Impact      what it changed
Revisit     whether and when to look at it again
```

---

## 2026-09-16

### Bark became the notification channel

**Context.** WeChat and the WeCom app both rejected every message: the source IP
was not whitelisted, and whitelisting required a verified domain or a message
receiver endpoint we did not have. The two channels were unusable without work
that had nothing to do with AIS.

**Decision.** Deliver to the phone through Bark, and keep the other channels
implemented and configurable.

**Reason.** The point of v1 was to reach the investor, not to reach them through
one particular application. Bark needed no domain, no whitelist and no
real-name verification, so it removed the blocker entirely.

**Impact.** Channels are additive rather than alternative. Configuring another
one never replaces Bark, so the failed WeChat path can be finished later without
taking the working path away.

**Revisit.** When a second channel is genuinely needed.

---

### A measurement that cannot be obtained is recorded as absent

**Context.** A discounted cash flow fair value was one of the inputs the
valuation rules expected. No market data source publishes one, because it is the
output of a model rather than a reported fact.

**Decision.** Report it as unavailable, permanently, with the reason. Do not
substitute a placeholder, and do not change the architecture to make the gap
disappear.

**Reason.** Any value would have to come from assumptions nobody has approved,
which would make it an invented number wearing the name of a measurement. The
product's value rests on its numbers being real.

**Impact.** Roughly one measurement in five is permanently missing from that
category, and the report says which. This became the pattern for every later
gap.

**Revisit.** Only if a defined valuation method is approved.

---

### The report model became authoritative and renderers became projections

**Context.** Each notification channel was beginning to build its own message.
The same recommendation would have been worded differently on the phone than in
the log.

**Decision.** There is one report model. Every channel, format and surface is a
projection of it. No channel may hold a report structure of its own.

**Reason.** Two renderings of one decision that disagree are worse than one
rendering, because a reader cannot tell which to trust. Keeping the content in
one place also means a channel is only ever a transport.

**Impact.** Every notifier receives text that has already been written. Adding a
channel cannot change what the report says.

**Revisit.** No.

---

### The architecture was frozen and framework work stopped

**Context.** Three phases of architecture review concluded that the structure
was sound, while every capability the product needed was still missing.

**Decision.** Freeze the architecture. No subsystem is to be rewritten and no
framework expansion is to be done unless a genuine defect is found.

**Reason.** Structure was no longer what stood between AIS and a useful report.
Continuing to improve it would have produced a better-organised system that
still told an investor nothing.

**Impact.** Component boundaries were written down and are enforced by tests. A
refactor that had been started to introduce an analysis pipeline was withdrawn
and the working tree reverted, because it was framework work at a moment when
framework work had been closed.

**Revisit.** Only on a real defect.

---

### The Constitution defines language only

**Context.** Almost every field in the report depended on meanings nobody had
written down: what confidence means, what coverage means, what a grade means.
The document that was supposed to own them did not exist.

**Decision.** Write it, but only for vocabulary and semantics. No method, no
scale, no thresholds. Deferred methodology is listed as deferred rather than
left unsaid.

**Reason.** Meanings settle slowly and must not be invented by an implementation,
while methods can be added incrementally once the words are fixed. Writing the
whole thing at once would have delayed every capability behind it.

**Impact.** Every later category could be built without waiting, because it was
clear which questions were answered and which were not.

**Revisit.** Continuously, by appending new vocabulary.

---

### HPO is intentionally left undefined

**Context.** One of the nine categories is an acronym with no explanation
anywhere in the repository or the source material.

**Decision.** Keep it undefined, and make the Constitution say so explicitly. AIS
never invents a meaning for it.

**Reason.** A guessed meaning would propagate into a definition, a rule and a
score, and would then be indistinguishable from a real one. Nothing may be
assumed about a category whose question is unknown.

**Impact.** The category is carried verbatim and never assessed. This became a
general principle: a name carries only the meaning the Constitution gave it.

**Revisit.** When someone defines it.

---

### One measurement may support two categories

**Context.** Financial health and financial risk both read the same figures. The
first implementation treated this as double counting and refused to let a
measurement serve two categories.

**Decision.** The rule is that one fact must not answer the same question twice
under two names. One fact read by two categories is allowed, when the questions
differ.

**Reason.** A balance sheet is one state; asking what it is and asking how
exposed a thesis is to it are different questions. Forbidding the second reading
would have hidden real risk to avoid a duplication that was not there.

**Impact.** Measurements are stored once as evidence and read by as many
categories as need them.

**Revisit.** No.

---

### The coverage fraction was removed from the report

**Context.** The report showed how much of each category had been examined, as a
fraction such as three of eight.

**Decision.** Stop showing it. The model keeps it; the report names what was not
examined instead.

**Reason.** An investor cannot act on a proportion. It is bookkeeping about the
model, and it made the reader do the work of turning a fraction into a fact.
Naming the things that were not looked at is a fact they can use.

**Impact.** Coverage remains in the model and is displayed as a list of names
under "not yet assessed".

**Revisit.** No.

---

### A provisional grade replaced the raw scores

**Context.** Category scores were means of measurements on different scales, and
they were displayed as numbers. An investor was being invited to compare figures
that could not be compared.

**Decision.** Show a grade out of five, derived from each measurement's
conventional reading rather than from the category score. Leave the score itself
raw and labelled as undefined.

**Reason.** The grade is presentation, and it makes the report readable today
without pretending the scoring problem is solved. Deriving it from the
measurements rather than the score avoided giving the meaningless average any
authority.

**Impact.** The grade is provisional and says so, and it is to be replaced once
the standard score exists. The score underneath was not touched.

**Revisit.** When the standard score is defined.

---

### The report is written in the reader's language

**Context.** The report was in English and used the system's own vocabulary:
decision states as enum values, categories by their internal names, coverage as
a ratio.

**Decision.** Write it for an investor, in Chinese, with technical terms kept
where they are the conventional name.

**Reason.** The reader is an investor, not a developer. A report they have to
translate before they can use it is not serving them, however accurate it is.

**Impact.** Category names, decision states and measurements are translated once
and shared by every renderer.

**Revisit.** No.

---

## 2026-09-17

### Trend is written as a sentence

**Context.** The trend section showed two figures: where the price sat in its
range, and how far it had moved over a year. A reader had to decide for
themselves what those two meant together.

**Decision.** Write the trend as a sentence. Keep the figures in the evidence.

**Reason.** Saying "the trend has turned up" is what the reader wanted. Handing
over two numbers and leaving the interpretation to them is not analysis, it is a
data feed.

**Impact.** Established the pattern of narrative in the body and numbers in the
evidence, which the rest of the report now follows.

**Revisit.** Redesigned once technical indicators were connected, which happened
the same day.

---

### Category structure is decided per category

**Context.** Risk has dimensions fixed by the Constitution. Market had one
measurement, and reporting it as complete would have claimed the whole
environment had been examined.

**Decision.** Choose the unit of each category's coverage separately: dimensions
for risk, aspects for market and trend, parts for earnings, measurements for
valuation and fundamental. Do not fix a pattern.

**Reason.** A single pattern would have been either wrong for risk, whose
dimensions are defined, or dishonest for market, which would have claimed
completeness it did not have.

**Impact.** Four categories now use four different units. This is recorded as
needing one review rather than being treated as settled.

**Revisit.** Yes, in the report product review after all nine categories exist.

---

### Price history and indicators replaced the two-figure trend

**Context.** Trend leaned on a 52-week range position and a 52-week change.
Those two figures were the whole of it, and neither said anything about how the
price had been behaving.

**Decision.** Retrieve daily price history and compute the conventional
indicators from it. Build the trend and part of the risk reading from those.

**Reason.** A trend measured from two endpoints cannot see the path between
them, and "how it got here" is the question. Volume and momentum were available
and were being ignored.

**Impact.** Trend now reads moving averages, momentum and volume. Risk gained
volatility and drawdown, and its grade fell, because the price's actual
behaviour was finally visible.

**Revisit.** No.

---

### Rating momentum is carried in the model

**Context.** A grade says where a category stands but not whether it is moving.
A category can improve for weeks without crossing into the next grade, and the
report showed nothing in that time.

**Decision.** Carry the movement inside a grade as model data, accumulated from
the point the grade was last set, and reset when the grade changes.

**Reason.** The movement is the interesting part and it is lost the moment it is
recomputed on each render. Remembering where a grade was set is the only way to
measure how far the category has travelled since.

**Impact.** The report can show a category improving before its grade moves. The
memory is per process, so a restart begins again rather than inventing a
baseline.

**Revisit.** No.

---

### The event alert was deferred to the runtime stage

**Context.** Three notification behaviours were agreed: a daily report, a weekly
report, and an alert when something material changes.

**Decision.** Build none of them yet. Finish the categories first, then build
the runtime as one piece.

**Reason.** An alert that fires on a material change needs a definition of
material, and every threshold in AIS is still deferred. Building it now would
mean inventing the number it depends on, or rebuilding it later.

**Impact.** Recorded in the backlog with the reason, so that the deferral is a
decision rather than an omission.

**Revisit.** After the report itself is settled.

---

End of Document
