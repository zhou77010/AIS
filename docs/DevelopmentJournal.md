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

### A movement carries a length and a reason

**Context.** The report showed a grade and an arrow. A bare "▲5%" does not tell
an investor whether the category moved in a day or in a month, or what moved,
and both of those decide whether the change means anything.

**Decision.** Every movement is written as three things together: how much, how
long, and why. The length comes from when the movement began, tracked with the
standing. The reason comes from the measurement that moved most over the same
stretch.

**Reason.** A number without a span is unreadable ("up 5% since when?"), and a
span without a reason is unactionable ("improving, but because of what?"). Both
had to be answered from recorded evidence rather than inferred by the renderer,
or the report would be inventing the explanation it presents as fact.

**Impact.** `RatingTracker` now records when a run of movement began and what
every measurement read at that moment, so attribution is a comparison of two
real readings rather than a summary of one. A run that only starts moving keeps
the length of the whole standing; only a genuine turn starts a new one.

**Revisit.** The attribution is by size, because how much each measurement
contributes to a judgement is still undefined. When the AIS Standard Score
defines that, attribution should follow it.

---

### AIS emphasises change over static state

**Context.** The report can now show movement, and the question arose of how
much of the report should be given to where things stand.

**Decision.** Investment decisions are driven by what is changing, not only by
what currently exists. The report leads with change; standing facts support it.

**Reason.** An investor already knows roughly where their position stands. What
they cannot see is what moved since they last looked and whether it matters.
Listing today's figures makes them redo the same work every day from the same
numbers.

**Impact.** Recorded as a product principle in `docs/ProductPrinciples.md`, so
later report work is measured against it rather than against taste.

**Revisit.** No.

---

### The last two factual categories were built, and HPO was defined

**Context.** Six of the nine categories were evaluated. Catalyst and Positioning
had no evaluator, and HPO was deliberately undefined: the Constitution forbade
any behaviour that would presuppose a meaning for it.

**Decision.** Build Catalyst and Positioning as vertical slices over evidence a
source can actually supply, and define HPO explicitly as an opportunity
judgement built from the categories the other two completed.

**Reason.** Both categories answer questions a source can partly answer:
Catalyst gets the dates on the calendar, Positioning gets who is on the register
and how crowded the short side is. The parts no source can supply — product
launches, regulatory decisions, fund flows, options positioning — are named as
not covered rather than approximated. HPO's question could not be answered while
two of the eight categories it reads did not exist, which is why it came last.

**Impact.** All nine categories now render a grade, a sentence and the list of
what they did not cover. Catalyst and Positioning declare coverage against parts
that include an unmeasurable one, so their coverage can never read as complete:
that is the honest state and it is deliberate. HPO is implemented as named
conditions counted, not as a combined score.

**Revisit.** The catalyst calendar will stay thin until a source for unscheduled
events exists. Positioning has no flow evidence at all.

---

### HPO is a synthesis, not a score

**Context.** HPO's question was fixed — is this, today, one of the highest
probability opportunities worth allocating capital to — and the obvious
implementation was to combine the categories into a number.

**Decision.** HPO reads the grades the categories already reached and decides a
small set of named conditions from them. Each condition holds, does not hold, or
could not be judged. The star count is a count of the conditions that hold among
those judged.

**Reason.** There is no common scale for the category measurements, so any
combination would have required inventing one — the exact thing the AIS Standard
Score entry defers. Counting named conditions needs no scale, and it has the
property that a reader can check it: every star can be traced to a condition, and
every condition to the category that decided it. A condition that could not be
judged is reported by name rather than counted as having failed, because a
question never asked is not a question answered no.

**Impact.** HPO carries no score, no confidence and no coverage. It is the first
component in AIS whose inputs are judgements rather than evidence, so it re-reads
nothing; that is what keeps it a synthesis rather than a ninth opinion. It sits
beside the overall assessment instead of inside it, so that the categories it was
built from are not counted twice.

**Revisit.** The conditions are thresholds on a provisional presentation grade.
When the standard score defines what a category reading means, the conditions
must be re-derived from it.

---

### The overall score is on its way out

**Context.** The overall score combines every category score into one number on a
scale that has never been defined, and it currently treats a larger reading as
more favourable in every category — so a measured risk raises it. It is labelled
as undefined wherever it appears.

**Decision.** Stop building on it. The daily report does not show it, no new
feature is to depend on it, and it is to be removed once the opportunity
judgement has taken its place.

**Reason.** It was a development artefact: a way to have an end-to-end pipeline
before the categories existed. Now that all nine categories produce something a
reader can use, a composite number nobody can explain adds confidence the system
has not earned. An investor is better served by eight named judgements and an
opportunity sentence than by a figure whose scale is undefined.

**Impact.** Recorded here and in the backlog. Nothing is deleted yet: the
recommendation still reads the overall assessment, and that migration is
deliberately postponed until after the product review that follows the nine
categories.

**Revisit.** When the recommendation stops reading the overall assessment. That
is a chain change and belongs to the review.

---

### Catalyst stopped being a calendar and became an event layer

**Context.** The first version of Catalyst answered "43 days until the results".
That is a fact and not an answer: an investor reading it learns nothing about why
the date matters, and every kind of event was read by its own rule, so a new kind
of event meant changing the evaluator.

**Decision.** Introduce `CatalystEvent` as a layer of its own, filled by
providers and classified by AIS, and make the category read events rather than
measurements. Company, industry and macro are the three layers, and each event
carries why that kind of event matters.

**Reason.** The question is what could change the investment case, not when
something happens, and an event is a different kind of fact from a measurement: it
has a date, a source, and a confidence in the date, none of which fit a number.
Separating the layer from the evaluator is what makes the category extensible:
adding a kind of event is a new source or a new row in a table, and the evaluator
never changes, because it only ever asks how near the nearest event is.

Classification is AIS's rather than the source's for the same reason. A provider
that decided which layer its event belonged to would be making a judgement about
AIS's own semantics, and swapping the provider would silently change how AIS
reads its world.

**Impact.** Two sources are connected: a market data vendor for company dates,
and the Federal Reserve's published schedule for policy meetings. A curated file
holds everything else, and it is empty, because AIS may not invent a date. The
report writes the calendar out by layer with a reason on every line, and the
industry layer is named as having no source rather than left out.

**Revisit.** The industry layer has no source at all, and the curated file needs
maintaining by hand. Both are recorded in the backlog.

---

### How many catalysts there are is not a signal

**Context.** With an event layer in place, the obvious scoring was to count
events: a busier calendar reads as a bigger opportunity.

**Decision.** The reading is the distance to the nearest event that could change
what the market expects. The count never enters it. Events that move the price
without moving a view — going ex-dividend, paying one — are written out and left
out of the reading.

