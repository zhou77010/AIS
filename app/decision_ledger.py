"""The decision ledger: what AIS concluded, written down as it concludes it.

A report is read once and a log is searched by a person. Neither is a dataset, and a
validation that has to be reconstructed from prose is a validation nobody can run twice.
This writes one line per asset per pass, so that what AIS concluded on a given day can
be
replayed, counted and compared later without reading anything back out of a message.

**It records, and it decides nothing.** The ledger is not read by the runtime, it
changes
no judgement, and nothing downstream of it can alter what was concluded: it is a copy of
the conclusions taken at the moment they were reached.

**It is append only, unlike the state file.** The state file is written by replacement
because it answers "what is owed now", and only the latest answer matters. A ledger
answers "what was concluded then", so every line is kept and no line is overwritten. A
line that cannot be parsed later costs its own row and nothing else.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from analysis.analysis_result import AnalysisResult
from config.logging_config import get_logger

_LOGGER_NAME = "runtime"

# What the ledger file is called beside the state file. It is configuration's directory
# rather than a path of its own, because it is state: the runtime writes it and a person
# does not.
FILE_NAME = "decisions.jsonl"


@dataclass(frozen=True)
class DecisionLedger:
    """Appends what each pass concluded, one line per asset.

    Attributes:
        path: File the lines are appended to.
    """

    path: Path

    def record(self, result: AnalysisResult, *, moment: datetime) -> None:
        """Append one asset's conclusion for one pass.

        A result without a Decision writes nothing: a ledger row with no conclusion
        would
        be a row that says a judgement was made when none was.

        Args:
            result: The result a pass produced.
            moment: Moment the pass ran, which is the moment the conclusion belongs to.
        """
        decision = result.decision
        if decision is None:
            return
        line = {
            "moment": moment.isoformat(),
            "ticker": result.asset.ticker,
            "outcome": decision.outcome.value,
            "summary": decision.summary,
            "conditions": {
                outcome.condition.value: outcome.satisfied
                for outcome in decision.conditions
            },
            "reasons": {
                outcome.condition.value: outcome.reason
                for outcome in decision.conditions
            },
            "evidence_references": list(decision.evidence_references),
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        except OSError as error:
            # A ledger that cannot be written costs the record of one pass. It must not
            # cost the pass itself, which has already produced a conclusion for a
            # reader.
            get_logger(_LOGGER_NAME).error(
                "the decision ledger at %s could not be written: %s",
                self.path,
                f"{type(error).__name__}: {error}",
            )
