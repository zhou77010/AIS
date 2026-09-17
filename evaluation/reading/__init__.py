"""AIS reading layer.

The single owner of what a number means.

It exists because AIS read its own numbers with three sets of conventions that did
not know about each other: the star grade had one table of thresholds, the
sentences had their own copies, and the opportunity conditions had a third on top
of a rounded average. They disagreed in public — a report could call a valuation
attractive directly above a sentence saying the cash flow did not support it.

Everything a reading decision needs is here:

* :mod:`evaluation.reading.bands` — one scale per measurement, with the word each
  band is described by and the score it carries.
* :mod:`evaluation.reading.windows` — the time windows, so that "near term" means
  one thing wherever it is said.
* :mod:`evaluation.reading.category` — what a category's measurements mean
  together, which is what a grade is a view of and what the opportunity judgement
  reads.
* :mod:`evaluation.reading.conditions` — the thresholds the opportunity conditions
  are decided at.

**It is provisional, and it is replaced as a whole.** These conventions are not the
AIS Standard Score and are not a decision anyone has approved. When the standard
score is defined it replaces this package, and nothing outside it has to be
reconciled first.
"""
