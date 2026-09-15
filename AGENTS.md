# AGENTS.md

Version: 1.1.0

Project: AIS (Adaptive Investment System)

Status: Active

---

# Purpose

This document defines the engineering rules that every AI coding agent must follow.

AIS is an evidence-based investment decision support system.

The responsibility of coding agents is to implement the architecture faithfully.

Coding agents must never redesign AIS without explicit approval.

`docs/Architecture.md` is the single authoritative source for project architecture, folder organization, and dependency rules.

---

# Highest Priority

The AIS Constitution is the highest authority.

If implementation conflicts with the Constitution,

the Constitution always wins.

---

# Single Source of Truth

Every architectural definition, business rule, and project structure should have exactly one authoritative source.

Duplication across documents or modules is prohibited to prevent inconsistency.

---

# AI Responsibilities

AI coding agents are responsible for:

- Writing code
- Refactoring code
- Improving readability
- Writing tests
- Fixing bugs
- Updating documentation

AI coding agents are NOT responsible for:

- Changing investment philosophy
- Creating new scoring methods
- Modifying business logic
- Inventing new indicators
- Redesigning architecture

Those decisions require explicit approval.

---

# Core Engineering Principles

## 1. Single Responsibility

Every module answers one question only.

Avoid mixed responsibilities.

---

## 2. No Double Counting

Never duplicate business logic.

Shared functionality belongs in shared modules.

---

## 3. Simplicity First

Prefer the simplest implementation that satisfies the requirement.

Avoid unnecessary abstraction.

---

## 4. Readability First

Code should be understandable before being clever.

---

## 5. Explicit Over Implicit

Avoid hidden behavior.

Prefer explicit data flow.

---

# Architecture Rules

Evaluators must never manually construct CategoryScore.

CategoryScore must only be produced through CategoryAssembler.

---

# Component Boundaries

The architecture review froze these owners. Each component answers one question, and no component may take over another's.

| Component | Owns | Must never |
| --- | --- | --- |
| Scheduler (`app/scheduler.py`) | The runtime. It decides when work runs. | Hold analysis, delivery, or presentation logic. |
| Analyzer (`analysis/analyzer.py`) | Orchestration. It runs the stages in order. | Judge, evaluate, or render. |
| Evaluators (`evaluation/`) | Business judgement. They turn evidence into category scores. | Retrieve data, deliver messages, or assemble a report. |
| Pipeline (`pipeline/`) | Evidence transformation. It turns retrieved data into evidence. | Evaluate, score, or decide. |
| Communication (`communication/`) | Delivery. It carries a message outward. | Build or reinterpret report content. |
| Renderer (`analysis/report.py`, `analysis/mobile_report.py`) | Presentation. They turn a result into text. | Send anything, or read a vendor. |
| Transport (`data/http.py`, the notifier internals) | The network. It moves bytes. | Know what a report is. |

Rules an agent must never break:

1. **Report Model → Renderer → Transport.** A report is rendered once and every transport carries that same text. A notifier only ever receives rendered text; never a recommendation, an assessment, or any other model.
2. **Every renderer renders the same report model.** No channel gets its own report structure.
3. **Only the Data Layer names a market data vendor.** Everything else depends on the `MarketDataProvider` contract, and never on a vendor specific field. Add a provider through `data/market_data.py`.
4. **Scheduler is the only runtime owner.** No loop and no waiting may appear in `main.py`, the application, or the analyzer.

These are enforced by `tests/test_architecture_boundaries.py`. If a change makes that test fail, the change is wrong, not the test.

---

# Frozen Designs

These have passed architecture review and must not be redesigned without explicit approval:

Domain Models · Rule Engine · CategoryAssembler · Evidence Pipeline · Analyzer · Scheduler · Provider abstraction · Renderer to Transport separation · Configuration strategy

Architecture is approved and framework work is in maintenance mode. Prefer methodology work over structural work, and report an architecture defect instead of fixing it silently.

---

# Constitution Rules

The following concepts must never be changed without approval.

- Evidence Before Opinion
- Simplicity Before Complexity
- Explain Every Decision
- Manage Risk Before Return
- Consistency Before Prediction
- Single Responsibility
- No Double Counting

---

# Coding Style

Python Version

3.12+

Use

- Type Hints
- Dataclasses when appropriate
- Enum for constant states
- pathlib instead of os.path

Formatting

- Black
- Ruff

Maximum Function Length

50 lines preferred.

Maximum Module Length

300 lines preferred.

---

# Testing

Every public module should include tests.

Avoid introducing untested business logic.

---

# Logging

Never print directly.

Use the project logging system.

---

# Configuration

Never hardcode:

- API Keys
- Secrets
- Tokens
- File Paths

Always use configuration.

---

# Git Rules

One logical feature per commit.

Avoid unrelated modifications.

Do not rename files unless necessary.

---

# Sprint Scope Rule

Only modify files that are necessary to satisfy the current Sprint objectives.

Avoid unrelated refactoring.

If unrelated issues are discovered, report them instead of fixing them automatically.

---

# Before Finishing

Before completing any task, verify:

- Architecture remains unchanged.
- Business logic is not duplicated.
- Imports remain clean.
- Tests pass.
- Documentation updated if necessary.

---

# If Uncertain

Do not guess.

Leave TODO comments.

Explain assumptions.

Request clarification.

Wrong architecture is worse than incomplete implementation.

---

End of Document
