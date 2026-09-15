"""AIS analysis report.

Renders one analysis result as plain text for console or log output. It uses no
formatting framework and prints nothing itself.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult

_NO_SOURCE_LABEL = "No market data source"
_UNAVAILABLE_LABEL = "Market data unavailable"
_LIVE_LABEL = "Live Market Data"


def describe_data_source(result: AnalysisResult) -> str:
    """Return a truthful one line label for the market data a run used.

    The label never claims live data when none was retrieved, so a notification
    can be trusted about where its numbers came from.

    Args:
        result: Analysis result to describe.

    Returns:
        Label naming the source and how much of it answered.
    """
    snapshot = result.market_data
    if snapshot is None:
        return _NO_SOURCE_LABEL
    if not snapshot.is_live:
        return f"{_UNAVAILABLE_LABEL} ({snapshot.source})"
    retrieved = len(snapshot.available_points)
    return (
        f"{_LIVE_LABEL} ({snapshot.source}; "
        f"{retrieved} of {len(snapshot.points)} metrics)"
    )


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
        f"  Market data: {describe_data_source(result)}",
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
