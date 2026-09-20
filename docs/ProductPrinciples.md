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

**The first fifteen seconds decide whether the rest is read.** Opening the report
must answer one question immediately: **why is this stock worth attention today,
or why is it not?** Not what the data is — whether today matters.

Every optimisation from here on is judged first by what it does to those first
fifteen seconds. A change that improves paragraph nine and costs the opening is
a regression, however much better paragraph nine is.

**A report is a selection, not a transcript.** AIS analyses everything it watches.
A report is not the list of what it analysed: the two sets are different sizes on
purpose, and a report that grows whenever the watchlist grows has stopped choosing.
What a report leaves out is not dropped — it is named, counted, or kept in the
record the reader can open — so that a short report can never be mistaken for a
narrow one.

That is a different question from how a report is laid out. A report that answers
"what should I look at first" is a different document from one that answers "here
is everything I looked at", and producing the second and shortening its lines does
not produce the first.

**And the same thing is said once.** When several assets amount to the same
conclusion, the report states it once and names the assets it covers, rather than
repeating the sentence once per asset. Repetition is not emphasis: it spends the
width that could have carried what is different about each asset, and it teaches the
reader to skim exactly the lines that matter most. Where a conclusion is shared, what
remains worth stating per asset is what is *not* shared — where it stands, why it is
worth attention, what it has ahead — and that is what the report writes.

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

**Density is not the same as value.** A longer report is not a better one. The
rule for anything new is:

> Does this sentence help an investment decision?

If it does not, it does not go in the daily report — however true it is, and
however interesting it is to the person who built it. Facts that a reader can
look up elsewhere, or that do not change what they would do, are not the
report's business.

The corollary matters just as much: when something is added, something else
usually has to go. A report that grows every round until nobody finishes it has
stopped being a report, and the reader will go back to their own screen.

**Nothing is deleted; it moves.** Cutting a line from the daily report is not the
same as deciding the fact does not matter. A fact that is real and traceable goes
to the expanded report, which keeps everything the phone leaves out. AIS is
allowed to show a reader less; it is not allowed to know less, and it is never
allowed to quietly drop something it had already said.

**A budget that is not enforced is not a budget.** Limits on length, width and
what the first screen must contain are held by tests, not by good intentions and
not by the person adding the next feature. The report had already grown past a
width it claimed to respect, and nobody noticed until it was measured.

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

**Catalyst answers what could change the investment case, not when something
happens.** "Results in 43 days" is a fact about a calendar. What an investor
needs to know is which events could change how the asset is viewed, and why each
of them matters. A date on its own is a reminder; an event with a reason is
information.

For the same reason, how many events there are is not a signal. A busy calendar
is a busy calendar, and it is not a bigger opportunity than a quiet one with a
single important date in it.

**AIS is worth more than the facts it repeats.** Its value is not that it can
list a price to earnings ratio, which any screen can do. It is that it says what
the ratio means: whether the price already assumes the growth on offer, whether
profit is being collected in cash, whether the risk is in the price or in the
business.

So every category says what its evidence amounts to, and not only what the
evidence is. Repeating a measurement is the one thing a reader can already do for
themselves.

**An interpretation is not a forecast.** AIS says what the evidence supports and
stops there. It does not say what will happen, does not give a target, and does
not put a probability on anything. Every sentence can be traced back to the
measurements it was read from, so a reader who disagrees has something to
disagree with — which is not true of a prediction.

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

## 9. Three Questions That Must Not Be Mixed

AIS distinguishes between three things, and never lets one stand in for another:

**What we know.** The categories. Facts, measurements and readings, each tied to
the evidence it came from.

**What it means.** The opportunity judgement. Whether what is known adds up to
something worth acting on today.

**What we should do.** The recommendation. The action, stated plainly.

They are three different questions, and the answer to one is not the answer to
another. A fact is not a conclusion. A conclusion is not an instruction. An
instruction is not an explanation.

