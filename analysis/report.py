"""AIS analysis report.

Renders one analysis result as plain text for console or log output. It uses no
formatting framework and prints nothing itself.

This is the **expanded report**: the daily report is a projection of the same
result, and everything the phone leaves out is kept here rather than dropped.
Every sentence the insight layer wrote, the whole event calendar, the opportunity
conditions and the model's own names for what was not looked at are all in this
output.

This module also owns the vocabulary that states where the numbers in a report
came from, so that every renderer labels the same run the same way.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from analysis.labels import UNASSESSED_ITEMS

LIVE_DATA_LABEL = "LIVE MARKET DATA"
PLACEHOLDER_DATA_LABEL = "PLACEHOLDER DATA"
NO_DATA_LABEL = "NO MARKET DATA"


def data_quality_label(result: AnalysisResult) -> str:
    """Return the one label stating where the numbers of a run came from.

    The label never claims live data when none was retrieved, so a reader is
    never left to guess whether a figure was measured or defaulted.

    Args:
        result: Analysis result to classify.

    Returns:
        One of :data:`LIVE_DATA_LABEL`, :data:`PLACEHOLDER_DATA_LABEL` or
        :data:`NO_DATA_LABEL`.
    """
    snapshot = result.market_data
    if snapshot is None:
        return PLACEHOLDER_DATA_LABEL
    if not snapshot.is_live:
        return NO_DATA_LABEL
    return LIVE_DATA_LABEL


def describe_data_source(result: AnalysisResult) -> str:
    """Return a detailed one line description of the data behind a run.

    Args:
        result: Analysis result to describe.

    Returns:
        Description naming the source and how much of it answered.
    """
    snapshot = result.market_data
    if snapshot is None:
        return "no market data source was connected"
    retrieved = len(snapshot.available_points)
    return f"{snapshot.source}, {retrieved} of {len(snapshot.points)} inputs retrieved"


def generate_report(result: AnalysisResult) -> str:
    """Render the analysis result as the expanded report.

    This is the layer the daily report projects from. Everything the phone report
    leaves out is here: every sentence the insight layer wrote, the whole event
    calendar, the opportunity conditions as they were decided, and the model's own
    name for each thing that was not looked at. Nothing is dropped from AIS when
    it is dropped from a phone screen; it moves here.

    Args:
        result: Analysis result to render.

    Returns:
        Report text, one fact per line.
    """
    asset = result.asset
    assessment = result.assessment
    recommendation = result.recommendation

    lines = [
        "AIS analysis report",
        f"  Asset: {asset.ticker} ({asset.name}) - {asset.exchange}, {asset.currency}",
        f"  Market data: {data_quality_label(result)}"
        f" ({describe_data_source(result)})",
        *data_provenance_lines(result),
        f"  Overall score: {assessment.overall_score}",
        f"  Grade: {assessment.grade}",
        f"  Decision state: {recommendation.decision_state.value}",
        f"  Confidence: {recommendation.confidence}",
        "  Category scores:",
    ]
    for category_score in assessment.category_scores:
        lines.append(
            f"    - {category_score.category.value}: {category_score.score} "
            f"(confidence {category_score.confidence})"
        )
        lines.append(f"      summary: {category_score.summary}")
    lines.extend(_insight_lines(result))
    lines.extend(_opportunity_lines(result))
    lines.extend(_event_lines(result))
    lines.extend(_environment_lines(result))
    lines.extend(_gap_lines(result))
    lines.append(
        "  Evidence references: " + ", ".join(recommendation.evidence_references)
    )
    lines.append(f"  Investment thesis: {recommendation.investment_thesis}")
    return "\n".join(lines)


def _insight_lines(result: AnalysisResult) -> list[str]:
    """Return every sentence the insight layer wrote, with what it stands on."""
    lines = ["  Insights:"]
    for insight in result.insights:
        lines.append(f"    {insight.category.value}:")
        for entry in insight.lines:
            lines.append(f"      - {entry.text}")
            lines.append(f"        from: {', '.join(entry.references)}")
    return lines


def _opportunity_lines(result: AnalysisResult) -> list[str]:
    """Return the opportunity judgement and every condition behind it."""
    opportunity = result.opportunity
    if opportunity is None:
        return []
    lines = ["  Opportunity:"]
    grade = "none" if opportunity.grade is None else str(opportunity.grade)
    lines.append(f"    grade: {grade}")
    lines.append(f"    summary: {opportunity.summary}")
    for entry in opportunity.conditions:
        state = (
            "unknown"
            if entry.satisfied is None
            else ("satisfied" if entry.satisfied else "not satisfied")
        )
        lines.append(f"    - {entry.condition.value}: {state} (grade {entry.grade})")
    return lines


def _event_lines(result: AnalysisResult) -> list[str]:
    """Return every dated event the run was built on, in date order."""
    if not result.events:
        return []
    lines = ["  Catalyst events:"]
    for event in result.events:
        confirmation = "confirmed" if event.confirmed else "unconfirmed"
        lines.append(
            f"    - {event.occurs_on} {event.kind.value} ({event.scope.value}, "
            f"{event.priority.value}, {confirmation}) {event.description} "
            f"[{event.source}]"
        )
    return lines


def _environment_lines(result: AnalysisResult) -> list[str]:
    """Return every measurement of the environment the run was judged in.

    The environment is the one part of a run that is not about the asset, so it is
    written out once, in the document that keeps everything: what the market was
    doing, and for each measurement either its value or the reason it is missing. A
    reader asking why a sentence about rates was written can find the rate here.
    """
    environment = result.environment
    if environment is None:
        return []
    lines = [f"  Environment ({environment.source}):"]
    lines.extend(
        f"    - {point.metric.value}: {point.reason}" for point in environment.points
    )
    return lines


def _gap_lines(result: AnalysisResult) -> list[str]:
    """Return what was not looked at, named the way the model names it.

    The daily report names whole categories and no more. The dimension-level and
    metric-level detail is a reader's reference rather than their reading, so it
    is kept here.
    """
    snapshot = result.market_data
    lines = ["  Not assessed:"]
    for category_score in result.assessment.category_scores:
        if not category_score.evidence_references:
            lines.append(f"    - {category_score.category.value}: no judgement")
    for category, items in UNASSESSED_ITEMS.items():
        for item in items:
            lines.append(f"    - {category.value}: {item}")
    if snapshot is not None:
        for point in snapshot.missing_points:
            lines.append(f"    - {point.metric.value}: {point.reason}")
    return lines


def data_provenance_lines(result: AnalysisResult) -> list[str]:
    """Return one line per market metric, stating its value or why it is missing.

    Args:
        result: Analysis result to describe.

    Returns:
        Provenance lines, empty when no market data source was consulted.
    """
    snapshot = result.market_data
    if snapshot is None:
        return []
    return [f"    - {point.metric.value}: {point.reason}" for point in snapshot.points]