**Reason.** Counting would say that four events next month are four times the
opportunity of one, which is not something anyone believes and not something AIS
can support. What a reader needs from a score is whether something is coming and
how soon; the report is where the calendar itself belongs. Excluding the
mechanical events keeps the reading from improving because shares are about to go
ex-dividend, which changes the price by the dividend and changes nobody's view.

**Impact.** Two assets whose nearest event is the same distance away read the
same number of stars however different their calendars are, and there is a test
that says so. No event is ranked, weighted or given a probability: AIS has no
basis for any of those, and a plausible ranking would look exactly like a real
one.

**Revisit.** When the AIS Standard Score defines what a reading means, the
exclusion of mechanical events should be restated against it.

---

### AIS moved from facts to insight

**Context.** All nine categories were implemented, and the report was a list of
measurements with a grade beside each one. "P/E 38.18, PEG 2.67" and "price above
all moving averages, momentum neutral" are true, and a reader still has to do the
interpreting themselves — which is the part they came for and the part AIS is in
a better position to do.

**Decision.** Every category now produces an **insight**: sentences saying what
its evidence amounts to, built on the analysis side, each naming the evidence it
was read from. The renderer shows them and composes nothing.

**Reason.** Repeating a measurement adds no value; interpreting it does. And the
interpretation belongs to analysis rather than to presentation, because a
renderer that composes its own explanation is doing analysis under a different
name, and it will do it differently in every renderer.

**Impact.** `analysis/insight/` holds one builder per category and a context that
offers the measurements, the events and a way to name evidence. Sentences are
capped at three per category: a fourth is always the least useful of the four,
and a phone report that is skimmed is worth less than a short one that is read.
Where the evidence supports nothing, the category falls back to its measurements
rather than to a sentence nobody can check.

**Revisit.** No.

---

### An insight is not a forecast

**Context.** Once AIS writes sentences, the temptation is to write the sentences
a reader most wants: what the price will do.

**Decision.** An insight only ever restates what the evidence supports. No
prediction, no target price, no probability, and no wording that confuses
distance with importance.

**Reason.** An interpretation can be checked: a reader who disagrees can go to the
evidence behind the sentence and argue with the rule that produced it. A forecast
cannot be checked until it is too late to be useful, and by then it has already
been acted on. The two are indistinguishable in tone, which is exactly why the
line has to be drawn in the code rather than in a style guide — there is a test
that fails if forecasting wording appears in an insight.

**Impact.** Every sentence carries evidence identifiers, and `InsightLine` refuses
to be constructed without them. The chain runs from a sentence to a measurement
to the source that reported it. A sentence that could not name its evidence would
be an opinion wearing the same clothes as a reading.

**Revisit.** No. If the line ever moves, it moves by a decision recorded here, not
by an implementation that gradually drifts across it.

---

### Which catalyst matters is decided by a table, not by a model

**Context.** With a calendar full of events, the report needed to say which of
them is worth a reader's attention. The obvious approach is a model, or a
probability, or a score.

**Decision.** Each kind of event carries a priority — primary, secondary, minor —
from one table, written by hand, in the open. The insight picks the highest
priority event rather than the nearest one.

**Reason.** AIS cannot estimate how likely an event is to move anything, and a
number that looked like an estimate would be trusted as one. What AIS can do is
state which kinds of event force an investment case to be re-examined, which is a
judgement somebody can disagree with and can see. A primary event forty days out
outranks a secondary one in two days, because distance is not importance.

**Impact.** No machine learning, no probability and no score anywhere in the
layer. The ordering is revisitable by editing one table, and the report never
says "the nearest event", which was the wording that confused the two.

**Revisit.** When industry data is connected, the ordering should be checked
against what those sources show.

---

### Market was repositioned from an index reading to an environment reading

**Context.** Market reported the broad index's change over a year, so every asset
got the same sentence. A bank, a rocket company and a gold miner were told they
lived in the same environment, which is not true and is not useful.

**Decision.** Market answers what the current environment means *for this stock*.
It draws on the macro backdrop, the industry, market style, risk appetite and
flows, and it answers in the reader's language rather than by listing an index
number.

**Reason.** The index is one input and never the answer. What an investor needs
from this category is the context their position sits in — whether the money is
currently paying for what this company sells, and what the backdrop is doing to
it. That is a different question from how the market did, and the difference is
the whole value of the category.

**Impact.** Recorded as a product principle and in the backlog. The work is not
started: the evidence it needs — industry, style, flows — is not connected, and
none of it will be inferred from a ticker. The Constitution needs no amendment:
Section 4 already asks what the environment in which this asset is being judged
is, and this sharpens the answer rather than the question.

**Revisit.** When industry and macro evidence is connected.

---

### Catalyst lists what is coming; Market explains what it means

**Context.** Catalyst can now answer what events are ahead. It cannot answer what
has just happened and what that does to the environment. Both are questions an
investor has, and they arrived close enough together to be confused.

**Decision.** Give them different tenses and forbid each from doing the other's
job. Catalyst is what is coming. Market is what is true now, including the effect
of what has already happened. Event outcomes belong in Market. No third section
is created for either.

**Reason.** Two sections answering overlapping questions is how a report starts
contradicting itself, and the reader is left to work out which one to believe.
Market is also the only category with a chance of holding the evidence an
explanation of impact needs — industry, style, flows — while Catalyst holds only
dates. A separate market brief would split one question across two places for no
gain.

**Impact.** Recorded as a principle and in the backlog. The boundary is stated in
terms of tense, which is checkable, rather than in terms of topic, which is not.

**Revisit.** When Market starts reading event outcomes, to confirm it explains
rather than relists.

---

### The report is governed by its first fifteen seconds

**Context.** The report grew a layer per round — grades, movement, events,
insights — and reached about forty eight lines. Every addition was defensible on
its own. Nobody was accountable for the whole.

**Decision.** Two rules now govern anything added to the daily report. The
opening must answer why today matters for this stock, and every new sentence must
help an investment decision or it does not go in.

**Reason.** A report nobody finishes is worth less than a short one that is read,
and the failure is invisible from inside: each round's addition looks like
progress, and the reader's experience only degrades in aggregate. Writing the
rule down gives the next addition something to fail against.

**Impact.** Recorded as product principles. It also sets a constraint on the work
already planned: the Reading Layer and the Market rework both have to earn their
lines, and what they add may have to displace something. The line budget itself is
not yet fixed, and it is in the backlog.

**Revisit.** When the report is next measured end to end against a reader's
thirty seconds.

---

### The daily report became a projection with a budget