The reason this matters is that mixing them is invisible. A report that presents
an opinion in the shape of a fact, or an action in the shape of an argument,
reads as though it were more certain than it is — and the reader has no way to
tell which part was measured and which part was decided.

So each layer is allowed to say only what it can support, and each is allowed to
say that it does not know. When a lower layer is missing, the higher layer says
it could not be judged rather than quietly proceeding without it.

---

## 10. Market Explains the Environment

**Market is not the index.** Its question is not "how did the market do", it is:

> What does the current environment mean for **this** stock?

An index change is one input to that and never the answer. Every asset sits in an
environment of its own — a sector, a set of policies that bear on it, a style the
market is currently paying for, a level of appetite for risk, money moving in or
out of the things it competes with — and a report that says the same sentence
about a bank, a rocket company and a gold miner has said nothing about any of
them.

So Market draws on the macro backdrop, the industry, market style, risk appetite
and flows, and answers in the reader's language. It is the category that explains
**what the environment means**, which is a different job from reporting what the
environment is.

**Market explains impact; Catalyst lists what is coming.** These are two
questions and they must not be merged:

| | Question | Tense |
| --- | --- | --- |
| **Catalyst** | What could change the investment case, and when? | What is coming. |
| **Market** | What does the environment mean for this stock? | What is true now, and what just happened. |

An event that has already happened and moved the environment is Market's
business: explaining its effect belongs there and nowhere else. A future event on
the calendar is Catalyst's business. Neither may do the other's job, and in
particular:

- Catalyst does not explain what the environment means — it does not have the
  industry, style or flow evidence that would take.
- Market does not list what is coming — a second calendar inside the report
  would be a second answer to a question that already has one.
- **No third section is created for this.** A separate "market brief" next to
  Market would split one question across two places, and the reader would have to
  join them up.

**Market's evidence is shared; its judgement never is.** How the futures are trading,
how turbulent the market is and what money costs are the same facts for every asset in
a market, so they are retrieved once and read by every asset in the pass rather than
fetched again for each. What is not shared is the sentence: a fact about the market
has no meaning until an asset is named beside it, and the meaning is the pair.

That is why a sentence about the environment names both halves — the condition and the
exposure. "Growth is under pressure" is a market recap; "growth is under pressure and
this is a growth company" is a judgement about something the reader owns. A clause
that cannot name both halves does not belong in the category.

**And a mechanism whose evidence is missing is named, not guessed.** A rate move
reaches a bank's margin through the shape of the curve, not through one yield; where
AIS has one yield and not the curve, it says the exposure exists and that the
direction is not judged. Naming an exposure and admitting the direction is unknown is
worth more than a confident sentence built on half the mechanism, and the reader can
act on the difference. An exposure that cannot be stated at all — what a currency is
doing to a company that does not publish where it earns — is listed as a gap rather
than described as though it were not one.

---

## 11. Reading Before Building

AIS reads its own numbers with conventions: a price to earnings ratio of twelve
reads cheap, a volatility of forty five per cent reads high. Those conventions
are provisional, and they are the one thing every part of the product leans on —
the grade, the sentences, and the opportunity judgement all measure against them.

**They are one layer, and they are replaced as one.** When the AIS Standard Score
finally defines what a reading means, it replaces a single place, not three that
have to be reconciled with each other first.

Until then they are provisional together, and they may not be adjusted one at a
time. A number changed in one place and not the others is how a report starts
contradicting itself — and a report that disagrees with itself is worse than one
that is merely wrong, because the reader cannot tell which half to believe.

**A reading is decided once, and everything that uses it reads the same decision.**
The grade, the sentence and the opportunity judgement are three views of one
reading. Where each of them decided privately what a number meant, AIS said an
asset had a near term catalyst in one line and no clear catalyst in the near term
forty lines below it — about the same calendar, from the same run.

