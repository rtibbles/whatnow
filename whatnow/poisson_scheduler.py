"""Poisson-distributed ping scheduler for TagTime-style activity tracking.

This module implements a scheduler that triggers "pings" (activity prompts)
at random intervals following a Poisson distribution. This statistical sampling
approach is the core of the TagTime methodology.

Mathematical Background:
The Poisson distribution ensures that pings occur randomly with a specified
average interval. This means:
- If average_gap = 45 minutes, you get ~32 pings per day
- The fraction of pings tagged with activity X approximates the fraction of
  time spent on activity X
- The randomness prevents gaming the system or anticipating pings

Implementation:
The scheduler runs in a background thread and uses exponentially distributed
intervals between pings (characteristic of Poisson processes). It handles
graceful shutdown and can be started/stopped dynamically.

Usage:
    scheduler = PoissonScheduler(
        average_gap_minutes=45,
        ping_callback=lambda: print("Ping!")
    )
    scheduler.start()
    # ... later ...
    scheduler.stop()
"""

import threading
import time
import random
import math
from typing import Callable, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PoissonScheduler:
    """Scheduler that triggers pings based on Poisson distribution.

    This implements TagTime-style random sampling where pings occur
    with an average gap time but are randomly distributed using
    Poisson statistics.
    """

    def __init__(self, average_gap_minutes: float = 45.0,
                 ping_callback: Optional[Callable[[int], None]] = None):
        """Initialize the Poisson scheduler.

        Args:
            average_gap_minutes: Average time between pings in minutes (default 45)
            ping_callback: Function to call when a ping occurs, receives timestamp
        """
        self.average_gap_minutes = average_gap_minutes
        self.ping_callback = ping_callback
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_scheduler, daemon=False)
        self._thread.start()
        logger.info(f"Poisson scheduler started with average gap of {self.average_gap_minutes} minutes")

    def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Poisson scheduler stopped")

    def _get_next_ping_interval(self) -> float:
        """Calculate next ping interval using Poisson distribution.

        Returns:
            Time in seconds until next ping
        """
        # Poisson process: time between events is exponentially distributed
        # Average gap in seconds
        lambda_param = self.average_gap_minutes * 60.0

        # Generate exponentially distributed random interval
        # Using inverse transform sampling: -ln(U) / lambda where U ~ Uniform(0,1)
        u = random.random()
        interval = -math.log(u) * lambda_param

        return interval

    def _run_scheduler(self):
        """Main scheduler loop running in background thread."""
        while self._running:
            # Calculate next ping interval
            interval = self._get_next_ping_interval()
            logger.info(f"Next ping scheduled in {interval/60:.1f} minutes")

            # Wait for the interval or until stopped
            if self._stop_event.wait(timeout=interval):
                # Stop event was set
                break

            if self._running:
                # Trigger ping
                timestamp = int(time.time())
                logger.info(f"Ping triggered at {datetime.fromtimestamp(timestamp)}")

                if self.ping_callback:
                    try:
                        self.ping_callback(timestamp)
                    except Exception as e:
                        logger.error(f"Error in ping callback: {e}")

    def set_average_gap(self, minutes: float):
        """Update the average gap between pings.

        Args:
            minutes: New average gap in minutes
        """
        self.average_gap_minutes = minutes
        logger.info(f"Average gap updated to {minutes} minutes")

    def set_callback(self, callback: Callable[[int], None]):
        """Set or update the ping callback function.

        Args:
            callback: Function to call when a ping occurs
        """
        self.ping_callback = callback

    @property
    def is_running(self) -> bool:
        """Check if scheduler is currently running."""
        return self._running


class PingStatistics:
    """Helper class to validate Poisson distribution characteristics."""

    @staticmethod
    def expected_pings_per_day(average_gap_minutes: float) -> float:
        """Calculate expected number of pings per day.

        Args:
            average_gap_minutes: Average gap in minutes

        Returns:
            Expected number of pings in a 24-hour period
        """
        minutes_per_day = 24 * 60
        return minutes_per_day / average_gap_minutes

    @staticmethod
    def expected_pings_per_week(average_gap_minutes: float) -> float:
        """Calculate expected number of pings per week.

        Args:
            average_gap_minutes: Average gap in minutes

        Returns:
            Expected number of pings in a 7-day period
        """
        return PingStatistics.expected_pings_per_day(average_gap_minutes) * 7


# Example usage and testing
if __name__ == "__main__":
    def test_callback(timestamp: int):
        dt = datetime.fromtimestamp(timestamp)
        print(f"PING! at {dt.strftime('%Y-%m-%d %H:%M:%S')}")

    # Create scheduler with 1-minute average for testing
    scheduler = PoissonScheduler(average_gap_minutes=1.0, ping_callback=test_callback)

    print(f"Expected pings per day (45min avg): {PingStatistics.expected_pings_per_day(45.0):.1f}")
    print(f"Expected pings per week (45min avg): {PingStatistics.expected_pings_per_week(45.0):.1f}")

    print("\nStarting scheduler (will run for 5 minutes with 1-minute average)...")
    scheduler.start()

    try:
        time.sleep(300)  # Run for 5 minutes
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        scheduler.stop()
        print("Scheduler stopped")
