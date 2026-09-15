# AIS

Adaptive Investment System — an evidence-based investment decision support system.

AIS organises market evidence into explainable investment decisions. It is built as a layered system in which every layer answers one question only, so that each decision can be traced back to the evidence behind it.

## Current Version

0.1.0

The version is declared once in `utils/constants.py`; `pyproject.toml` reads it from there.

## Folder Overview

| Folder | Holds |
| --- | --- |
| `app/` | Application entry |
| `config/` | Configuration management and logging setup |
| `contracts/` | Engine contracts between engines |
| `core/` | AIS Core Engine |
| `portfolio/` | Portfolio Engine |
| `data/` | Market data collection |
| `evidence/` | Evidence models and validation |
| `pipeline/` | Evidence pipeline |
| `evaluation/` | Core Engine subsystem: evaluation framework and evaluators |
| `dashboard/` | Dashboard generation |
| `communication/` | Notification system |
| `models/` | Shared domain models |
| `utils/` | Shared utilities: constants, exceptions, helpers |
| `logs/` | Runtime logs, written at run time |
| `tests/` | Unit and integration tests |
| `docs/` | Project documentation |

Authoritative folder responsibilities, layers, and dependency rules are defined in `docs/Architecture.md`. The table above is only an index and does not define them.

## Development Workflow

Requires Python 3.12 or newer.

1. Create and activate a virtual environment.
2. Install the project in editable mode: `pip install -e .`
3. Run the application: `python main.py`
4. Run the tests: `python -m pytest`
5. Check formatting and linting: `black .` and `ruff check .`

Runtime logs are written to `logs/`, configured by the environment variables documented in `config/config.py`.
