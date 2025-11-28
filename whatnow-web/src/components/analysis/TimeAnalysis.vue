<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
      <h2 class="text-lg font-semibold text-gray-900">Time Analysis</h2>
      <p class="text-sm text-gray-600 mt-1">
        Analyze your time distribution across activities, tags, and tasks
      </p>
    </div>

    <!-- Controls -->
    <div class="px-6 py-4 border-b border-gray-200">
      <div class="flex flex-wrap gap-4 items-end">
        <!-- Date Range Selector -->
        <div class="flex-1 min-w-[200px]">
          <label class="block text-sm font-medium text-gray-700 mb-2">Time Period</label>
          <select
            v-model="selectedRange"
            @change="handleRangeChange"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option v-for="option in rangeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <!-- Custom Date Range -->
        <template v-if="selectedRange === 'custom'">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
            <input
              v-model="customStart"
              type="date"
              class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">End Date</label>
            <input
              v-model="customEnd"
              type="date"
              class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </template>

        <!-- Average Gap -->
        <div class="w-32">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Avg Gap (min)
          </label>
          <input
            v-model.number="averageGapMinutes"
            type="number"
            min="1"
            max="120"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <!-- Analyze Button -->
        <button
          @click="analyze"
          :disabled="isAnalyzing"
          class="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="!isAnalyzing">Analyze</span>
          <span v-else class="flex items-center">
            <svg
              class="animate-spin h-4 w-4 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              />
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Analyzing...
          </span>
        </button>
      </div>

      <!-- Error Message -->
      <div v-if="analysisError" class="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-sm text-red-800">{{ analysisError }}</p>
      </div>
    </div>

    <!-- Results -->
    <div v-if="hasData" class="px-6 py-4">
      <!-- Summary Cards -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-blue-50 rounded-lg p-4">
          <p class="text-sm text-blue-600 font-medium">Total Time</p>
          <p class="text-2xl font-bold text-blue-900 mt-1">
            {{ formatDuration(analysisResult!.totalMinutes) }}
          </p>
        </div>
        <div class="bg-green-50 rounded-lg p-4">
          <p class="text-sm text-green-600 font-medium">Total Pings</p>
          <p class="text-2xl font-bold text-green-900 mt-1">
            {{ analysisResult!.totalPings }}
          </p>
        </div>
        <div class="bg-purple-50 rounded-lg p-4">
          <p class="text-sm text-purple-600 font-medium">Meeting Time</p>
          <p class="text-2xl font-bold text-purple-900 mt-1">
            {{ formatDuration(analysisResult!.meetingMinutes) }}
          </p>
          <p class="text-xs text-purple-600 mt-1">
            {{ formatPercentage(analysisResult!.meetingPercentage) }}
          </p>
        </div>
        <div class="bg-orange-50 rounded-lg p-4">
          <p class="text-sm text-orange-600 font-medium">Average Gap</p>
          <p class="text-2xl font-bold text-orange-900 mt-1">
            {{ analysisResult!.averageGapMinutes }}m
          </p>
        </div>
      </div>

      <!-- Export Buttons -->
      <div class="flex gap-3 mb-6 pb-6 border-b border-gray-200">
        <button
          @click="handleExportPings('csv')"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export Pings (CSV)
        </button>
        <button
          @click="handleExportPings('json')"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export Pings (JSON)
        </button>
        <button
          @click="handleExportAnalysis('csv')"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Export Analysis (CSV)
        </button>
        <button
          @click="handleExportAnalysis('json')"
          class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Export Analysis (JSON)
        </button>
      </div>

      <!-- Tabs -->
      <div class="border-b border-gray-200">
        <nav class="-mb-px flex space-x-8">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            @click="activeTab = tab.id"
            :class="[
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors'
            ]"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <!-- Tab Content -->
      <div class="mt-6">
        <!-- By Tag -->
        <div v-if="activeTab === 'tags'" class="space-y-3">
          <div
            v-for="tag in analysisResult!.byTag"
            :key="tag.tag"
            class="bg-gray-50 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-gray-900">{{ tag.tag }}</span>
              <div class="text-right">
                <p class="text-lg font-semibold text-gray-900">
                  {{ formatDuration(tag.totalMinutes) }}
                </p>
                <p class="text-xs text-gray-500">{{ formatPercentage(tag.percentage) }}</p>
              </div>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-blue-600 h-2 rounded-full"
                :style="{ width: tag.percentage + '%' }"
              ></div>
            </div>
            <p class="text-sm text-gray-600 mt-2">{{ tag.pingCount }} pings</p>
          </div>
        </div>

        <!-- By TODO -->
        <div v-else-if="activeTab === 'todos'" class="space-y-3">
          <div
            v-for="todo in analysisResult!.byTodo"
            :key="todo.todoId"
            class="bg-gray-50 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <div>
                <span class="font-medium text-gray-900">{{ todo.todoId }}</span>
                <span class="ml-2 text-xs text-gray-500 uppercase">({{ todo.todoType }})</span>
              </div>
              <div class="text-right">
                <p class="text-lg font-semibold text-gray-900">
                  {{ formatDuration(todo.totalMinutes) }}
                </p>
                <p class="text-xs text-gray-500">{{ formatPercentage(todo.percentage) }}</p>
              </div>
            </div>
            <div class="w-full bg-gray-200 rounded-full h-2">
              <div
                class="bg-purple-600 h-2 rounded-full"
                :style="{ width: todo.percentage + '%' }"
              ></div>
            </div>
            <div class="flex items-center justify-between mt-2">
              <p class="text-sm text-gray-600">{{ todo.pingCount}} pings</p>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="tag in todo.tags"
                  :key="tag"
                  class="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-700"
                >
                  {{ tag }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!isAnalyzing && !hasData" class="px-6 py-12 text-center">
      <svg
        class="mx-auto h-12 w-12 text-gray-400"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </svg>
      <h3 class="mt-2 text-sm font-medium text-gray-900">No data yet</h3>
      <p class="mt-1 text-sm text-gray-500">
        Select a time period and click "Analyze" to see your time distribution
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useTimeAnalysis } from '../../composables/useTimeAnalysis';

