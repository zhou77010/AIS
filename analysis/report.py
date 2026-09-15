"""AIS analysis report.

Renders one analysis result as plain text for console or log output. It uses no
formatting framework and prints nothing itself.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult


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
