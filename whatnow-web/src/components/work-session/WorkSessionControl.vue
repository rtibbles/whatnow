<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useWorkSession } from '../../composables/useWorkSession';
import { usePoissonScheduler } from '../../composables/usePoissonScheduler';

const { isActive, startSession, endSession, getCurrentDuration } = useWorkSession();
const {
  isActive: schedulerActive,
  nextPingTime,
  start: startScheduler,
  stop: stopScheduler,
  requestNotificationPermission
} = usePoissonScheduler();

const averageGapMinutes = ref(45);
const sessionDuration = ref('0:00:00');
const notificationPermission = ref<NotificationPermission>(
  'Notification' in window ? Notification.permission : 'denied'
);

// Format duration as HH:MM:SS
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

// Update session duration every second
let durationInterval: number | null = null;

watch(isActive, (active) => {
  if (active) {
    // Start duration update interval
    durationInterval = window.setInterval(() => {
      sessionDuration.value = formatDuration(getCurrentDuration.value);
    }, 1000);
  } else {
    // Stop duration update interval
    if (durationInterval) {
      clearInterval(durationInterval);
      durationInterval = null;
    }
    sessionDuration.value = '0:00:00';
  }
});

// Format next ping time
const nextPingFormatted = computed(() => {
  if (!nextPingTime.value) return null;
  const date = new Date(nextPingTime.value);
  return date.toLocaleTimeString();
});

// Time until next ping
const timeUntilNextPing = computed(() => {
  if (!nextPingTime.value) return null;
  const diff = Math.max(0, nextPingTime.value - Date.now());
  const minutes = Math.floor(diff / 1000 / 60);
  const seconds = Math.floor((diff / 1000) % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
});

// Start work session and scheduler
const handleStart = async () => {
  try {
    // Request notification permission first
    const permission = await requestNotificationPermission();
    notificationPermission.value = permission;

    // Start work session
    await startSession();

    // Start ping scheduler
    await startScheduler(averageGapMinutes.value);
  } catch (error) {
    console.error('Failed to start work session:', error);
    alert('Failed to start work session. Please try again.');
  }
};

// Stop work session and scheduler
const handleStop = async () => {
  try {
    // Stop ping scheduler
    await stopScheduler();

    // End work session
    await endSession();
  } catch (error) {
    console.error('Failed to stop work session:', error);
    alert('Failed to stop work session. Please try again.');
  }
};
</script>

<template>
  <div class="work-session-control">
    <div v-if="!isActive" class="start-view">
      <h2 class="text-2xl font-bold mb-4">Start Work Session</h2>

      <div class="mb-4">
        <label for="average-gap" class="block text-sm font-medium mb-2">
          Average ping interval (minutes):
        </label>
        <input
          id="average-gap"
          v-model.number="averageGapMinutes"
          type="number"
          min="5"
          max="120"
          class="w-full px-3 py-2 border rounded-md"
        />
        <p class="text-xs text-gray-600 mt-1">
          Recommended: 45 minutes (TagTime default)
        </p>
      </div>

      <div v-if="notificationPermission === 'denied'" class="mb-4 p-3 bg-yellow-100 border border-yellow-400 rounded">
        <p class="text-sm text-yellow-800">
          ⚠️ Notifications are blocked. You may miss pings when the tab is hidden.
          Please enable notifications in your browser settings.
        </p>
      </div>

      <button
        @click="handleStart"
        class="w-full px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
      >
        Start Work Session
      </button>
    </div>

    <div v-else class="active-view">
      <h2 class="text-2xl font-bold mb-4">Active Work Session</h2>

      <div class="stats-grid mb-6">
        <div class="stat-card">
          <div class="text-sm text-gray-600">Session Duration</div>
          <div class="text-2xl font-mono font-bold">{{ sessionDuration }}</div>
        </div>

        <div class="stat-card" v-if="schedulerActive">
          <div class="text-sm text-gray-600">Next Ping</div>
          <div class="text-lg font-medium">{{ nextPingFormatted || 'N/A' }}</div>
          <div class="text-sm text-gray-500" v-if="timeUntilNextPing">
            in {{ timeUntilNextPing }}
          </div>
        </div>

        <div class="stat-card">
          <div class="text-sm text-gray-600">Ping Interval</div>
          <div class="text-lg font-medium">~{{ averageGapMinutes }} min</div>
        </div>
      </div>

      <button
        @click="handleStop"
        class="w-full px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
      >
        End Work Session
      </button>
    </div>
  </div>
</template>

<style scoped>
.work-session-control {
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  padding: 1rem;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
}
</style>
