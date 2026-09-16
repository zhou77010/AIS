# AIS Product Principles

What kind of product AIS is.

This document answers that question and no other. It is not about how AIS is
built, and it contains no code, no structure, no method and no numbers. Those
belong elsewhere:

| Question | Document |
| --- | --- |
| What should AIS be? | this document |
| Why did AIS become what it is? | `docs/DevelopmentJournal.md` |
| How is AIS organised? | `docs/Architecture.md` |
| How does AIS think? | `docs/Constitution.md` |

These principles are long-lived. They are maintained for the life of the
project, not for a sprint, and a change to one is a product decision rather than
an implementation detail.

---

## 1. Purpose

AIS helps an investor answer questions about an asset they are considering
holding.

The questions are ordinary ones. Is this worth owning? What is it worth paying?
What could go wrong? What has already changed? What do I still not know?

AIS does not answer a different question instead. It does not forecast prices,
it does not produce signals to trade on, and it does not tell anyone what to do
with their money. It assembles what is known about an asset, says plainly what
it concludes, and shows its working.

The value is in being able to disagree with it. A conclusion an investor cannot
trace back to its evidence cannot be argued with, and a conclusion that cannot
be argued with is not worth having.

---

## 2. Report Philosophy

The daily report says **what has changed**, not what the numbers are today.

**AIS emphasises change over static state.** Investment decisions are driven by
what is changing, not only by what currently exists.

An investor who holds a position already knows roughly where it stands. What
they do not know is what moved since they last looked, and whether it matters.
A report that lists today's figures makes them work that out themselves, every
day, from the same figures they saw yesterday.

So the report leads with change: a grade moving, a measurement turning, an
assumption starting to fail. Standing facts are the support for that, not the
message.

---

## 3. Decision Philosophy

**Evidence comes before opinion.** Nothing is concluded that the evidence does
not carry.

**What is not known is said plainly.** A dimension that was not examined is
reported as not examined. A measurement that could not be obtained is reported
as missing, with the reason. Being incomplete is acceptable; appearing complete
is not.

**Nothing is invented to fill a gap.** A number that looks plausible and is not
real is worse than an admitted hole, because a hole can be seen.

---

## 4. Progressive Completeness

Anything AIS can already tell an investor goes into the report immediately. It
does not wait for the final methodology, the final scale or the final score.

The product grows by adding something genuinely useful at every step, not by
delaying everything until the whole system is finished. A category that is
partly assessed today is worth more than a category that will be fully assessed
at some unspecified point later.

This is also why the product tolerates its own rough edges in public. A grade
that is provisional, in a report that says so, is honest. Waiting for a perfect
grade before showing any is not.

---

## 5. Mobile First

The report is written for a phone before anywhere else.

An investor reads it in the time they have — on a train, between meetings, first
thing in the morning. The whole report should be readable in about thirty
seconds, and the conclusion should be readable in the first few lines.

Anything that only works on a large screen, or that needs the reader to scroll
back and forth, has been designed for the wrong reader.

---

## 6. Natural Language

The report is written in the reader's language, not the system's.

Prose carries the meaning. Numbers live in the evidence, where they support a
conclusion rather than being the thing the reader is asked to interpret. Where a
measurement reads better as a sentence, the report writes the sentence.

This does not mean rounding the truth off. It means saying "the trend has turned
up" instead of handing over two figures and leaving the reader to work out
whether that is what they mean.

---

## 7. Honesty

Where AIS does not know something, it says so. It prefers "not yet assessed" to
a number it cannot stand behind.

The hardest cases are the ones where saying nothing looks like saying something.
A dimension never examined is not a dimension found to be safe. A measurement
that is absent is not a measurement of zero. Both must look absent, and must
never look like a result.

Every part of the product is held to this, including the parts that are
unfinished. A visible gap is a promise; an invisible one is a lie.

---

## 8. Evolution

AIS is expected to grow, and it is expected to grow in steps.

A backlog is part of the design. It records what has been thought about and
deliberately deferred, together with the reason, so that a later reader can tell
the difference between a decision and an oversight. Deferred work is not a
defect, and an incomplete product described honestly is not a failure.

The product is allowed to be better next month than it is today. It is not
allowed to pretend it is better today than it is.

---

End of Document
