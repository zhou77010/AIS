"""Tests for the decision ledger: what AIS concluded, written down as a dataset.

The ledger exists because a paper validation needs a record rather than a memory. So the
tests here are about the two properties that make it usable: every pass appends a line
and
no line is ever overwritten, and a line carries enough to replay the conclusion - the
answer, each condition's outcome, the reason beside it and the evidence behind it.

It is also, deliberately, not on the runtime's reading path: nothing in AIS reads the
ledger, so the tests say that it records and decides nothing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from analysis.analysis_result import AnalysisResult
from app.decision_ledger import DecisionLedger
from models.asset import Asset
from models.asset_profile import AssetProfile
from models.decision_result import (
    ConditionOutcome,
    DecisionCondition,
    DecisionOutcome,
    DecisionResult,
)
from models.decision_state import DecisionState
from models.overall_assessment import OverallAssessment
from models.recommendation import Recommendation

_MOMENT = datetime(2026, 9, 23, 4, 0, tzinfo=UTC)


def _result(ticker: str = "AAPL", *, decision: DecisionResult | None) -> AnalysisResult:
    """Return a result as a pass produces one, with or without a Decision."""
    return AnalysisResult(
        asset=Asset(
            ticker=ticker,
            name=f"{ticker} Inc.",
            exchange="NASDAQ",
            currency="USD",
            profile=AssetProfile.UNKNOWN,
        ),
        assessment=OverallAssessment(
            overall_score=0.0,
            confidence=1.0,
            grade="PLACEHOLDER",
            category_scores=(),
        ),
        recommendation=Recommendation(
            decision_state=DecisionState.WATCH,
            confidence=1.0,
            investment_thesis="",
            evidence_references=(),
        ),
        decision=decision,
    )


def _decision(outcome: DecisionOutcome) -> DecisionResult:
    return DecisionResult(
        outcome=outcome,
        conditions=(
            ConditionOutcome(
                condition=DecisionCondition.TERMS,
                satisfied=outcome is DecisionOutcome.FAVOURABLE,
                reason="valuation reads 2 with a weakest member of 1, against a bar",
            ),
            ConditionOutcome(
                condition=DecisionCondition.CURRENCY,
                satisfied=True,
                reason="the judgements were read from data retrieved at this moment",
            ),
        ),
        summary="1 of 3 conditions hold",
        evidence_references=("AAPL.valuation.pe", "AAPL.risk.pe"),
    )


def _lines(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_a_pass_writes_one_line_per_asset(tmp_path: Path) -> None:
    path = tmp_path / "decisions.jsonl"
    ledger = DecisionLedger(path=path)

    ledger.record(
        _result("AAPL", decision=_decision(DecisionOutcome.FAVOURABLE)), moment=_MOMENT
    )
    ledger.record(
        _result("RKLB", decision=_decision(DecisionOutcome.NOT_FAVOURABLE)),
        moment=_MOMENT,
    )

    lines = _lines(path)
    assert [line["ticker"] for line in lines] == ["AAPL", "RKLB"]
    assert [line["outcome"] for line in lines] == ["favourable", "not_favourable"]


def test_a_line_carries_enough_to_replay_the_conclusion(tmp_path: Path) -> None:
    path = tmp_path / "decisions.jsonl"

    DecisionLedger(path=path).record(
        _result(decision=_decision(DecisionOutcome.NOT_FAVOURABLE)), moment=_MOMENT
    )

    line = _lines(path)[0]
    assert line["moment"] == _MOMENT.isoformat()
    assert line["conditions"] == {"terms": False, "currency": True}
    assert "bar" in line["reasons"]["terms"]
    assert line["evidence_references"] == ["AAPL.valuation.pe", "AAPL.risk.pe"]


def test_the_ledger_appends_rather_than_replacing(tmp_path: Path) -> None:
    # A ledger answers "what was concluded then", so nothing is ever overwritten: the
    # state file is written by replacement and this deliberately is not.
    path = tmp_path / "decisions.jsonl"
    ledger = DecisionLedger(path=path)

    for _ in range(3):
        ledger.record(
            _result(decision=_decision(DecisionOutcome.FAVOURABLE)), moment=_MOMENT
        )

    assert len(_lines(path)) == 3


def test_a_result_without_a_decision_writes_nothing(tmp_path: Path) -> None:
    # A row with no conclusion would say a judgement was made when none was.
    path = tmp_path / "decisions.jsonl"

    DecisionLedger(path=path).record(_result(decision=None), moment=_MOMENT)

    assert not path.exists() or _lines(path) == []


def test_a_ledger_that_cannot_be_written_does_not_raise(tmp_path: Path) -> None:
    # The pass has already produced a conclusion for a reader; the record of it must not
    # be able to take that away.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    DecisionLedger(path=blocker / "decisions.jsonl").record(
        _result(decision=_decision(DecisionOutcome.FAVOURABLE)), moment=_MOMENT
    )
