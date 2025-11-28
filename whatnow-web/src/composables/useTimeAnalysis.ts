/**
 * Composable for time analysis
 */

import { ref, computed } from 'vue';
import { TimeAnalysisService, type DateRange, type TimeAnalysisResult } from '../services/time-analysis';
import { ExportService, type ExportFormat } from '../services/export';

export function useTimeAnalysis() {
  const analysisService = new TimeAnalysisService();

  const isAnalyzing = ref(false);
  const analysisResult = ref<TimeAnalysisResult | null>(null);
  const analysisError = ref<string | null>(null);

  const selectedRange = ref<keyof ReturnType<typeof TimeAnalysisService.getCommonRanges> | 'custom'>('last7Days');
  const customStartDate = ref<Date>(new Date());
  const customEndDate = ref<Date>(new Date());
  const averageGapMinutes = ref(45);

  /**
   * Get current date range
   */
  const currentRange = computed((): DateRange => {
    if (selectedRange.value === 'custom') {
      return {
        start: customStartDate.value,
        end: customEndDate.value
      };
    }

    const ranges = TimeAnalysisService.getCommonRanges();

    // TypeScript guard: ensure we always return a DateRange
    const rangeKey = selectedRange.value;
    if (rangeKey in ranges) {
      return ranges[rangeKey as keyof typeof ranges]!;
    }

    return ranges.last7Days!;
  });

  /**
   * Perform time analysis
   */
  const analyze = async () => {
    isAnalyzing.value = true;
    analysisError.value = null;

    try {
      const result = await analysisService.analyzeTimeRange(
        currentRange.value,
        averageGapMinutes.value
      );
      analysisResult.value = result;
    } catch (error) {
      analysisError.value = error instanceof Error ? error.message : 'Analysis failed';
      console.error('Analysis error:', error);
    } finally {
      isAnalyzing.value = false;
    }
  };

  /**
   * Export pings
   */
  const exportPings = async (format: ExportFormat) => {
    try {
      const pings = await analysisService.getAllPings(currentRange.value);
      await ExportService.exportPings(pings, format);
    } catch (error) {
      console.error('Export error:', error);
      throw error;
    }
  };

  /**
   * Export analysis
   */
  const exportAnalysis = async (format: 'csv' | 'json') => {
    if (!analysisResult.value) {
      throw new Error('No analysis data to export');
    }

    try {
      await ExportService.exportAnalysis(analysisResult.value, format);
    } catch (error) {
      console.error('Export analysis error:', error);
      throw error;
    }
  };

  /**
   * Set date range
   */
  const setRange = (range: typeof selectedRange.value) => {
    selectedRange.value = range;
  };

  /**
   * Set custom date range
   */
  const setCustomRange = (start: Date, end: Date) => {
    customStartDate.value = start;
    customEndDate.value = end;
    selectedRange.value = 'custom';
  };

  /**
   * Format duration helper
   */
  const formatDuration = (minutes: number): string => {
    return TimeAnalysisService.formatDuration(minutes);
  };

  /**
   * Format percentage helper
   */
  const formatPercentage = (percentage: number): string => {
    return TimeAnalysisService.formatPercentage(percentage);
  };

  /**
   * Available range options
   */
  const rangeOptions = computed(() => [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'last7Days', label: 'Last 7 Days' },
    { value: 'last30Days', label: 'Last 30 Days' },
    { value: 'thisWeek', label: 'This Week' },
    { value: 'lastWeek', label: 'Last Week' },
    { value: 'thisMonth', label: 'This Month' },
    { value: 'lastMonth', label: 'Last Month' },
    { value: 'custom', label: 'Custom Range' }
  ]);

  /**
   * Top tags (for quick view)
   */
  const topTags = computed(() => {
    if (!analysisResult.value) return [];
    return analysisResult.value.byTag.slice(0, 5);
  });

  /**
   * Top TODOs (for quick view)
   */
  const topTodos = computed(() => {
    if (!analysisResult.value) return [];
    return analysisResult.value.byTodo.slice(0, 5);
  });

  /**
   * Has data
   */
  const hasData = computed(() => {
    return analysisResult.value && analysisResult.value.totalPings > 0;
  });

  return {
    // State
    isAnalyzing,
    analysisResult,
    analysisError,
    selectedRange,
    customStartDate,
    customEndDate,
    averageGapMinutes,

    // Computed
    currentRange,
    rangeOptions,
    topTags,
    topTodos,
    hasData,

    // Methods
    analyze,
    exportPings,
    exportAnalysis,
    setRange,
    setCustomRange,
    formatDuration,
    formatPercentage
  };
}
