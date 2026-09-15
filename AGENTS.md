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
