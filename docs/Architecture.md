# AIS Architecture

Version: 1.0.0

Project: AIS (Adaptive Investment System)

Status: Active

---

## Overview

AIS follows a **layered architecture**.

Each layer answers one question only and depends on the layers beneath it. Data flows upward as evidence and decisions; dependencies flow downward only. This keeps responsibilities separated, prevents duplicated business logic, and makes every decision explainable.

An upper layer may use a lower layer.

A lower layer must never know that an upper layer exists.

---

## Layers

Layers are listed from top to bottom.

### Presentation Layer

Responsible for displaying dashboards and reports.

This layer renders information for the human reader. It formats and presents what lower layers produced; it does not reason, evaluate, or decide.

↓

### Communication Layer

Responsible for notifications (WeChat, Daily Brief, Event Alerts).

This layer delivers messages outward through notification channels. It transports content produced by lower layers and does not create or reinterpret that content.

↓

### AIS Core Engine

Responsible for investment reasoning and decision generation.

This layer is the only place where business logic lives. It consumes validated evidence, forms categories, produces the overall assessment, derives the decision state, and generates the action.

The Core Engine is not a single package. It contains three subsystems:

- **Recommendation** — turns the overall assessment into the recommendation.
- **Overall Evaluation** — combines the category scores into the overall assessment.
- **Evaluation Framework** — executes evaluation rules and assembles category scores.

The Evaluation Framework is a **subsystem of the Core Engine**. It is not an independent architecture layer.

↓

### Portfolio Engine

Responsible for allocation, position sizing and portfolio management.

This layer decides how capital is allocated and sized. It consumes decisions as inputs and does not evaluate business quality.

↓

### Evidence Layer

Responsible for validating and organizing evidence.

This layer turns raw data into structured, validated evidence. It never produces Buy/Sell decisions.

↓

### Data Layer

Responsible for collecting raw market data and company information.

This layer acquires, normalizes, and stores raw data. It never generates investment recommendations.

↓

### External Providers

Sources the Data Layer collects from:

- Yahoo Finance
- SEC EDGAR
- FRED
- News APIs
- Future providers

External providers are outside the system boundary. Their availability, format, and rate limits are not under AIS control, so all provider access must be isolated behind the Data Layer.

---

## Layer Pipeline

```text
Presentation Layer
    ↓
Communication Layer
    ↓
AIS Core Engine
    ├── Recommendation
    ├── Overall Evaluation
    └── Evaluation Framework
    ↓
Portfolio Engine
    ↓
Evidence Layer
    ↓
Data Layer
    ↓
External Providers
```

---

## Project Folders

| Folder | Responsibility |
| --- | --- |
| `app/` | Application entry. |
| `analysis/` | Asset analysis: orchestrates one analysis flow for a single asset, and the reports projected from it. |
| `config/` | Configuration management. |
| `contracts/` | Engine contracts: the interfaces between engines. |
| `core/` | AIS Core Engine. |
| `portfolio/` | Portfolio Engine. |
| `data/` | Market data collection. |
| `evidence/` | Evidence models and validation. |
| `pipeline/` | Evidence pipeline: assembles evidence into a collection. |
| `evaluation/` | Core Engine subsystem: evaluation framework and category evaluators. |
| `dashboard/` | Dashboard generation. |
| `communication/` | Notification system. |
| `models/` | Shared domain models. |
| `state/` | What the runtime remembers between restarts. |
| `utils/` | Shared utilities. |
| `logs/` | Runtime logs. |
| `tests/` | Unit and integration tests. |
| `docs/` | Project documentation. |

### Folder Details

**`app/`** — Application entry. Starts the system and wires the layers together. Contains no business logic.

**`analysis/`** — Asset analysis. Orchestrates one complete analysis flow for a single asset: evidence, category score, overall assessment and recommendation. Contains no business logic. It also holds the two report models and their projections: the per-asset report, and the brief that covers the whole watch universe in one message. A projection chooses what a reader sees and never reaches a judgement; what the projections decide the same way — width, wrapping, and how small a movement is too small to mention — lives in `analysis/projection.py`, so that two renderers cannot describe one reading two ways.

**`config/`** — Configuration management. Holds all runtime configuration, including credentials and file paths. No secrets or paths are hardcoded elsewhere.

**`contracts/`** — Engine contracts. The stable interfaces between engines, defined as typing protocols with no implementation. A contract also owns the value objects exchanged across its boundary, because that is the only place both sides may depend on. `market_data_provider.py` carries one asset's measurements, `market_environment.py` carries the market's own, and `catalyst_event_provider.py` carries dated events: the environment is separate because its measurements belong to no asset, and a fact shared by every asset in a pass must not be fetched once per asset.

**`core/`** — AIS Core Engine. Investment reasoning and decision generation. The Core Engine is the only layer that owns business logic; its framework subsystems live in sibling packages (see `evaluation/`).

