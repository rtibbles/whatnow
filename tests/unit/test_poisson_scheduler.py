"""Unit tests for Poisson scheduler."""

import pytest
import time
import math
from unittest.mock import Mock, patch
from whatnow.poisson_scheduler import PoissonScheduler, PingStatistics


class TestPoissonScheduler:
    """Tests for PoissonScheduler class."""

    def test_initialization(self):
        """Test scheduler initialization with default and custom parameters."""
        # Default initialization
        scheduler = PoissonScheduler()
        assert scheduler.average_gap_minutes == 45.0
        assert scheduler.ping_callback is None
        assert not scheduler.is_running

        # Custom initialization
        callback = Mock()
        scheduler = PoissonScheduler(average_gap_minutes=30.0, ping_callback=callback)
        assert scheduler.average_gap_minutes == 30.0
        assert scheduler.ping_callback == callback

    def test_interval_distribution(self, poisson_intervals):
        """Test that generated intervals follow exponential distribution."""
        scheduler = PoissonScheduler(average_gap_minutes=45.0)

        # Generate many intervals
        intervals = []
        for _ in range(1000):
            interval = scheduler._get_next_ping_interval()
            intervals.append(interval)

        # Check all intervals are positive
        assert all(i > 0 for i in intervals)

        # Check mean is close to expected (45 minutes = 2700 seconds)
        mean_interval = sum(intervals) / len(intervals)
        expected_mean = 45.0 * 60  # 2700 seconds
        # Allow 10% deviation due to randomness
        assert abs(mean_interval - expected_mean) < expected_mean * 0.1

        # Check standard deviation is close to mean (property of exponential distribution)
        variance = sum((i - mean_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = math.sqrt(variance)
        # For exponential distribution, std dev should equal mean
        assert abs(std_dev - expected_mean) < expected_mean * 0.15

    def test_start_stop(self):
        """Test starting and stopping the scheduler."""
        callback = Mock()
        scheduler = PoissonScheduler(average_gap_minutes=0.01, ping_callback=callback)  # Very short interval for testing

        # Start scheduler
        scheduler.start()
        assert scheduler.is_running
        assert scheduler._thread is not None
        assert scheduler._thread.is_alive()

        # Try to start again (should warn but not crash)
        scheduler.start()
        assert scheduler.is_running

        # Stop scheduler
        scheduler.stop()
        assert not scheduler.is_running

        # Wait for thread to finish
        time.sleep(0.1)
        assert not scheduler._thread.is_alive()

    def test_ping_callback_invoked(self):
        """Test that ping callback is invoked when ping triggers."""
        callback = Mock()
        scheduler = PoissonScheduler(average_gap_minutes=0.001, ping_callback=callback)  # Very short interval

        scheduler.start()
        time.sleep(0.2)  # Wait for at least one ping
        scheduler.stop()

        # Callback should have been called at least once
        assert callback.call_count >= 1

        # Check that callback received a timestamp
        call_args = callback.call_args_list[0]
        timestamp = call_args[0][0]
        assert isinstance(timestamp, int)
        assert timestamp > 0

    def test_callback_exception_handling(self):
        """Test that scheduler continues running even if callback raises exception."""
        callback = Mock(side_effect=Exception("Test exception"))
        scheduler = PoissonScheduler(average_gap_minutes=0.001, ping_callback=callback)

        scheduler.start()
        time.sleep(0.2)  # Wait for pings
        scheduler.stop()

        # Scheduler should still have called callback despite exceptions
        assert callback.call_count >= 1
        assert not scheduler.is_running  # But should be stopped now

    def test_set_average_gap(self):
        """Test updating average gap."""
        scheduler = PoissonScheduler(average_gap_minutes=45.0)
        assert scheduler.average_gap_minutes == 45.0

        scheduler.set_average_gap(30.0)
        assert scheduler.average_gap_minutes == 30.0

    def test_set_callback(self):
        """Test updating callback function."""
        callback1 = Mock()
        callback2 = Mock()

        scheduler = PoissonScheduler(ping_callback=callback1)
        assert scheduler.ping_callback == callback1

        scheduler.set_callback(callback2)
        assert scheduler.ping_callback == callback2

    def test_graceful_shutdown(self):
        """Test that scheduler stops gracefully."""
        callback = Mock()
        scheduler = PoissonScheduler(average_gap_minutes=10.0, ping_callback=callback)

        scheduler.start()
        time.sleep(0.1)  # Let it run briefly
        scheduler.stop()

        # Thread should complete within reasonable time
        scheduler._thread.join(timeout=2.0)
        assert not scheduler._thread.is_alive()

    def test_stop_event_interrupts_wait(self):
        """Test that stop event properly interrupts long waits."""
        callback = Mock()
        scheduler = PoissonScheduler(average_gap_minutes=100.0, ping_callback=callback)  # Long interval

        start_time = time.time()
        scheduler.start()
        time.sleep(0.1)  # Let it start waiting
        scheduler.stop()
        end_time = time.time()

        # Stop should be quick, not wait for full interval
        assert (end_time - start_time) < 2.0


class TestPingStatistics:
    """Tests for PingStatistics helper class."""

    def test_expected_pings_per_day(self):
        """Test calculation of expected pings per day."""
        # 45-minute average: 24 * 60 / 45 = 32 pings
        assert PingStatistics.expected_pings_per_day(45.0) == pytest.approx(32.0)

        # 30-minute average: 24 * 60 / 30 = 48 pings
        assert PingStatistics.expected_pings_per_day(30.0) == pytest.approx(48.0)

        # 60-minute average: 24 pings
        assert PingStatistics.expected_pings_per_day(60.0) == pytest.approx(24.0)

    def test_expected_pings_per_week(self):
        """Test calculation of expected pings per week."""
        # 45-minute average: 32 * 7 = 224 pings
        assert PingStatistics.expected_pings_per_week(45.0) == pytest.approx(224.0)

        # 30-minute average: 48 * 7 = 336 pings
        assert PingStatistics.expected_pings_per_week(30.0) == pytest.approx(336.0)

    def test_zero_and_extreme_values(self):
        """Test behavior with edge case values."""
        # Very short interval
        assert PingStatistics.expected_pings_per_day(1.0) == pytest.approx(1440.0)

        # Very long interval
        assert PingStatistics.expected_pings_per_day(1440.0) == pytest.approx(1.0)


@pytest.mark.slow
class TestPoissonDistributionAccuracy:
    """Detailed statistical tests for Poisson distribution accuracy."""

    def test_interval_distribution_properties(self, poisson_intervals):
        """Test that intervals have correct statistical properties."""
        scheduler = PoissonScheduler(average_gap_minutes=10.0)

        # Generate large sample
        sample_size = 5000
        intervals = [scheduler._get_next_ping_interval() for _ in range(sample_size)]

        # Calculate statistics
        mean = sum(intervals) / len(intervals)
        variance = sum((x - mean) ** 2 for x in intervals) / (len(intervals) - 1)
        std_dev = math.sqrt(variance)

        expected_mean = 10.0 * 60  # 600 seconds

        # For exponential distribution:
        # - Mean should equal lambda
        # - Variance should equal lambda^2
        # - Std dev should equal lambda

        assert abs(mean - expected_mean) < expected_mean * 0.05  # Within 5%
        assert abs(std_dev - expected_mean) < expected_mean * 0.10  # Within 10%

    def test_memoryless_property(self, poisson_intervals):
        """Test memoryless property of exponential distribution."""
        scheduler = PoissonScheduler(average_gap_minutes=10.0)

        # Generate two independent sequences
        sequence1 = [scheduler._get_next_ping_interval() for _ in range(1000)]
        sequence2 = [scheduler._get_next_ping_interval() for _ in range(1000)]

        # Means should be similar (memoryless property)
        mean1 = sum(sequence1) / len(sequence1)
        mean2 = sum(sequence2) / len(sequence2)

        expected = 10.0 * 60
        assert abs(mean1 - expected) < expected * 0.10
        assert abs(mean2 - expected) < expected * 0.10
        assert abs(mean1 - mean2) < expected * 0.10  # Sequences shouldn't differ significantly
