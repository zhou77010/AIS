# Evidence Survey

Status: **Non-normative.** An implementation reference.

This document records what market data AIS can currently retrieve, measured
rather than assumed. It is a statement about the world, not about AIS.

---

## What this document is not

**It does not define risk, or anything else.**

The dependency in AIS runs in one direction only:

```
Investment Philosophy
  → Risk Semantics
    → Evidence
      → Data Sources
```

It never runs the other way. A measurement may become evidence *for* a semantic
dimension; it must never become the *definition* of one. A field listed below is
a candidate source of evidence, and nothing more.

Concretely: this document is allowed to say that a field exists. It is not
allowed to say what that field means for a judgement. That mapping is made
top-down, at implementation time, from the semantics the Constitution fixes —
never upward from whatever happens to be available.

Some of the fields below may never be used by AIS at all. That is a normal
outcome of a survey, not an omission.

---

## Method

The survey queries the market data source currently behind the Data layer's
provider, for the assets AIS is configured to watch, and records whether each
field carries a usable finite number.

- Modules requested: `summaryDetail`, `defaultKeyStatistics`, `financialData`.
- Field names are spelled exactly as the source spells them, because an
  implementation needs the real key, not a prettier one.
- A field counts as available only when it holds a finite number. A null, an
  absent key and a non-numeric placeholder all count as unavailable.
- The survey is repeatable: re-run the same query to refresh it. It is a
  snapshot, and market data changes.

Regenerating this table is a matter of repeating the query above. Nothing in it
is hand-maintained.

## Availability

| Field | AAPL | CGDV | APP | BABA | HSBC | MNST | RKLB |
| --- | --- | --- | --- | --- | --- | --- | --- |
| beta | yes | - | yes | yes | yes | yes | yes |
| fiftyTwoWeekHigh | yes | yes | yes | yes | yes | yes | yes |
| fiftyTwoWeekLow | yes | yes | yes | yes | yes | yes | yes |
| marketCap | yes | - | yes | yes | yes | yes | yes |
| averageVolume | yes | yes | yes | yes | yes | yes | yes |
| trailingPE | yes | yes | yes | yes | yes | yes | - |
| forwardPE | yes | - | yes | yes | yes | yes | yes |
| payoutRatio | yes | - | yes | yes | yes | yes | yes |
| 52WeekChange | yes | - | yes | yes | yes | yes | yes |
| pegRatio | yes | - | yes | yes | yes | yes | - |
| enterpriseToEbitda | yes | - | yes | yes | - | yes | yes |
| priceToBook | yes | - | yes | yes | yes | yes | yes |
| bookValue | yes | - | yes | yes | yes | yes | yes |
| trailingEps | yes | - | yes | yes | yes | yes | yes |
| forwardEps | yes | - | yes | yes | yes | yes | yes |
| netIncomeToCommon | yes | - | yes | yes | yes | yes | yes |
| sharesShort | yes | - | yes | yes | yes | yes | yes |
| shortPercentOfFloat | yes | - | yes | yes | - | yes | yes |
| shortRatio | yes | - | yes | yes | yes | yes | yes |
| floatShares | yes | - | yes | yes | yes | yes | yes |
| heldPercentInsiders | yes | - | yes | yes | yes | yes | yes |
| heldPercentInstitutions | yes | - | yes | yes | yes | yes | yes |
| earningsQuarterlyGrowth | yes | - | yes | yes | yes | yes | - |
| debtToEquity | yes | - | yes | yes | - | yes | yes |
| currentRatio | yes | - | yes | yes | - | yes | yes |
| quickRatio | yes | - | yes | yes | - | yes | yes |
| totalDebt | yes | - | yes | yes | yes | yes | yes |
| totalCash | yes | - | yes | yes | yes | yes | yes |
| freeCashflow | yes | - | yes | yes | - | yes | yes |
| operatingCashflow | yes | - | yes | yes | yes | yes | yes |
| ebitda | yes | - | yes | yes | - | yes | yes |
| revenueGrowth | yes | - | yes | yes | yes | yes | yes |
| earningsGrowth | yes | - | yes | yes | - | yes | - |
| profitMargins | yes | - | yes | yes | yes | yes | yes |
| grossMargins | yes | - | yes | yes | yes | yes | yes |
| operatingMargins | yes | - | yes | yes | yes | yes | yes |
| returnOnEquity | yes | - | yes | yes | yes | yes | yes |
| returnOnAssets | yes | - | yes | yes | yes | yes | yes |

Fields available per asset:

| Asset | Available |
| --- | --- |
| AAPL | 38 / 38 |
| APP | 38 / 38 |
| BABA | 38 / 38 |
| MNST | 38 / 38 |
| RKLB | 34 / 38 |
| HSBC | 30 / 38 |
| CGDV | **4 / 38** |

## What the gaps are, and why they matter

The gaps are not random. Each has a reason, and the reasons are different kinds
of thing.

**CGDV is an exchange-traded fund, not a company.** It has no earnings, no
balance sheet and no cash flow of its own, so almost every field that describes
a business is absent. Only price-derived fields exist. Any dimension that
depends on a company's finances can never be assessed for it, and that is a
permanent property of the asset class, not a data outage.

**HSBC is a bank.** Banks do not report a current ratio, a quick ratio, EBITDA
or a conventional free cash flow, because those concepts do not apply to a
balance-sheet business. Their absence is correct, not missing data. An
implementation that treats it as a gap will report a defect where there is none.

**RKLB is loss-making.** It has no trailing P/E, no PEG and no earnings growth,
because there are no positive earnings to divide by. A negative or absent
earnings figure is information, and a rule that requires a positive denominator
will fail here for a reason that is itself informative.

The general lesson, and the reason this survey is worth keeping: **the same
field can be missing for three entirely different reasons** — the concept does
not apply, the asset class does not have it, or the value does not exist. AIS
already distinguishes these in its absence vocabulary. This survey is the
evidence that it needs to.

---

End of Document
