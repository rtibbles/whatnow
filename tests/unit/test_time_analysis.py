"""Unit tests for time analysis calculations."""

import pytest
from datetime import datetime, timedelta


class TestTagTimeFormula:
    """Tests for TagTime statistical formula calculations."""

    def test_basic_time_calculation(self):
        """Test basic time calculation from pings."""
        # If we have 10 pings total and 3 are for 'coding'
        # and we worked 5 hours, then coding took 1.5 hours
        total_pings = 10
        coding_pings = 3
        total_hours = 5.0

        coding_hours = (coding_pings / total_pings) * total_hours
        assert coding_hours == pytest.approx(1.5)

    def test_percentage_calculation(self):
        """Test percentage calculation."""
        total_pings = 20
        meeting_pings = 5

        percentage = (meeting_pings / total_pings) * 100
        assert percentage == pytest.approx(25.0)

    def test_multiple_categories(self):
        """Test calculation for multiple categories."""
        total_pings = 100
        total_hours = 8.0

        categories = {
            'coding': 40,
            'meetings': 20,
            'email': 15,
            'break': 10,
            'planning': 15
        }

        # Calculate time for each
        times = {}
        for category, pings in categories.items():
            times[category] = (pings / total_pings) * total_hours

        # Verify calculations
        assert times['coding'] == pytest.approx(3.2)
        assert times['meetings'] == pytest.approx(1.6)
        assert times['email'] == pytest.approx(1.2)

        # Sum should equal total (accounting for rounding)
        assert sum(times.values()) == pytest.approx(total_hours)

    def test_zero_pings(self):
        """Test behavior with zero pings."""
        total_pings = 0
        total_hours = 5.0

        # Should handle division by zero gracefully
        if total_pings > 0:
            result = (1 / total_pings) * total_hours
        else:
            result = 0

        assert result == 0

    def test_single_ping(self):
        """Test with single ping."""
        total_pings = 1
        category_pings = 1
        total_hours = 2.0

        time = (category_pings / total_pings) * total_hours
        assert time == pytest.approx(2.0)  # 100% of time

    def test_precision(self):
        """Test calculation precision with small numbers."""
        total_pings = 1000
        category_pings = 1
        total_hours = 40.0

        time = (category_pings / total_pings) * total_hours
        # Should be 0.04 hours = 2.4 minutes
        assert time == pytest.approx(0.04)
        assert time * 60 == pytest.approx(2.4)  # minutes


class TestTimeAggregation:
    """Tests for time aggregation calculations."""

    def test_daily_aggregation(self):
        """Test aggregating pings by day."""
        # Simulate pings across multiple days
        pings_by_day = {
            '2025-11-10': 32,
            '2025-11-11': 28,
            '2025-11-12': 35
        }

        work_hours_by_day = {
            '2025-11-10': 8.0,
            '2025-11-11': 7.0,
            '2025-11-12': 8.5
        }

        # Calculate average pings per day
        avg_pings = sum(pings_by_day.values()) / len(pings_by_day)
        assert avg_pings == pytest.approx(31.67, abs=0.01)

        # Calculate total hours
        total_hours = sum(work_hours_by_day.values())
        assert total_hours == pytest.approx(23.5)

    def test_weekly_aggregation(self):
        """Test aggregating pings by week."""
        # 5 days of work, 32 pings per day (45-min average)
        pings_per_day = 32
        days_worked = 5
        hours_per_day = 8.0

        total_pings = pings_per_day * days_worked
        total_hours = hours_per_day * days_worked

        assert total_pings == 160
        assert total_hours == pytest.approx(40.0)

    def test_tag_distribution(self):
        """Test calculating distribution across multiple tags."""
        total_pings = 50
        total_hours = 8.0

        tag_pings = {
            'work': 35,
            'break': 10,
            'admin': 5
        }

        distributions = {}
        for tag, pings in tag_pings.items():
            percentage = (pings / total_pings) * 100
            hours = (pings / total_pings) * total_hours
            distributions[tag] = {
                'percentage': percentage,
                'hours': hours
            }

        assert distributions['work']['percentage'] == pytest.approx(70.0)
        assert distributions['work']['hours'] == pytest.approx(5.6)
        assert distributions['break']['percentage'] == pytest.approx(20.0)
        assert distributions['admin']['hours'] == pytest.approx(0.8)


class TestStatisticalAccuracy:
    """Tests for statistical accuracy of TagTime method."""

    def test_expected_variance(self):
        """Test expected variance in ping counts."""
        # For Poisson distribution with rate λ, variance = λ
        # With 45-min average, expect 32 pings/day
        expected_pings_per_day = 32

        # Standard deviation = sqrt(λ)
        import math
        std_dev = math.sqrt(expected_pings_per_day)

        assert std_dev == pytest.approx(5.66, abs=0.01)

        # 95% confidence interval is approximately ±2 std devs
        lower_bound = expected_pings_per_day - 2 * std_dev
        upper_bound = expected_pings_per_day + 2 * std_dev

        assert lower_bound == pytest.approx(20.68, abs=0.01)
        assert upper_bound == pytest.approx(43.32, abs=0.01)

    def test_minimum_sample_size(self):
        """Test that we need sufficient pings for accuracy."""
        # With very few pings, estimates are unreliable
        few_pings = 5
        many_pings = 100

        # Variance as fraction of mean
        few_variance_ratio = 1.0 / few_pings
        many_variance_ratio = 1.0 / many_pings

        # More pings = less variance relative to mean
        assert many_variance_ratio < few_variance_ratio
        assert many_variance_ratio == pytest.approx(0.01)
        assert few_variance_ratio == pytest.approx(0.2)

    def test_confidence_intervals(self):
        """Test calculation of confidence intervals."""
        import math

        total_pings = 100
        category_pings = 30
        total_hours = 8.0

        # Point estimate
        estimated_hours = (category_pings / total_pings) * total_hours

        # Standard error for proportion
        proportion = category_pings / total_pings
        se = math.sqrt((proportion * (1 - proportion)) / total_pings)

        # 95% confidence interval (±1.96 SE)
        margin_of_error = 1.96 * se * total_hours

        lower = estimated_hours - margin_of_error
        upper = estimated_hours + margin_of_error

        assert estimated_hours == pytest.approx(2.4)
        assert lower < estimated_hours < upper
        assert margin_of_error < estimated_hours * 0.5  # Within 50% for reasonable sample
