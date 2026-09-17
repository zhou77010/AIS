"""Tests for the expanded report.

The daily report is a projection, and everything it leaves out has to be
somewhere. This module is the check that the projection is a projection and not
a deletion: every sentence the insight layer wrote, the whole calendar, the
opportunity conditions and the model's own names for what was not looked at are
all in the expanded report, which is what is written to the log.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from test_mobile_report import _event, _render, _result  # noqa: E402

from analysis.report import generate_report  # noqa: E402
from models.catalyst_event import CatalystEventKind  # noqa: E402
from models.category import Category  # noqa: E402


def _expanded(result=None) -> str:
    return generate_report(_result() if result is None else result)


def test_every_insight_sentence_is_kept() -> None:
    result = _result()
    expanded = _expanded(result)

    for insight in result.insights:
        for line in insight.lines:
            assert line.text in expanded, line.text


def test_every_insight_line_names_what_it_stands_on() -> None:
    expanded = _expanded()

    assert "from: NVDA.market_data." in expanded


def test_the_whole_calendar_is_kept() -> None:
    events = (
        _event(CatalystEventKind.EARNINGS, 43),
        _event(CatalystEventKind.FOMC, 3),
        _event(CatalystEventKind.LAUNCH_WINDOW, 60, confirmed=False),
    )

    expanded = _expanded(_result(events=events))

    assert "Catalyst events:" in expanded
    for event in events:
        assert str(event.occurs_on) in expanded
        assert event.kind.value in expanded
    assert "unconfirmed" in expanded


def test_the_event_priority_and_layer_are_kept() -> None:
    expanded = _expanded(_result(events=(_event(CatalystEventKind.EARNINGS, 43),)))

    assert "company" in expanded
    assert "primary" in expanded


def test_every_opportunity_condition_is_kept_with_its_state() -> None:
    result = _result(grades={Category.CATALYST: None})

    expanded = _expanded(result)

    assert "Opportunity:" in expanded
    assert "catalyst: unknown (grade None)" in expanded
    assert "valuation: satisfied (grade 5)" in expanded


def test_the_models_own_gap_names_are_kept() -> None:
    expanded = _expanded(_result((Category.MARKET,)))

    assert "Not assessed:" in expanded
    assert "业务风险" in expanded
    assert "长期风险" in expanded


def test_the_expanded_report_keeps_what_the_phone_leaves_out() -> None:
    # The two projections are of one model, and the difference between them is
    # exactly what this round moved rather than removed.
    result = _result(events=(_event(CatalystEventKind.EARNINGS, 43),))
    phone = _render(result)
    expanded = _expanded(result)

    assert "业务风险" not in phone
    assert "业务风险" in expanded
    assert "市盈率" not in phone
    assert "trend_ma20_gap" in expanded


def test_the_expanded_report_still_states_the_scores_and_the_thesis() -> None:
    expanded = _expanded()

    assert "Overall score:" in expanded
    assert "Investment thesis:" in expanded
    assert "Evidence references:" in expanded


def test_the_expanded_report_is_deterministic() -> None:
    result = _result(events=(_event(CatalystEventKind.EARNINGS, 43),))

    assert _expanded(result) == _expanded(result)


def test_an_asset_with_nothing_known_still_produces_an_expanded_report() -> None:
    expanded = _expanded(replace(_result((Category.MARKET,)), market_data=None))

    assert "AIS analysis report" in expanded
    assert "Not assessed:" in expanded
