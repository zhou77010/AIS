"""AIS insight package.

Turns the evidence a category collected into what it means. Each category has a
builder that reads only that category's evidence and writes sentences the
evidence supports, each carrying the identifiers of the evidence it was read
from.

Two rules hold everywhere in this package:

* **Interpretation, not prediction.** A sentence says what the measurements
  amount to. It never says what will happen, and it never puts a number on a
  future outcome.
* **Nothing is written without evidence.** A builder that cannot support a
  sentence writes no sentence. An empty insight is a truthful statement that the
  evidence did not support a reading, and it is preferred to a fluent one that
  nothing stands behind.
"""
