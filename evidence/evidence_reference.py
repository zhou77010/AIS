"""AIS evidence reference domain model.

An evidence reference points from an assessment back to the evidence items it
rests on. It carries references only.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvidenceReference:
    """Reference from an assessment back to one or more evidence items.

    Attributes:
        evidence_ids: Identifiers of the evidence items being referenced.
    """

    evidence_ids: tuple[str, ...]