**`portfolio/`** — Portfolio Engine. Allocation, position sizing, and portfolio management.

**`data/`** — Market data collection. Collects and normalizes raw market data and company information from external providers.

**`evidence/`** — Evidence models and validation. Defines and validates the evidence structures that the Core Engine consumes.

**`pipeline/`** — Evidence pipeline. Orchestrates evidence providers and assembles their items into an evidence collection.

**`evaluation/`** — Core Engine subsystem. The reusable evaluation framework (rule engine, score normalizer, normalized score, category assembler, base evaluator) plus the concrete category evaluators, starting with valuation.

**`dashboard/`** — Dashboard generation. Builds the dashboards and reports the Presentation Layer displays.

**`communication/`** — Notification system. Sends notifications such as WeChat messages, daily briefs, and event alerts.

**`models/`** — Shared domain models. Domain types used across more than one layer, so shared structures are defined once.

**`state/`** — What the runtime remembers between restarts, written by the runtime rather than configured by a person. It records what AIS has done, never anything about the world: a fact about the world has an owner, and a copy of one in a file is a copy that will go stale.

**`utils/`** — Shared utilities. Small shared helpers without business meaning. Must not become a home for duplicated business logic.

**`logs/`** — Runtime logs. Output location for the project logging system.

**`tests/`** — Unit and integration tests. Tests for every public module.

**`docs/`** — Project documentation. Architecture and design documents, including this file.

---

## Architecture Rules

1. Upper layers may depend on lower layers.
2. Lower layers must never depend on upper layers.
3. Business logic belongs only inside the Core Engine.
4. Data Layer must never generate investment recommendations.
5. Evidence Layer must never generate Buy/Sell decisions.
6. Portfolio Engine must not evaluate business quality.
7. Architecture changes require explicit approval.
8. Scheduler is the only runtime owner. No loop may appear in `main.py`, the application, or the analyzer.
9. The report model is authoritative, and every renderer is a projection of it. No notifier, channel, or transport may build report content.
10. AIS depends only on the `MarketDataProvider` contract. Only the Data Layer may name a market data vendor, and no component outside it may depend on a vendor specific field.
11. A component must not take over another component's responsibility. The owners are listed under Component Boundaries.

---

## Component Boundaries

Each component answers one question, and no component may take over another's. These boundaries were frozen by the architecture review.

| Component | Owns | Must never |
| --- | --- | --- |
| Scheduler (`app/scheduler.py`) | The runtime. It decides when work runs. | Hold analysis, delivery, or presentation logic. |
| Analyzer (`analysis/analyzer.py`) | Orchestration. It runs the stages in order. | Judge, evaluate, or render. |
| Evaluators (`evaluation/`) | Business judgement. They turn evidence into category scores. | Retrieve data, deliver messages, or assemble a report. |
| Pipeline (`pipeline/`) | Evidence transformation. It turns retrieved data into evidence. | Evaluate, score, or decide. |
| Communication (`communication/`) | Delivery. It carries a message outward and reports whether it arrived. | Build or reinterpret report content. |
| Renderer (`analysis/report.py`, `analysis/mobile_report.py`, `analysis/brief_report.py`) | Presentation. They turn a model into text. | Send anything, or read a vendor. |
| Transport (`data/http.py`, the notifier internals) | The network. It moves bytes. | Know what a report is. |

The rules these boundaries produce:

- **Report Model → Renderer → Transport.** A report is rendered once, by a renderer, and every transport carries that same text. A notifier only ever receives rendered text; it cannot receive a recommendation, an assessment, or any other model.
- **One model per document, and every renderer is a projection of it.** AIS renders two documents: a report about one asset, and a brief over the watch universe. Each has exactly one model, and a channel that wants different content gets a projection of that model rather than a second one of its own. A document is added by adding a model and saying so here; it is never added by a channel assembling its own content.
- **One provider contract per kind of fact.** The Data Layer implements `MarketDataProvider` for measurements of an asset, `CatalystEventProvider` for dated events and `EnvironmentProvider` for the market's own measurements, and exposes a factory for each. Nothing outside the Data Layer names a vendor, and no vendor field crosses the boundary, so a new source plugs into an existing interface rather than into the components that read it.
- **A provider returns facts; AIS classifies them.** A catalyst event provider states what kind of event it is and when it falls. Which layer of the investment case that bears on is read from one table in `models/catalyst_event.py`. A provider that decided it would be making a judgement, and this keeps a new source from changing how AIS reads the sources it already has.
- **One runtime.** The scheduler owns the loop. Everything above it is called, and never waits.

These boundaries are enforced structurally by `tests/test_architecture_boundaries.py`. A boundary that is only written down is a wish; that test is what makes it true.

---

## Business Rule Pipeline

The layer order exists to protect one pipeline:

Indicators produce evidence.

Evidence supports Categories.

Categories support Overall Assessment.

Overall Assessment generates Decision State.

