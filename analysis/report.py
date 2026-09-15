"""AIS analysis report.

Renders one analysis result as plain text for console or log output. It uses no
formatting framework and prints nothing itself.

This module also owns the vocabulary that states where the numbers in a report
came from, so that every renderer labels the same run the same way.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult

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
    """Render the analysis result as a human readable report.

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
    lines.append(
        "  Evidence references: " + ", ".join(recommendation.evidence_references)
    )
    lines.append(f"  Investment thesis: {recommendation.investment_thesis}")
    return "\n".join(lines)


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
