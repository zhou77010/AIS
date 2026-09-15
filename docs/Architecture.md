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
| `utils/` | Shared utilities. |
| `logs/` | Runtime logs. |
| `tests/` | Unit and integration tests. |
| `docs/` | Project documentation. |

### Folder Details

**`app/`** — Application entry. Starts the system and wires the layers together. Contains no business logic.

**`config/`** — Configuration management. Holds all runtime configuration, including credentials and file paths. No secrets or paths are hardcoded elsewhere.

**`contracts/`** — Engine contracts. The stable interfaces between engines, defined as typing protocols with no implementation.

**`core/`** — AIS Core Engine. Investment reasoning and decision generation. The Core Engine is the only layer that owns business logic; its framework subsystems live in sibling packages (see `evaluation/`).

**`portfolio/`** — Portfolio Engine. Allocation, position sizing, and portfolio management.

**`data/`** — Market data collection. Collects and normalizes raw market data and company information from external providers.

**`evidence/`** — Evidence models and validation. Defines and validates the evidence structures that the Core Engine consumes.

**`pipeline/`** — Evidence pipeline. Orchestrates evidence providers and assembles their items into an evidence collection.

**`evaluation/`** — Core Engine subsystem. The reusable evaluation framework (rule engine, category assembler, normalizer, base evaluator) plus the concrete category evaluators, starting with valuation.

**`dashboard/`** — Dashboard generation. Builds the dashboards and reports the Presentation Layer displays.

**`communication/`** — Notification system. Sends notifications such as WeChat messages, daily briefs, and event alerts.

**`models/`** — Shared domain models. Domain types used across more than one layer, so shared structures are defined once.

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

## Implementation Status

Implemented so far: shared domain models (`models/`), evidence domain models (`evidence/`), engine contracts (`contracts/`), a deterministic placeholder evidence pipeline (`pipeline/`), the reusable evaluation framework with its rule engine and category assembler (`evaluation/`), and the first concrete evaluator (`evaluation/valuation/`), alongside configuration, logging, shared constants, and the exception hierarchy.

The remaining category evaluators, the overall evaluation, scoring, recommendation, allocation, and data collection are not implemented yet.

---

End of Document