**Context.** The report had reached 54 to 61 lines, and the widest line was 93
columns against a stated limit of 42. Both numbers were discovered by measuring
the real output rather than by anyone noticing: each round had added a layer, and
every addition was defensible on its own. The first screen held the market
environment and the fundamentals — not because they mattered that day, but
because that is the order the categories are declared in — while the most
time-sensitive category, Catalyst, sat eighth.

**Decision.** Rebuild the report as a projection with three enforced budgets: 32
lines, 42 columns, and the first 20 lines answering the whole question — which
stock, whether it is worth attention, what to do, what changed, what to watch.
Everything the phone leaves out moves to the expanded report rather than
disappearing. Each category gets a heading and **one** sentence; the movement
lines move out of the categories and into a single changes block, because what
changed is the question the report exists to answer.

**Reason.** Three specific failures drove it. The report contradicted itself in
public — HPO said "有近期催化" while the catalyst block said "近期暂无明确催化" —
because nothing owned the question of what the report as a whole was saying. The
same fact appeared twice, once as an insight sentence and once as an event list
line under it. And the budget was a comment: a limit nobody had made checkable
had already been broken by a factor of two on the most important line in the
report.

**Impact.** The first sentence of a category is now written to a width the
projection can show in one line, which shortened several of them; the model is
unchanged and the expanded report still holds every sentence. The three budgets
are asserted in `tests/test_report_projection.py`, and a second module asserts
that everything removed from the phone is present in `generate_report`. The
report went from 54–61 lines to 23–29 across the seven watched assets, with no
line over the width.

**Revisit.** The reading layer is still the next priority: the report is now
short, but it still reads its own numbers with three sets of conventions that do
not know about each other.

---

### The watch universe became membership sets, not tiers

**Context.** The first design for the watchlist put assets in tiers: a permanent
core, a growth tier, a theme tier, a temporary tier. It looked like a natural way
to decide what gets looked at and how often.

**Decision.** Drop tiers entirely. The universe is a set of **membership sets** —
Portfolio, Core, Growth, Theme, Temporary — which are unordered and may overlap.
An asset belongs to as many as apply, and nothing has to decide which single one
it is in.

**Reason.** The tier model was contradicted by its own example list: NVDA and TSLA
appear both in the M7 and in the growth list, because being a mega cap and being a
growth stock are two different facts that happen to be true at once. A tier is an
ordered, exclusive concept, and forcing overlapping memberships into it means
every later operation — what the daily report shows, what an intraday scan
considers, what is worth pushing — has to invent its own rule for resolving the
overlap, and they will not agree with each other. Sets state the facts; the
questions about what to do with them stay separate and are answered once each.

**Impact.** The universe becomes configuration with no judgement in it, which is
what makes it cheap: no evaluator, no pipeline, no report model and no contract is
touched, and the only module that changes is the one that decides what to look at.
Recorded in the backlog with the one part that is not cheap — the daily report
sends one message per asset, so scaling the universe needs a digest decision that
has nothing to do with tiers.

**Revisit.** When the Theme sets are built: a theme is an investment logic mapped
to representative assets, so the theme watchlist has to be **derived** from that
mapping rather than listed a second time.

---

### Priority belongs to the runtime because only the runtime can see enough

**Context.** The intraday engine needs to decide whether something is worth
interrupting the user for. The obvious place for a value like that is beside the
other judgements, as another input the analyzer produces.

**Decision.** Priority is a runtime result. It is computed from state at the
moment an alert is considered, never configured, and it does not enter the
analysis chain.

**Reason.** The tempting reading is that Priority is simply produced later than
the rest. The real reason is stronger: the inputs it needs are not present in the
analysis layer at all. "Relevance" means how much this matters to this user — what
they already hold, what they have already been told today, how often they have
already been interrupted. The analyzer sees one asset, once, with no portfolio, no
history and no sight of any other asset. Putting Priority there would force the
analysis layer to read runtime state to do its job, which is exactly what the
architecture forbids: the scheduler owns the runtime, and no component takes over
another's responsibility.

There is a second reason. The Constitution records one blocker about scales that
have not been defined. A priority level is a scale. Sitting in the notification
path it is a policy, and the worst it can do is interrupt at the wrong moment.
Sitting in the judgement chain it would be one more undefined scale among the
scores, and its levels would have to be argued about as though they measured
something. Keeping it out of the chain is what keeps the question small.

**Impact.** Recorded in the backlog as future design. What Priority needs —
a cross-asset view, thresholds, a record of what the user has already been told —
does not exist, so nothing is built. The note also flags that when this phase
arrives, AIS will need a statement about interrupt-driven surfaces, because every
principle written so far describes a report a reader chooses to open, and an alert
is something else. That statement is deliberately not written yet: what makes an
interruption legitimate is a product decision nobody has taken.

**Revisit.** When the intraday engine is designed.

---

### The reading layer comes before the watch universe

**Context.** The confirmed order is Reading Layer, then Watch Universe, then
Market, then the Intraday Engine, then the portfolio. The watch universe looks
cheaper — it is configuration — and it would be easy to do first.

**Decision.** Correctness first: the reading layer is built before the universe
grows.

**Reason.** The reading layer removes something already wrong: the grade, the
insights and the opportunity judgement read their own numbers with three sets of
conventions that do not know about each other, and two of those disagreements are
already visible in the reports being sent to a phone today. Growing the universe
first would multiply that by the size of the universe and put the multiplied
version in front of the reader, which is the opposite of progressive
completeness: showing more is not progress when what is shown disagrees with
itself.

**Impact.** Recorded as the confirmed order in the backlog.

**Revisit.** No.

---

### A report has two times, and they are not the same time

**Context.** The trigger list said a Daily Review fires when the market close is
confirmed. Read literally, that is 16:00 Eastern — four in the morning in Beijing
— and it was carried into the design as though it were the time the reader is
told anything. The reader objected, and was right.

**Decision.** Separate the two moments and never infer one from the other. The
**evaluation anchor** is set by the data: an analysis is worth computing once the
information behind it is complete, which the close is. The **send time** is set by
the reader: a report is worth sending when somebody can read it. 04:00 Beijing is
an anchor and is not a send time; nothing is pushed at it.

**Reason.** The two questions look like one question and are answered by different
things. The close is a statement about data; breakfast is a statement about a
person. A trigger named after the close will be read as a send time by everyone who
comes across it, which is exactly what happened here — and the resulting report
would have been correct, complete, and unread.

The corrected times also happen to be better on content, not only on comfort: a
review sent at 09:00 Beijing is five hours after the close, so the after-hours
results have landed and the after-hours move has happened. The close is the moment
the data is complete; it is not the moment the day's information is complete.