const {
  isAnalyzing,
  analysisResult,
  analysisError,
  selectedRange,
  customStartDate,
  customEndDate,
  averageGapMinutes,
  rangeOptions,
  hasData,
  analyze,
  exportPings,
  exportAnalysis,
  formatDuration,
  formatPercentage
} = useTimeAnalysis();

const activeTab = ref<'tags' | 'todos'>('tags');

const tabs = [
  { id: 'tags' as const, label: 'By Tag' },
  { id: 'todos' as const, label: 'By TODO' }
];

// Custom date inputs
const customStart = computed({
  get: () => customStartDate.value.toISOString().split('T')[0],
  set: (val: string) => {
    customStartDate.value = new Date(val);
  }
});

const customEnd = computed({
  get: () => customEndDate.value.toISOString().split('T')[0],
  set: (val: string) => {
    customEndDate.value = new Date(val);
  }
});

/**
 * Handle range change
 */
const handleRangeChange = () => {
  // Auto-analyze when range changes (except custom)
  if (selectedRange.value !== 'custom') {
    analyze();
  }
};

/**
 * Handle export pings
 */
const handleExportPings = async (format: 'csv' | 'json') => {
  try {
    await exportPings(format);
  } catch (error) {
    console.error('Export error:', error);
    alert('Failed to export pings');
  }
};

/**
 * Handle export analysis
 */
const handleExportAnalysis = async (format: 'csv' | 'json') => {
  try {
    await exportAnalysis(format);
  } catch (error) {
    console.error('Export analysis error:', error);
    alert('Failed to export analysis');
  }
};
</script>
