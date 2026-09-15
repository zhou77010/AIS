"""AIS scheduler.

Runs the evaluation cycle repeatedly at a fixed interval.

The scheduler owns the loop and nothing else: the cycle is handed to it, so it
knows nothing about analysis, notification or the market clock. Waiting is a
sleep rather than a poll, so the process costs nothing between cycles, and the
loop is left interruptible so the caller decides how a shutdown is reported.
"""

from __future__ import annotations

import time
from collections.abc import Callable

from config.logging_config import get_logger
from utils.constants import CycleStatus

_LOGGER_NAME = "scheduler"
_SECONDS_PER_MINUTE = 60


class Scheduler:
    """Runs the evaluation cycle repeatedly at a fixed interval."""

    def __init__(self, interval_minutes: int) -> None:
        """Create the scheduler.

        Args:
            interval_minutes: Minutes to wait between cycles. Zero or less runs
                a single cycle and returns.
        """
        self._interval_minutes = interval_minutes
        self._interval_seconds = interval_minutes * _SECONDS_PER_MINUTE
        self._logger = get_logger(_LOGGER_NAME)

    def run(self, cycle: Callable[[], CycleStatus]) -> None:
        """Run the cycle on the configured interval, until interrupted.

        The first cycle runs immediately. Every following cycle runs once the
        interval has elapsed. The call only returns when the interval is zero or
        less, or when the caller interrupts it.

        Args:
            cycle: Work to run once per cycle.
        """
        while True:
            self._run_once(cycle)
            if self._interval_seconds <= 0:
                self._logger.info("interval is zero; stopping after one cycle")
                return
            self._logger.info("next cycle in %d minute(s)", self._interval_minutes)
            time.sleep(self._interval_seconds)

    def _run_once(self, cycle: Callable[[], CycleStatus]) -> None:
        """Run one cycle and report its outcome.

        A cycle that raises is recorded and the loop continues: an evaluation
        that fails once must not stop a system meant to keep running.
        """
        try:
            status = cycle()
        except Exception:  # noqa: BLE001 - the loop must survive any failure
            self._logger.exception(
                "cycle failed unexpectedly and was recorded as %s",
                CycleStatus.EVALUATION_FAILED.value,
            )
            return
        self._logger.info("cycle finished: %s", status.value)