**Impact.** Recorded in the backlog with the timeline it produces: the close at
04:00 Beijing is the anchor, the review if it exists is sent at 09:00, and the
pre-market brief at 21:00 sits thirty minutes before the open and after that
morning's macro releases. The assumption that anything is pushed at 04:00 is
removed explicitly, so that it cannot be reintroduced by reading the trigger list.

**Revisit.** No.

---

### The Daily Review is kept only if it earns its place

**Context.** Once the pre-market brief was defined, the review next to it stopped
being obviously necessary. The brief already carries the analysis of the last
closed session, and it arrives twelve hours later with everything that happened in
between.

**Decision.** Do not treat the Daily Review as required. If it is kept, it is sent
at 09:00 Beijing; if it is not, it is not invented in order to fill a time slot.
The analysis it would contain is computed either way, because the brief needs it.

**Reason.** A report earns its place by what it tells a reader that they do not
already have. The review's content is close to a subset of the brief's, delivered
earlier: the same conclusion, from the same closed session, with less of the
overnight information. That may still be worth having — a reader who wants to think
in the morning gets value from it — but it is a choice about the reader's day, not
a hole in the design that needs filling. Building it because the schedule has a
gap would be adding a report for the sake of the schedule.

**Impact.** Recorded in the backlog as the one trigger that is not settled. The
distinction that makes it safe to leave open is that the **evaluation** at the close
is needed regardless; only the **delivery** is in question, and the two are now
separate decisions.

**Revisit.** When the runtime is designed, and when there is a reader to ask.

---

### The morning report is live, not a review

**This supersedes the entry above.** The rule it reached — that a report has to
earn its place in the reader's day — still stands. Its reasoning does not: it
described the morning report as a subset of the evening brief, which is wrong, and
it left the report's existence conditional on a reader wanting the same thing twice.

**Context.** Having corrected the send time to 09:00 Beijing, the morning report
was still being described as a recap: the close happened at 04:00, the reader reads
at 09:00, so the report was the close explained later. That description was wrong,
and it led to a second wrong conclusion — that the morning report was close to a
subset of the evening brief and had to justify existing.

**Decision.** The morning report is **live**. It is computed at the moment it is
sent, from the freshest state available then, covering everything between the
previous report and this one. It answers what the state is now and what changed to
get there, and it is never described as a summary of the previous session.

**Reason.** The subset reasoning assumed both reports describe the last closed
session. They do not: the evening brief goes out **seventeen hours before** that
session closes, and the morning report **five hours after**. Between the two lie an
entire US session, the after-hours move and the Asian session. The morning report
is not a repetition of the brief; it is the only report that can contain the
session at all.

There is a second reason, and it is about the reader rather than the data. A report
is worth sending at the moment a reader can act on it, which means it has to reflect
the world at that moment. Building it at the close and delivering it at breakfast
would produce a document that is correct, complete, and five hours out of date — the
worst kind of wrong, because nothing about it looks wrong.

**Impact.** The name is **Live Morning Brief** and the backlog states that it is
computed at send time, with the timeline that shows why the two reports cannot be
substitutes for each other. It also surfaced a consequence that had not been
noticed: a report whose job is to say what changed needs a baseline that outlives
the process, and AIS keeps both of its baselines — the rating standings and the
notification fingerprints — in memory only. Today a restart merely makes the next
report read "first rating" everywhere. With scheduled reports built around change,
it would erase the only thing they exist to say.

**Revisit.** No.

---

### One layer decides what a number means

**Context.** AIS read its own numbers with three sets of conventions that did not
know about each other. The star grade had a table of thresholds; the sentences had
their own copies of the same numbers; the opportunity judgement had a third on top
of a rounded average. Two of the disagreements were visible in reports being sent
to a phone: an asset could be given the near term catalyst condition while the
sentence forty lines below said there was no clear catalyst in the near term, about
the same calendar from the same run.

**Decision.** One owner, `evaluation/reading/`, holds every scale, every window and
every bar. The grade becomes a view of a category's reading and keeps no threshold
of its own; the sentences read bands instead of numbers of their own; the
opportunity judgement reads the category's reading instead of its rounded star.

**Reason.** The contradictions were not carelessness; they were the predictable
result of three components each answering the same question privately. Nothing
could have caught them, because nothing was comparing one answer with another. The
second reason is the one that pays later: the standard score will replace exactly
one thing now, instead of three things that would first have to be argued into
agreement.

**Impact.** The known contradictions are gone and
`tests/test_report_consistency.py` checks a rendered report for new ones — whether a
condition that holds is denied by a sentence drawn from the same readings, and
whether the headline and the sentence agree about what "near term" means. Writing
that test found two more overstatements nobody had noticed: a short side described
as middling was being called heavy in the next line, and a trend structure could be
called broken while the trend still read well.

**Revisit.** No. The values inside the layer stay provisional and are replaced as a
whole.

---

### A condition needs two bars, not one

**Context.** The valuation in a real report read four stars and "估值具备吸引力"
while the sentence beside it said the free cash flow was negative and the valuation
had no cash support. Both were produced from the same run.

**Decision.** An opportunity condition is decided on two readings of the category:
the mean, and the weakest measurement. The mean must reach the bar **and** nothing
in the category may fall into the bottom two bands.

**Reason.** The mean was not wrong; it was answering a different question from the
sentence. Cheap multiples beside a negative cash flow average out to attractive, and
a category that reads well on balance has not thereby read well — the question the
condition asks is whether the category reads well, not whether it reads well on
average. The second bar is what makes "attractive" mean nothing in the category
disqualifies it.

How the weakest bar is chosen is a rule rather than a preference: **it is set so
that no sentence denying the condition can fire.** That drew a line through the
sentences as well as the bars — a sentence saying the structure has broken, or the
balance sheet is stretched, or the short side is heavy, had to move down into the
bands a satisfied condition can never reach. Both ends are held by the consistency
test.

**Impact.** HPO is stricter, and visibly so: across the seven watched assets it now
reads one for six of them. That is the honest output of the conditions as stated,
and it is recorded in the backlog as a shape worth deciding on rather than a defect
to tune away.

**Revisit.** When the standard score defines what a reading means, both bars are
re-derived from it.

---

### Configuration describes what AIS chooses, never what is true

**Context.** The watch universe has five membership sets — Portfolio, Core, Growth,
Theme and Temporary — and the obvious reading of that was five lists in a file.
Two of them cannot be lists in a file without becoming wrong.

**Decision.** The file carries three things: the core members, the growth members,
and the mapping from a theme to its representative assets. Portfolio and Temporary
are sets of the same universe and are never written down. The theme watchlist is
derived from the mapping rather than listed beside it. The loader lives in
`config/`, because a watchlist is AIS's own configuration and not data collected
from the world.