Decision State generates Action.

This pipeline must never be bypassed. Any change to it is an architecture change and requires explicit approval.

---

## Scoring Pipeline

Inside the Core Engine, evaluation follows one pipeline:

```text
RuleResult
    ↓
ScoreNormalizer
    ↓
NormalizedScore
    ↓
CategoryAssembler
    ↓
CategoryScore
```

A rule reports a raw measurement. The score normalizer converts that measurement into a `NormalizedScore` on the AIS standard scale. The category assembler builds the `CategoryScore` from normalized scores only: raw measurements are never aggregated into an investment score.

Thresholds, weighting, and industry adjustment are defined by the Constitution. They are not part of this framework.

---

## Evidence Traceability Rule

- Evidence is a first-class object.
- Structured EvidenceReference objects are owned exclusively by the Evidence Layer.
- The Core Engine carries only lightweight evidence identifiers (`tuple[str, ...]`).
- Evidence references must never be silently discarded while a decision is propagated through the analysis pipeline.
- Intermediate models should avoid redundant copies unless required by downstream consumers.

---

## Implementation Status

Implemented so far: shared domain models (`models/`), evidence domain models (`evidence/`), engine contracts (`contracts/`), a deterministic placeholder evidence pipeline (`pipeline/`), the reusable evaluation framework (`evaluation/`), the first complete vertical slice (`core/`) that runs evidence into a category score, an overall assessment and a recommendation, the asset analysis flow (`analysis/`) that orchestrates that slice for a single asset, live market data (`data/`), and the notification channels (`communication/`), alongside configuration, logging, shared constants, and the exception hierarchy.

Live market data is retrieved by a provider that holds every vendor detail, so no other layer knows which source is used. A metric a source cannot provide is recorded as evidence that states why it is missing, and the rule that needs it fails; no value is ever invented to fill a gap. Because a discounted cash flow fair value is the output of a valuation model rather than a published market datum, it is reported as unavailable by nature and no placeholder number stands in for it.

The overall evaluation, the recommendation, the score normalizer and the analysis flow remain placeholders: live measurements now feed a placeholder scale, so the scores they produce are not yet meaningful. The remaining category evaluators, the AIS standard scale, and allocation are not implemented yet.

### Architecture review

Phases 1 to 3 of the architecture review are complete and the architecture is approved. Framework work is now in maintenance mode: no subsystem is to be rewritten, and no framework expansion is to be done before methodology work begins.

The boundaries above are frozen. The designs frozen with them are the domain models, the rule engine, the category assembler, the evidence pipeline, the analyzer, the scheduler, the provider abstraction, the renderer to transport separation, and the configuration strategy.

### Deferred architecture work

Recorded so the decisions are not lost, and explicitly **not** scheduled. Each is worth doing only when its trigger appears; until then the current, simpler design is the correct one.

| # | Deferred | Trigger |
| --- | --- | --- |
| B1 | `NotificationPolicy` | Notification rules become more complex than "the recommendation changed". `ChangeDetector` is sufficient today. |
| B2 | A `Renderer` interface | The number of renderers exceeds two. Today the renderers are plain functions, and an interface would be ceremony. |
| B3 | A trigger strategy | The runtime gains trigger types beyond a fixed interval. The interval scheduler is sufficient today. |
| B4 | Dependency injection for the analyzer | The evaluator count grows enough that constructor wiring stops being readable. Constructor wiring is acceptable today. |
| B5 | A health status endpoint | Someone needs to observe the system remotely. It should report last run, last success, last notification, provider, and scheduler state. Not implemented. |

### Stage 2 — Investment Intelligence

The architecture review is closed. Architecture is no longer the bottleneck, and framework expansion is not to be done unless an architectural defect is discovered. The primary objective is no longer the quality of the software structure but the quality of the investment decisions it produces.

Work proceeds in this order:

1. Constitution — vocabulary and semantics only. It defines what each term means, not how it is computed. It is built up incrementally rather than specified in full up front.
2. Risk Evaluator
3. AIS Standard Score
4. Decision Thresholds
5. Remaining Category Evaluators
6. Portfolio Intelligence

Two consequences of this order are deliberate and worth stating.

**Semantics before scale.** The Constitution lands before the standard score, so the Risk evaluator is built while the scale is still undefined. That is intentional: a measurement whose meaning is settled can be normalized later, whereas a measurement whose meaning is unsettled cannot. Risk will therefore report raw measurements on a placeholder scale, exactly as Valuation does today, and the report already says so.

**Risk before the score it feeds.** Risk is evaluated before the standard score exists, which means the overall score will briefly be the mean of two categories on an undefined scale. Adding a second evaluated category makes the average look more authoritative without making it more meaningful. The report must keep stating that the scale is undefined until the standard score lands.

Every category currently renders `NOT EVALUATED` except Valuation. Turning those into `EVALUATED` is the point of this stage, not making the report nicer.

---

End of Document
