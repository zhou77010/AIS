"""Which part of the market an asset belongs to.

A sector is not a measurement. It is the name of the part of the market an asset
competes in, and it exists here because AIS needs it to compare the right things: how
the market is doing is one question and how this asset's corner of it is doing is
another, and without the second the environment sentence is about an average nobody
holds.

**It is stated where a person can state it, and left absent where nobody has.** The
same rule the kind of an asset follows, and for the same reason: which sector an asset
is in decides which comparison AIS makes, and therefore which sentence it is able to
write. Guessing it — from the name, from a vendor's label, from anything but a person
saying so — would quietly change what AIS can say, and a changed ability to speak is
never visible in the output.

**AIS's vocabulary, not a vendor's.** Half a dozen providers classify the same company
into their own taxonomies with their own boundaries, and two of them disagree about
the same company. AIS states one set of names and one mapping to the instruments that
measure them, so a sentence means the same thing on every run.

**An asset with no sector gets no sector sentence.** An exchange-traded fund holds a
style rather than a sector, and a business nobody has classified is simply not
classified. Both are told nothing about their sector rather than something plausible.
"""

from __future__ import annotations

from enum import StrEnum


class Sector(StrEnum):
    """The part of the market an asset belongs to.

    The eleven names a market is conventionally divided into. They are the ones the
    sector instruments track, which is what makes them usable: a name with nothing
    measuring it would be a label AIS could not act on.
    """

    TECHNOLOGY = "technology"
    COMMUNICATION = "communication"
    CONSUMER_CYCLICAL = "consumer_cyclical"
    CONSUMER_DEFENSIVE = "consumer_defensive"
    ENERGY = "energy"
    FINANCIAL = "financial"
    HEALTHCARE = "healthcare"
    INDUSTRIALS = "industrials"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    UTILITIES = "utilities"