**Reason.** Whether AIS holds something is decided by a broker, not by a person
editing a file. If the file could say so, the configuration would begin asserting a
position before there was anything to assert it from, and nothing would ever
correct it — a second portfolio, written by hand, drifting quietly away from the
real one. The same holds for Temporary, whose members the calendar adds and the
runtime removes; a hand-written temporary list is a list nobody removes from.

That is the general form, and it is the reason this is a principle rather than a
note about one file: **a setting tells AIS what to do, and a file that tells it what
is true is a file that will eventually be lying.** Configuration is where choices
live. Facts come from the component that owns the fact.

The derived theme watchlist is the same idea applied inside the file. Two lists of
the same members — one as a mapping and one as a membership — do not stay equal, and
whichever one a component happens to read becomes the real one.

**Impact.** Recorded in the backlog with the boundary table: five sets, three
sources, only one of them a file. The model holds one entry per asset carrying the
sets it belongs to, so a symbol cannot appear twice with two copies of its own
metadata. The phase stays small for the same reason — the universe decides what is
looked at and never what is concluded, so no evaluator, no pipeline and no report
model is touched.

**Revisit.** When the Portfolio Layer arrives, it fills the Portfolio set and
nothing about the file changes.

---

### One scheduled report until the evidence can tell two apart

**Context.** Two scheduled reports were defined: a pre-market brief at 21:00 Beijing
and a live morning brief at 09:00. Both were about to be built, and the question was
asked whether they could be sent now.

**Decision.** Only the morning one runs. The pre-market brief stays defined and
stays off until the Market Layer exists.

**Reason.** The two would be the same report. AIS reads a quote summary and a year
of daily bars per asset, and that evidence changes about once per trading day. At
09:00 Beijing the latest completed US session is D-1 — and at 21:00 Beijing the
session has still not opened, so the latest completed session is **still D-1**, and
the latest bar is the same bar. Two reports built from one piece of evidence are not
two reports; they are one report sent twice, and the second copy arrives when the
reader has already read the first.

There is a worse version of the same problem. If the source ticks a price during
extended hours, the second copy will not be identical — it will show a movement that
is not news. **A report whose only change comes from resampling the same data is
worse than no report**, because it teaches the reader to look for meaning where
there is only noise.

What makes 21:00 a report of its own is therefore not the clock. It is the
market-level evidence — pre-market prices, futures, volatility, yields, the dollar,
the morning's macro releases — that only exists at that hour. Phase C is what turns
the pre-market brief from a second copy into a report.

**Impact.** Recorded in the backlog as the reason the order is Phase C then 21:00,
and recorded explicitly that this is not a decision to build the 09:00 trigger: the
scheduler still has no notion of an hour, and the market-open gate still skips
everything outside the US session.

**Revisit.** When the Market Layer can answer what changed overnight.

---

### The runtime stopped being an interval and became a set of schedules

**Context.** AIS ran one thing on one cadence: the evaluation cycle, every thirty
minutes, its phase set by whatever moment the process happened to start. Everything
else about when AIS speaks was decided inside that cycle — whether the market was
open, whether the conclusion had changed — so the two questions "when should this
run" and "should it speak" were answered in the same place, by the same code.

**Decision.** The scheduler now runs **schedules**, each of which answers one
question: when am I next owed? It sleeps to the earliest answer and runs what is
due. Two are wired — the cycle on its interval, and the morning brief at an hour of
the day — and each carries its own rules about the market and about change.

**Reason.** The brief could not be built any other way. It is owed at 09:00 Beijing,
which falls outside the United States session by definition, so a cycle that skips
whenever the market is closed can never reach it; and it is expected every day, so a
cycle that says nothing when nothing changed is the wrong shape for it. Both of
those were properties of the *cycle*, not of the work, and separating the schedules
is what let the brief have its own.

**Impact.** The loop still lives in one place and still owns nothing but timing. The
market gate and the change detector stayed exactly where they were for the cycle, so
nothing about the existing behaviour moved; the brief simply does not consult either.
Adding the pre-market brief later is another schedule and nothing else.

**Revisit.** No.

---

### A brief is owed; an alert has to earn it

**Context.** AIS had one rule about speaking: say nothing unless the conclusion
changed. The morning brief says something every day, which reads at first like the
opposite of that rule.

**Decision.** Separate the two. A report the reader is expecting is owed whether or
not it has news; an interruption the reader is not expecting has to earn the
interruption.

**Reason.** The change rule exists so that an unchanged conclusion does not become a
stream of identical messages. It works because the reader did not ask for those
messages. A brief is different in kind: the reader chose the hour and opened the slot
for it, and "nothing has changed" is the answer to the question they asked, not a
failure to answer it. Applying the change rule to the brief would mean the report
arrives on the days something happened and silently does not on the days nothing did
— which turns a daily report into an unpredictable one, and makes its absence
ambiguous.

There is a second reason, about what "unchanged" even means over a day. The brief is
sent once per trading day, and the evidence behind it changes about that often, so it
describes a state that has genuinely moved. It is not the same report again merely
because the conclusion held; the change rule governs interruptions, not repetition,
and a report that describes the present is not a repetition of one that described
yesterday.

**Impact.** The brief sends whatever it finds. The change detector still guards the
cycle, unchanged. What both share is the analysis: one engine, two reasons to speak,
and the reasons kept apart.

**Revisit.** When the intraday alert is designed, which is the case that really does
have to earn its interruption.

---

### "Once a day" is not something a process can remember

**Context.** The brief is owed once per local day, and the process that sends it is
restarted whenever the machine is restarted.

**Decision.** The day the brief was last sent is written to `state/runtime.json`,
by replacement, and read at startup. A brief missed because the process was not
running is sent late rather than dropped.

**Reason.** Neither half of "once" survives memory. A process that starts at noon
cannot know whether the brief already went out, and one that starts at ten cannot
know whether it was missed. Both questions are about the past, and the only thing
that answers a question about the past is something written down. The written day
also settles the case a person would ask about first: a restart an hour after the
brief does not send a second copy to the same phone.

Two details are worth keeping. The day is recorded **whatever the outcome**, because
retrying a delivery failure would send a second copy to whoever the first attempt
reached and would repeat a full evaluation of the universe on every wake until it
stopped failing — a failure is reported as a failure instead. And the day is
remembered **in memory as well as on disk**, so a state file that cannot be written
does not make the brief permanently due.

**Impact.** `state/` is a new directory, gitignored, holding what AIS has done rather
than anything about the world. The backlog records the half of the problem that is
still open: the runtime remembers what it owes, and still does not remember what it
concluded.

