import { describe, it, expect } from 'vitest';
import { generatePingSchedule, calculateScheduleStats } from '../../services/poisson-scheduler';

describe('Poisson Scheduler', () => {
  describe('generatePingSchedule', () => {
    it('generates correct number of pings', () => {
      const schedule = generatePingSchedule(Date.now(), 100, 45);
      expect(schedule).toHaveLength(100);
    });

    it('generates increasing timestamps', () => {
      const schedule = generatePingSchedule(Date.now(), 50, 45);

      for (let i = 1; i < schedule.length; i++) {
        expect(schedule[i]!).toBeGreaterThan(schedule[i - 1]!);
      }
    });

    it('starts at the specified start time', () => {
      const startTime = Date.now();
      const schedule = generatePingSchedule(startTime, 10, 45);

      // First ping should be after start time
      expect(schedule[0]).toBeGreaterThan(startTime);
    });

    it('generates valid timestamps', () => {
      const schedule = generatePingSchedule(Date.now(), 20, 45);

      schedule.forEach(timestamp => {
        expect(timestamp).toBeGreaterThan(0);
        expect(Number.isInteger(timestamp)).toBe(true);
      });
    });
  });

  describe('calculateScheduleStats', () => {
    it('calculates statistics correctly', () => {
      const schedule = generatePingSchedule(Date.now(), 100, 45);
      const stats = calculateScheduleStats(schedule);

      expect(stats.averageGapMinutes).toBeGreaterThan(0);
      expect(stats.minGapMinutes).toBeGreaterThan(0);
      expect(stats.maxGapMinutes).toBeGreaterThan(0);
      expect(stats.totalDurationHours).toBeGreaterThan(0);
      expect(stats.minGapMinutes).toBeLessThan(stats.maxGapMinutes);
    });

    it('has statistically correct average gap', () => {
      // Large sample for statistical test
      const schedule = generatePingSchedule(Date.now(), 1000, 45);
      const stats = calculateScheduleStats(schedule);

      // Average should be within 10% of expected (45 minutes)
      // Due to randomness, we allow a reasonable margin
      expect(stats.averageGapMinutes).toBeGreaterThan(40);
      expect(stats.averageGapMinutes).toBeLessThan(50);
    });

    it('follows exponential distribution characteristics', () => {
      // Large sample for statistical test
      const schedule = generatePingSchedule(Date.now(), 10000, 45);
      const stats = calculateScheduleStats(schedule);

      // In exponential distribution:
      // - Min is much less than average (very short intervals possible)
      // - Max is much greater than average (very long intervals possible)
      expect(stats.minGapMinutes).toBeLessThan(stats.averageGapMinutes * 0.2);
      expect(stats.maxGapMinutes).toBeGreaterThan(stats.averageGapMinutes * 3);
    });

    it('works with different average gap values', () => {
      const testCases = [
        { avgGap: 15, expected: { min: 10, max: 20 } },
        { avgGap: 30, expected: { min: 25, max: 35 } },
        { avgGap: 60, expected: { min: 50, max: 70 } }
      ];

      testCases.forEach(({ avgGap, expected }) => {
        const schedule = generatePingSchedule(Date.now(), 500, avgGap);
        const stats = calculateScheduleStats(schedule);

        // Average should be close to expected
        expect(stats.averageGapMinutes).toBeGreaterThan(expected.min);
        expect(stats.averageGapMinutes).toBeLessThan(expected.max);
      });
    });

    it('calculates total duration correctly', () => {
      const startTime = Date.now();
      const schedule = generatePingSchedule(startTime, 100, 45);
      const stats = calculateScheduleStats(schedule);

      // With 100 pings at 45 min average, total should be roughly 100 * 45 / 60 hours
      // Allow wide margin due to randomness
      const expectedHours = (100 * 45) / 60;
      expect(stats.totalDurationHours).toBeGreaterThan(expectedHours * 0.7);
      expect(stats.totalDurationHours).toBeLessThan(expectedHours * 1.3);
    });
  });

  describe('edge cases', () => {
    it('handles single ping', () => {
      const schedule = generatePingSchedule(Date.now(), 1, 45);
      expect(schedule).toHaveLength(1);
    });

    it('handles small average gap', () => {
      const schedule = generatePingSchedule(Date.now(), 10, 1);
      const stats = calculateScheduleStats(schedule);

      // Should still work with 1 minute average
      expect(stats.averageGapMinutes).toBeGreaterThan(0.5);
      expect(stats.averageGapMinutes).toBeLessThan(1.5);
    });

    it('handles large average gap', () => {
      const schedule = generatePingSchedule(Date.now(), 50, 120);
      const stats = calculateScheduleStats(schedule);

      // Should work with 2 hour average (wider margin due to randomness with larger gaps)
      expect(stats.averageGapMinutes).toBeGreaterThan(90);
      expect(stats.averageGapMinutes).toBeLessThan(150);
    });
  });

  describe('randomness', () => {
    it('generates different schedules each time', () => {
      const startTime = Date.now();
      const schedule1 = generatePingSchedule(startTime, 50, 45);
      const schedule2 = generatePingSchedule(startTime, 50, 45);

      // Schedules should be different (random)
      let differences = 0;
      for (let i = 0; i < schedule1.length; i++) {
        if (schedule1[i] !== schedule2[i]) {
          differences++;
        }
      }

      // At least some pings should be different
      expect(differences).toBeGreaterThan(45); // Most should be different
    });

    it('maintains randomness across multiple generations', () => {
      const averages: number[] = [];

      // Generate 10 schedules and check their averages
      for (let i = 0; i < 10; i++) {
        const schedule = generatePingSchedule(Date.now(), 100, 45);
        const stats = calculateScheduleStats(schedule);
        averages.push(stats.averageGapMinutes);
      }

      // All averages should be different (very unlikely to be exactly the same)
      const uniqueAverages = new Set(averages);
      expect(uniqueAverages.size).toBeGreaterThan(8); // Most should be unique
    });
  });
});
