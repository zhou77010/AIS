"""Turning an opportunity judgement into the sentence an investor reads.

A report is not a table of numbers, and it is not a list of conditions either. The
opportunity judgement is a set of named conditions that hold or do not; a reader
wants the sentence those conditions amount to.

**What is no longer here.** This module used to translate measurements into
sentences about trends, holdings and the calendar. The insight layer does that now,
and it does it from the same bands the grade is read from. Keeping a second set of
sentences here meant two places decided what a measurement meant, which is how the
report came to describe the same number two ways.

What remains is the one sentence nothing else owns: what the opportunity conditions
amount to, and what the report's headline says about them.
"""

from __future__ import annotations

from analysis.analysis_result import AnalysisResult
from analysis.labels import opportunity_condition_label, opportunity_headline
from contracts.market_data_provider import MarketDataPoint
from models.category import Category
from models.opportunity_assessment import OpportunityAssessment


def measurements_of(
    result: AnalysisResult, category: Category
) -> list[MarketDataPoint]:
    """Return the retrieved measurements that bear on one category.

    A measurement may support more than one category, so a category's readings are
    the ones whose categories include it, not only the ones filed under it.
    """
    snapshot = result.market_data
    if snapshot is None:
        return []
    return [
        point
        for point in snapshot.available_points
        if category in point.metric.categories
    ]


def opportunity_sentence(assessment: OpportunityAssessment) -> str:
    """Return why this is, or is not, one of the better opportunities today.

    The sentence names the conditions that hold and the conditions that do not,
    which is the whole of what the judgement contains: there is no combined score
    behind it to explain, because none was computed. A condition that could not be
    judged is named by the report rather than written into the sentence, so that a
    question which was never asked is never read as one that was answered.

    Args:
        assessment: Opportunity judgement to write.

    Returns:
        A sentence, always one: an opportunity that could not be judged at all is
        itself something a reader is owed.
    """
    held = [
        opportunity_condition_label(result.condition, True)
        for result in assessment.satisfied
    ]
    missing = [
        opportunity_condition_label(result.condition, False)
        for result in assessment.unsatisfied
    ]

    if assessment.grade is None:
        return "尚无可用的类别判断，机会条件无法评估。"

    lead = opportunity_headline(assessment.grade)
    if held and missing:
        return f"{lead}：{'、'.join(held)}；但{'、'.join(missing)}。"
    if held:
        return f"{lead}：{'、'.join(held)}。"
    return f"{lead}：{'、'.join(missing)}。"