**Revisit.** When the baseline a report compares against has to survive a restart
too.

---

### A brief is a document, not a shorter pile of messages

**Context.** The brief sent one message per watched asset. With seven assets that is
seven notifications arriving within a few seconds of each other, each repeating the
timestamp, the source line and the structure, and each carrying one asset's
conclusion. The reader asked one question — what should I look at first today — and
received seven answers to a different one.

**Decision.** Add a second report model. `analysis/brief.py` holds the brief: a set of
entries, each carrying an analysis result and the reason it earned a line, plus the
coverage it was selected from. `analysis/brief_report.py` renders it as one message.
The application sends that message once.

**Reason.** The report model described one asset, and every renderer was a projection
of it. That is why seven assets could only be seven reports: there was nowhere for a
document about several assets to exist. The alternative was to keep the per-asset
model and shorten its text, which produces a feed of small messages rather than a
brief — and the difference is not length. A brief answers *what matters today* and a
per-asset report answers *what AIS knows about this asset*; no amount of trimming
turns the second into the first, because the second has no place to say that one
asset matters more than another.

So the digest is a model, and what the two models share is the projection layer:
width, wrapping, and the threshold below which a movement is not worth a line. Those
moved into `analysis/projection.py` for the same reason the reading layer exists —
two places deciding what a number means is how a report came to disagree with itself,
and two places deciding what fits on a line would do exactly the same thing.

**Impact.** The message is one message whatever the size of the watchlist, and the
watchlist can now grow. The per-asset report is still rendered for every asset and
still written to the log, so the phone showing less costs the system nothing. The
cycle is untouched: one asset changing is news about that asset and still gets its
own message.

**Revisit.** No.

---

### Coverage and projection stopped being the same number

**Context.** With one message per asset, "what AIS looked at" and "what the reader was
sent" were the same list by construction. Nobody had to decide what to leave out,
because nothing was left out.

**Decision.** Separate them. Every watched asset is analysed; at most three are
written into the brief. The brief states both numbers and names the assets it did not
write out.

**Reason.** The two sets answer different questions. Coverage is bounded by how much
AIS can look at, which is a cost AIS pays. Projection is bounded by how much a reader
will read, which is attention the reader pays. Tying them together means the second
grows whenever the first does, and a brief for thirty symbols would be thirty
messages — the failure mode is not that the reader stops reading the brief, it is
that the reader stops reading AIS.

The harder half is what the reader is owed about the gap. A brief that shows three of
seven assets and says nothing else can be read as a quiet universe when it is really
a narrowed one — the same failure as reporting an unexamined dimension as a safe one.
So the count and the names are in the message, and the full report of every asset is
in the log.

**Impact.** `MAX_FOCUS` is a number in one module, and the brief's budget no longer
depends on the watchlist. What is left open is recorded in the backlog: the brief
names what it left out, and it does not yet know which of the assets it left out
would have mattered most.

**Revisit.** When the watch universe is large enough that three is the wrong number,
which is a decision about attention and belongs to the product owner.

---

### What earns a line is a reason, and a score would have been a new method

**Context.** A brief has to decide which assets to write out. The obvious
implementation — score each asset, sort, take the top three — is the one thing this
project is not allowed to invent: a scoring method.

**Decision.** An asset earns a line through the first named slot that applies to it,
in a stated order: held and moved, held, moved, where it stands, and otherwise
nothing. Inside the standing slot — which risk and opportunity share — the count of
opportunity conditions that hold decides, and ties fall to how near the nearest event
that could change a view is and then to the order the universe holds.

**Reason.** Every part of that ordering is a judgement AIS has already reached and
already shows the reader: the portfolio layer decides what is held, the rating
tracker decides what moved, the opportunity assessor decides which conditions hold,
and the calendar decides what is near. Combining them into a number would create a
new scale with no meaning behind it, and the first question anybody asked about it
would be why one asset scored 0.7 more than another — a question with no answer,
because the weights would be ours. Ordering by named reasons answers the same
question in words the reader can argue with.

**Risk was ordered above opportunity first, and the live run reversed it.** The first
version read the Constitution's "manage risk before return" as an ordering rule and
put every asset whose risk condition fails ahead of every asset with a case. On a run
of the seven watched assets the risk condition fails for six of them, so the brief
led with three copies of the same warning and left HSBC — the one asset whose
judgement read three conditions instead of one — inside the list of assets it did not
write out. That is not a brief choosing the most important thing; it is a brief
choosing the most common one. The rule about risk governs the decision, which the
evaluators make and where risk is read first; it does not order the lines of a report.
So the two reasons now compete in one slot and the count of held conditions separates
them, which is a judgement AIS already reached.

**Impact.** The whole policy is one table in `analysis/brief.py`, and both the
ordering and the labels a reader sees come from it. Adding a slot later is a row in
that table. The brief states the reason on the line where a judgement supports one,
so a reader can see why an asset was shown and another was not — the same obligation
the report has to its evidence.

**Revisit.** When Priority becomes a runtime concept with a threshold, which is the
first thing that could legitimately outrank a judgement.

---

### The brief does not say what the market is doing, because it cannot

**Context.** The brief was specified with a market state at the top: today's
conditions, the most important external change. AIS has no market-level evidence —
that is Phase C — and what it does have is a market reading carried per asset, which
is a twelve-month index move.

**Decision.** The brief states the events that bear on every asset and says nothing
about the state of the market. A macro event arrives in every asset's calendar on the
same date, so it is reported once at the top and is not repeated beside each entry.

**Reason.** A twelve-month index move is not a statement about today. Writing it
under a heading that says "the market today" would be the report asserting something
its evidence does not carry, and nothing about the output would look wrong — the
worst kind of wrong, because it cannot be seen. The honest position is that the brief
knows what is on the calendar and not what the market is doing, and says so; the line
arrives with the evidence that supports it, in Phase C.

**Impact.** The top of the brief carries coverage and the shared calendar. The
backlog records the market state as an open item with the same dependency as the
21:00 brief — one reason the two should be designed together rather than twice.

**Revisit.** In Phase C, when there is market-level evidence to report.

---

### A message that reached nobody is not a message

**Context.** The brief sent one digest at 09:00 and recorded the day as done whatever
the attempt returned. The log then showed it firing on three consecutive mornings and
delivering nothing: the machine had no route to the network at that hour, both the
market data source and the notification channel were refused, and every asset was
reported as failed. The trigger was right every day. The reader never received a brief,
and the state file said the day had been sent.

**Decision.** The runtime's memory of a day becomes a **state** rather than a flag:
`owed`, `sent` or `abandoned`, with the attempt count and the moment of the last
attempt. An attempt that reached at least one channel settles the day; an attempt that
reached nobody leaves it owed and spaced for another try; the attempts are capped, and
running out abandons the day rather than retrying until midnight.

