"""Architecture boundary tests.

The architecture review froze a set of boundaries. A boundary that is only
written down is a wish, so these tests check the boundaries structurally and
fail when one is crossed.

They are deliberately blunt: they read source text and import graphs rather than
reasoning about behaviour, because what they guard is structure.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PACKAGES = (
    "analysis",
    "app",
    "communication",
    "config",
    "contracts",
    "core",
    "dashboard",
    "data",
    "evidence",
    "evaluation",
    "models",
    "pipeline",
    "portfolio",
    "utils",
)

# The market data vendor is a Data layer concern. Every other component depends
# on the MarketDataProvider contract and never names the vendor.
VENDOR_MARKERS = ("yahoo",)
VENDOR_OWNER = "data"

# The runtime loop lives in the scheduler and nowhere else.
LOOP_OWNER = "app/scheduler.py"
MOUNTED_RUNTIME_MODULES = ("main.py", "app/application.py", "analysis/analyzer.py")


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _sources(*packages: str) -> list[Path]:
    """Return every Python source file under the given packages."""
    files: list[Path] = []
    for package in packages:
        files.extend(
            path
            for path in (PROJECT_ROOT / package).rglob("*.py")
            if "__pycache__" not in path.parts
        )
    return sorted(files)


def _imported_modules(path: Path) -> set[str]:
    """Return every module name imported by a source file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def _notifier_modules() -> list[Path]:
    """Return the communication modules that define a notification channel.

    A module qualifies when it defines a class with a ``send`` method, which is
    what the notification contract requires. A demonstration module that only
    exercises a channel does not qualify: the renderer boundary binds the
    channels themselves.
    """
    notifiers: list[Path] = []
    for path in _sources("communication"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and any(
                isinstance(member, ast.FunctionDef) and member.name == "send"
                for member in node.body
            ):
                notifiers.append(path)
                break
    return notifiers


# --------------------------------------------------------------------------
# A3 - the market data provider boundary
# --------------------------------------------------------------------------


def test_only_the_data_layer_names_the_market_data_vendor() -> None:
    offenders = [
        _relative(path)
        for path in _sources(*PACKAGES)
        if path.relative_to(PROJECT_ROOT).parts[0] != VENDOR_OWNER
        and any(
            marker in path.read_text(encoding="utf-8").lower()
            for marker in VENDOR_MARKERS
        )
    ]

    assert offenders == [], (
        "only the Data layer may name a market data vendor; "
        f"these files cross the provider boundary: {offenders}"
    )


def test_the_data_layer_exposes_a_provider_factory() -> None:
    from data.market_data import build_market_data_provider

    provider = build_market_data_provider()

    assert callable(getattr(provider, "fetch", None))


# --------------------------------------------------------------------------
# A4 - the scheduler boundary
# --------------------------------------------------------------------------


def test_only_the_scheduler_owns_the_runtime_loop() -> None:
    owners = [
        _relative(path)
        for path in _sources(*PACKAGES)
        if "while true" in path.read_text(encoding="utf-8").lower()
    ]

    assert owners == [LOOP_OWNER]


def test_the_mounted_runtime_modules_contain_no_loop() -> None:
    for name in MOUNTED_RUNTIME_MODULES:
        text = (PROJECT_ROOT / name).read_text(encoding="utf-8")

        assert "while " not in text, f"{name} must not run a loop"
        assert "time.sleep" not in text, f"{name} must not wait; the scheduler does"


def test_only_the_scheduler_imports_the_waiting_module() -> None:
    importers = [
        _relative(path)
        for path in _sources(*PACKAGES)
        if "time" in _imported_modules(path)
    ]

    assert importers == [LOOP_OWNER]


# --------------------------------------------------------------------------
# A2 - the renderer and transport boundary
# --------------------------------------------------------------------------


def test_no_notifier_imports_a_renderer() -> None:
    offenders: list[str] = []
    for path in _notifier_modules():
        renderers = {
            module
            for module in _imported_modules(path)
            if module in {"analysis.report", "analysis.mobile_report"}
        }
        if renderers:
            offenders.append(f"{_relative(path)} imports {sorted(renderers)}")

    assert (
        offenders == []
    ), "a notifier transports a report, it does not build one: " + "; ".join(offenders)


def test_every_notifier_send_takes_only_rendered_text() -> None:
    offenders: list[str] = []
    for path in _notifier_modules():
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.FunctionDef) or node.name != "send":
                continue
            parameters = [
                argument
                for argument in (*node.args.args, *node.args.kwonlyargs)
                if argument.arg != "self"
            ]
            for parameter in parameters:
                annotation = (
                    ast.unparse(parameter.annotation) if parameter.annotation else ""
                )
                if annotation != "str":
                    offenders.append(
                        f"{_relative(path)}: send takes "
                        f"{parameter.arg}: {annotation or 'unannotated'}"
                    )

    assert offenders == [], "a notifier may only carry rendered text: " + "; ".join(
        offenders
    )


# --------------------------------------------------------------------------
# A1 - the boundary between judgement and everything else
# --------------------------------------------------------------------------


def test_the_evidence_pipeline_does_not_evaluate() -> None:
    forbidden = {"evaluation", "core"}

    offenders = [
        _relative(path)
        for path in _sources("pipeline")
        if _imported_modules(path) & forbidden
    ]

    assert (
        offenders == []
    ), "the evidence pipeline transforms evidence and never judges: " + str(offenders)