**A sentence may not deny the verdict beside it.** If AIS says a category reads
well, nothing it writes from the same readings may say that it does not. Where a
threshold would let both appear, the threshold is wrong, not the reader's patience.

**And "reads well" means nothing in it disqualifies it.** A category that reads well
on average while holding a measurement at the bottom of its scale has not been read
well; it has been averaged. Cheap multiples beside a negative cash flow are not an
attractive valuation, and a report that says they are has used a number to avoid a
judgement.

---

## 12. When AIS Thinks and When It Speaks

Working out what AIS thinks and telling the reader are two different moments,
chosen for two different reasons, and neither may be assumed from the other.

**When AIS thinks is decided by the data.** An analysis is worth computing once
the information behind it is complete — after a session has closed, after a
release has landed. That moment belongs to the market and to the calendar, and it
has nothing to do with whether anybody is awake.

**When AIS speaks is decided by the reader.** A report is worth sending when
somebody can read it. A conclusion delivered at four in the morning reaches a
phone, not a person.

So a report has two times. One anchored to the close is not therefore sent at the
close, and one sent in the morning is not therefore computed in the morning.

**And a report the reader is expecting is owed; an interruption has to earn it.**
These are different in kind and must not be run by one rule. A message that arrives
because something changed earns its place by carrying news — and if there is no
news, it does not arrive. A report that arrives at an hour the reader chose is owed
whether or not it has news, because the reader opened that slot for it and "nothing
has changed" is an answer to the question they asked.

Applying the change rule to an expected report turns it into an unpredictable one:
it arrives on the days something happened and silently does not on the days nothing
did, and its absence stops meaning anything. **A report that describes the present
is not a repetition of one that described yesterday**, even when it reaches the same
conclusion — the change rule governs interruptions, not repetition.

**And an expected report arrives as one thing.** A reader who opens a slot in the
morning has agreed to read a brief, not to receive a stream. Several messages
arriving together are a feed, and a conclusion spread across them has to be
reassembled before it can be used. One asset changing is worth a message of its own,
because that message is news; a whole universe being looked at is worth one message,
because the reader asked one question.

**And a report is computed when it is sent.** It describes the world as it is at
the moment the reader receives it, not as it was at the moment AIS last looked. A
report built at four and delivered at nine is five hours out of date, and it is the
worst kind of out of date, because nothing about it looks wrong.

This is the part that keeps a scheduled report from becoming a recital. A report
that only restates an earlier conclusion in different words has taken the reader's
attention and given them nothing they did not already have.

**And a report has to earn its place in the reader's day.** Arriving at a
convenient hour is not a reason to exist. If what a report says is already
contained in another one the reader gets, then sending it is asking for attention
without giving anything back — and a reader who is asked for attention twice for
the same thing starts ignoring both.

---

## 13. Configuration Says What to Do, Never What Is True

A setting tells AIS how to behave. It does not tell AIS what the world is like.

The line matters because a file that states a fact will eventually state a wrong
one, and nothing will correct it. Whether a position is held is decided by a broker;
whether an event is near is decided by a calendar. Written into a settings file,
those become a second copy of the truth that nobody updates — and by the time the
two disagree, the copy is the one the system has been reading.

So configuration holds **choices**: which assets to watch, how often to look, where
to send the result. Everything else comes from the component that owns it, and a
component that cannot supply it says so rather than having it filled in from a file.

The same reasoning applies inside a file. When the same membership can be written
two ways — a mapping and a list of its values — it will not stay equal, so it is
written one way and the other is derived.

**And a label that decides what AIS can say must be stated, never guessed.** What
kind of thing an asset is decides which questions apply to it: an exchange-traded
fund has no earnings, a bank has no current ratio, and a report that treats those
absences as zeros has said something false about the asset. So the kind is stated
where a person can state it, and left unknown where nobody has — because guessing it
would quietly change what AIS is able to say, and a changed ability to speak is
never visible in the output.

---

End of Document