**Reason.** The old rule — a failure is not retried, and the day is recorded whatever
happens — was written for a *partial* failure, where a retry would send a second copy
to whoever the first attempt had already reached. That reasoning is sound and it is
preserved: a channel failing while another delivers is a degraded delivery, not a
missing one, and it settles the day. What the rule did not have was the other case.
When every channel fails, nobody has been told anything, and "already handled" is
false.

**The difference had to be reported, not inferred.** The run's status could not carry
it: an asset that cannot be analysed and a message that reaches nobody both surface as
a failed run, and they mean opposite things for the day. So the brief asks the
application for two facts — what the run did, and whether anybody was told — and the
state machine is built on the second.

**Spacing is not decoration.** The hour the brief is owed at is already behind once it
has run, so a failed attempt would be due again the instant it failed. That is a loop
that costs a full analysis of the universe every time round, and it is what makes the
retry interval part of the state rather than a detail of the scheduler.

**Impact.** The day survives an outage that lasts minutes, which is the failure that
actually happens, and it stops after three attempts, which bounds what an outage that
does not end can cost. A restart reads the attempts back, so a process that keeps
coming back cannot restart the count. What is not solved is the reader who is told
nothing all day: the channel that would tell them failed, and the runtime logs it
instead.

**Revisit.** When an alert has its own delivery state, which is the same question with
a threshold in front of it.

---

### The same conclusion is written once

**Context.** The brief had become one message, and it still said the same sentence
three times: on a real run the watched universe read `★★☆☆☆` for six assets of seven,
so the three assets a brief writes out carried an identical line each.

**Decision.** Assets that reached the same conclusion are written under one statement
of it, labelled, with their own headings beneath. Two assets reached the same
conclusion when their opportunity judgements hold the same number of conditions.

**Reason.** A brief that has already been reduced to one message and then repeats one
sentence three times has spent its width on nothing. What the reader needs from the
second and third asset is what is *different* about them — where each stands, why each
is in the brief, what each has ahead — and every one of those is still on its own line.
The conclusion is the part that was the same.

**And the alternative was declined.** The other way to stop the repetition is to make
the reading less uniform, so that the assets do not all read alike. That would mean
loosening the Reading Layer, and the Reading Layer is strict because it is internally
consistent: it says one thing about a measurement, and every sentence, grade and
judgement reads the same decision. Adjusting it to produce variety in a report would
put back the contradictions that work removed. HPO reading 1 for six assets is the
reading; a report that finds it boring has a projection problem, not a reading problem.

**Impact.** The grouping lives in the brief model, not in the renderer: which assets
share a conclusion is a fact about the document. Grouping never reorders the brief — a
group sits where its most important member sat — so an asset whose own standing is
lower can appear above one that outranks it. That is the price, it is stated, and every
heading still carries its own standing so nothing is hidden by it.

**Revisit.** When the watch universe is large enough that three assets rarely share a
conclusion, at which point the label is doing nothing and can go.

---

### A fixture dated from a constant expires

**Context.** One test failed for a reason that had nothing to do with any change:
`test_a_primary_event_outranks_a_nearer_secondary_one`. Its events were dated from a
constant moment in the test file while the insight layer reads a result that carries no
market data against the current moment — so on the day the constant left the catalyst
window, the fixture's events stopped being upcoming and the assertion had nothing left
to find.

**Decision.** The fixture's moment follows the clock. `_MOMENT` is the moment the test
module is imported, and the events are dated relative to it, so the fixture is
self-consistent whenever it runs.

**Reason.** A test that passes on the day it is written and fails a week later is worse
than no test: it teaches whoever meets it to distrust the suite. The cause here was not
the constant itself but the mismatch — the fixture's own moment was fixed while the
code under test read the real clock, and an event that is two days ahead of a date in
the past is not ahead at all.

**Impact.** The same shape was found in the brief's own tests, which asserted a
particular day against the system clock; they take the moment they run at from a
supplied clock now, which is the pattern the scheduler already used. The rule that
comes out of it: **a test that depends on now supplies now**, and a fixture with dates
in it is dated from one moment rather than two.

**Revisit.** No.

---

### The environment is evidence, and it belongs to no asset

**Context.** Market reported the broad market's change over a year, which the vendor
hands over with every asset's own figures. That was the only market-level fact AIS had,
and it meant every asset was judged in an environment described identically, which is
the failure the category was created to fix.

**Decision.** The market's own measurements — the equity futures since the last close,
the volatility index, the ten year yield — become a **separate input**, retrieved once
per pass and shared by every asset in it. They arrive through the same evidence stream
as everything else, are filed under the Market category, and are read through the same
reading layer. Only their identifiers differ, because they carry no ticker.

**Reason.** Three things pushed the same way. Fetching them per asset would fetch one
fact once per asset and let the copies disagree about the same morning, so the retrieval
belongs where a pass is known. Putting them in the per-asset snapshot was not available:
a snapshot carries one point per metric, and six market measurements would appear in
every asset's provenance as missing, which is a lie about where the numbers come from.
And filing them under Market rather than inventing a Market Data category keeps the
one question the category asks — what is the environment this asset is judged in —
while widening what it can answer.

**Impact.** Coverage of the market question went from one aspect of four to four of
four on a live run. The aspects themselves did not change: volatility and rates were
declared and listed as unmeasured long before anything measured them, which is what the
aspect set was for, and the evidence that closed the gap did not move the question. The
evidence is written out once in the expanded report and its one user-visible line is a
line of the brief, not a section of it.

**A defect the change exposed.** With the new rules in place, a run with no source at
all reported **four of four** aspects assessed, because each rule returns a placeholder
and a placeholder was counted as an examined aspect. That is the same failure the aspect
set exists to prevent, only with better numbers. An aspect now counts when a rule
actually read something, and the placeholder stays what it was for: keeping the pipeline
deterministic.

**Revisit.** When the industry, flow or currency evidence is connected, which would add
aspects rather than change these.

---

### A fact about the market is not a judgement about an asset

**Context.** The first version of the sentences was going to say what the environment
was doing, which is what a market recap says. That is the thing the category is not.

**Decision.** Every Market sentence names **both halves**: an environment measurement
and one of the asset's own, in the same sentence, with both in its references. A rising
yield beside a valuation that reads expensive is a finding; a rising yield is not. A
weak tape beside a high beta is a finding; a weak tape is not.

**Reason.** The category's question is what the environment means for this stock, and a
sentence that answers it has to say which stock. It also has to be checkable: a reader
who disagrees with "利率上行而估值很贵，分母端承压" can see both halves and argue with
either, which is not true of a sentence that reports the market and lets the reader
supply the consequence.

