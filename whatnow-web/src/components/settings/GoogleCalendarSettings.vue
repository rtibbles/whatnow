<script setup lang="ts">
import { computed } from 'vue';
import { useGoogleCalendar } from '../../composables/useGoogleCalendar';

const {
  isAuthenticated,
  isSyncing,
  lastSyncTime,
  syncError,
  signIn,
  signOut,
  performSync
} = useGoogleCalendar();

// Format last sync time
const lastSyncFormatted = computed(() => {
  if (!lastSyncTime.value) return 'Never';
  const date = new Date(lastSyncTime.value);
  return date.toLocaleString();
});

// Handle sign in
const handleSignIn = async () => {
  await signIn();
};

// Handle sign out
const handleSignOut = async () => {
  if (confirm('Are you sure you want to disconnect Google Calendar?')) {
    await signOut();
  }
};

// Handle manual sync
const handleSync = async () => {
  await performSync(7); // Sync next 7 days
};
</script>

<template>
  <div class="google-calendar-settings">
    <h3 class="text-lg font-medium mb-4">Google Calendar</h3>

    <!-- Not authenticated state -->
    <div v-if="!isAuthenticated" class="not-connected">
      <div class="mb-4">
        <p class="text-sm text-gray-600 mb-4">
          Connect your Google Calendar to automatically track meetings and events in your pings.
        </p>
        <ul class="text-xs text-gray-500 list-disc list-inside mb-4">
          <li>Upcoming events appear in ping dialogs</li>
          <li>Meetings are automatically suggested</li>
          <li>Syncs events for the next 7 days</li>
        </ul>
      </div>

      <button
        @click="handleSignIn"
        class="btn-primary"
      >
        <svg class="w-5 h-5 mr-2 inline" fill="currentColor" viewBox="0 0 24 24">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        Connect Google Calendar
      </button>

      <p v-if="syncError" class="text-sm text-red-600 mt-3">
        {{ syncError }}
      </p>
    </div>

    <!-- Authenticated state -->
    <div v-else class="connected">
      <div class="status-card mb-4">
        <div class="flex items-center justify-between mb-3">
          <div class="flex items-center">
            <div class="status-dot bg-green-500"></div>
            <span class="text-sm font-medium text-gray-700">Connected</span>
          </div>
          <button @click="handleSignOut" class="text-xs text-red-600 hover:text-red-700">
            Disconnect
          </button>
        </div>

        <div class="text-xs text-gray-600">
          <div class="mb-1">
            <span class="font-medium">Last synced:</span> {{ lastSyncFormatted }}
          </div>
        </div>
      </div>

      <!-- Sync button -->
      <button
        @click="handleSync"
        :disabled="isSyncing"
        class="btn-secondary w-full"
      >
        <svg
          v-if="isSyncing"
          class="w-4 h-4 mr-2 inline animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <svg
          v-else
          class="w-4 h-4 mr-2 inline"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        {{ isSyncing ? 'Syncing...' : 'Sync Now' }}
      </button>

      <p v-if="syncError" class="text-sm text-red-600 mt-3">
        {{ syncError }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.google-calendar-settings {
  padding: 1.5rem;
  background: white;
  border-radius: 0.5rem;
  border: 1px solid #e5e7eb;
}

.status-card {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 0.375rem;
  border: 1px solid #e5e7eb;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  background-color: #4285f4;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-primary:hover {
  background-color: #3367d6;
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  transition: background-color 0.15s;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #f9fafb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