**The environment itself is stated once, and separately.** It is the same for every
asset in the market, so the brief leads with it before any asset and the per-asset
reports carry it as the second sentence behind the sentence about the asset. The first
sentence of a category is what a phone shows, so the first sentence of Market had to be
the one about the holding.

**And two of the five measurements are never graded.** Risk appetite and volatility are
graded, because a tape being bought and a calm market are favourable conditions for
owning risk and the direction scale already grades exactly that. Rates and the change in
volatility are described and not scored: a rise in the cost of money is not better or
worse in itself, and it is not worse for a bank than for a software company until an
asset is named. Scoring it would have made the category's grade express a preference
the reading layer does not hold.

**Impact.** The sentence table is five rows, each a pair. Where a mechanism needs
evidence AIS does not have — a bank's margin needs the shape of the curve, and AIS has
one yield — the sentence names the exposure and says the direction is not judged. The
dollar is left out entirely for the same reason: its move is retrievable, and without
knowing where an asset earns its revenue there is no effect to state.

**Revisit.** When a sector or industry environment is connected, which would add rows to
the table rather than change the rule.

---

### A vendor's "previous close" is not the previous close

**Context.** The environment's measurements are changes, and the vendor's chart endpoint
offers two candidate baselines: a `chartPreviousClose` and the closes in the series.

**Decision.** The change is read as the last two closes of the series, and
`chartPreviousClose` is deliberately not used. A live probe made the reason concrete:
for the S&P futures it returned 7,589.25 while the previous session had closed at
7,640.00, so reading it as "the previous close" would have reported four sessions of
movement as one overnight move — a number that looks entirely plausible in a report.

**Reason.** The field is the close before the range that was requested, which is a fact
about the request and not about the market. Nothing in its name says so, and the
mistake it invites is invisible in the output: the change is still a change, the
sentence still reads correctly, and only the window is wrong.

**Impact.** The derivation is carried in each point's own reason, so a reader of the
expanded report can see which two sessions a move was measured between. Sessions with no
close are dropped rather than carried forward, which would turn a gap into a flat
session.

**Revisit.** No.

---

### The part of the market an asset is in is stated, and measured against the market

**Context.** Market could say what the whole market was doing and nothing about the
part of it a holding actually sits in. "The market is up" says little about a bank, and
"financials are being sold while the market is bought" says a great deal about one. The
first evidence round left this as the largest remaining gap, and it is the one the
product owner put first.

**Decision.** Two halves. The **sector** is stated per asset in the watchlist, beside the
profile. The **measurement** is that sector's move less the broad market's over the same
session, read once per pass for the sectors the universe is actually in — six for seven
assets, not eleven — and paired with the asset's own sector in a sentence.

**Why the sector is stated rather than taken from the vendor.** The vendor publishes a
sector for almost every symbol, and it was used to fill the current entries in. What it
cannot be is the authority. Which sector an asset is in decides which comparison AIS
makes and therefore which sentence it can write, and that is the same class of label as
the profile: a guessed one changes what AIS is able to say, and the change is invisible
in the output because a sentence about the wrong sector reads exactly like a sentence
about the right one. A vendor's taxonomy also has no way to be argued with — half a dozen
providers classify the same company differently — while a line in a file can be corrected
by the person who reads the report. So the file states it and the vendor does not.

**Why the measurement is relative.** A sector's own move answers nothing: the market
moved too, and on a day when everything falls 2% and one sector falls 1%, the number
that matters is the one point of difference. The relative move is computed once and
stored as one value, so nothing downstream can subtract the two in the wrong order or
over different windows.

**Why it is graded, and where it sits.** Where the asset's own part of the market is
going is a condition of the environment the asset is judged in, so it counts toward the
Market grade like the direction of the market does. Two assets in different sectors
therefore get different Market grades, which is the point: their environments differ. It
is the first sentence of the category, because it is the most specific thing the
environment can say about a holding.

**What it does not claim.** A relative move is consistent with money leaving a sector
and it is not a flow figure, so the sentence states the comparison — 所属板块（科技）
跑输大盘 — and never claims the flows. An asset with no stated sector gets no sector
sentence at all: an exchange-traded fund holds a style rather than a sector, and being
told nothing is honest where being told something plausible is not.

**Impact.** The sector is the first label AIS states about an asset that a vendor could
have supplied, and the reversal is deliberate and recorded: the report is corrected by
the person reading it, not by a taxonomy nobody in this project controls. A sector that
cannot be recognised is left absent with a warning, so a typo costs a sentence rather
than producing one about the wrong part of the market.

**Revisit.** If the watchlist ever grows to the point where stating a sector per entry
is a burden, which is the point at which a vendor may become the authority for the ones
nobody has stated.

---

### Only the gaps that change a judgement, and in the order they change it

**Context.** The environment layer left a list of things not connected: the industry, the
style, flows, realised macro releases, the shape of the curve, the currency. The
instruction was to fill the ones that change a judgement, in priority order, and not to
complete for completeness.

**Decision.** One round, one gap, chosen as the largest: the industry and the style. The
other two were investigated, and each stops for a different reason.

**The macro release result has no source.** The vendor publishes no economic calendar,
and the central bank provider publishes meeting dates that are still ahead — checked
directly, its next event is a month away and it holds nothing behind it. So "what the
overnight release said" cannot be read today. What can be read is the market's own
response to it, and that is what the futures, volatility and yields already record: the
report can say the tape moved, and it cannot yet say what moved it. That is a gap with a
reason, and it stays a gap.

**The curve has a source and needs a decision first.** The United States Treasury
publishes its whole daily curve as CSV with no key, which would close the one sentence
in the report that currently admits it cannot judge a direction: a bank's margin moves
with the shape of the curve, and one yield is not a curve. What has to be decided before
it is built is smaller than it looks and is not technical: the ten year yield currently
comes from the vendor, and adding a Treasury ten year beside it would let the report
state two slightly different numbers about the same thing. Either all of the rate
readings move to the Treasury together, or the curve arrives without its legs. Deciding
that is a sentence about the product, not a line of code, so it waits.

**Reason.** A round that fills three gaps at once is a round nobody can review, and the
third gap's value is concentrated in one asset: the curve sentence is about banks, and
there is one bank in the universe. The sector reading is about all seven.

**Impact.** The watchlist gained a field, the environment gained a collection it did not
have — one reading per sector rather than one for the market — and the reading layer
learned to read a measurement whose subject is chosen per asset. Everything else was
already in place, which is what the earlier rounds were for.

**Revisit.** When the curve decision is taken, which is the next thing worth doing.

---

End of Document
