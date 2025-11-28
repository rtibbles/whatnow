<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading state -->
    <div v-if="!isInitialized" class="flex items-center justify-center min-h-screen">
      <LoadingSpinner />
    </div>

    <!-- Error state -->
    <div v-else-if="initError" class="flex items-center justify-center min-h-screen">
      <div class="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
        <h2 class="text-xl font-bold text-red-800 mb-2">Database Error</h2>
        <p class="text-red-600">{{ initError.message }}</p>
      </div>
    </div>

    <!-- Main app -->
    <MainLayout v-else>
      <template #header>
        <AppHeader />
      </template>

      <template #content>
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <!-- Work Session Control -->
          <div class="mb-8">
            <WorkSessionControl />
          </div>

          <!-- Google Calendar Settings -->
          <div class="mb-8">
            <GoogleCalendarSettings />
          </div>

          <!-- GitHub Settings -->
          <div class="mb-8">
            <GitHubSettings />
          </div>

          <!-- Placeholder content -->
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">Welcome to WhatNow</h2>
            <p class="text-gray-600">
              Phase 2, 3, 4 & 5 complete! Connect your Google Calendar and GitHub above to sync
              meetings, events, and assigned issues.
            </p>
          </div>
        </div>
      </template>
    </MainLayout>

    <!-- Ping Dialog -->
    <PingDialog
      v-if="currentPingIndex !== null && currentPingTime !== null"
      :ping-index="currentPingIndex"
      :ping-time="currentPingTime"
      :show="showPingDialog"
      @complete="handlePingComplete"
      @dismiss="dismissPing"
    />

    <!-- Missed Pings Dialog -->
    <MissedPingsDialog
      :missed-pings="missedPings"
      :show="showMissedPingsDialog"
      @complete="handleMissedPingsComplete"
      @dismiss="dismissMissedPings"
    />
  </div>
</template>

<script setup lang="ts">
import { useDatabase } from './composables/useDatabase';
import { usePoissonScheduler } from './composables/usePoissonScheduler';
import MainLayout from './components/layout/MainLayout.vue';
import AppHeader from './components/layout/AppHeader.vue';
import LoadingSpinner from './components/common/LoadingSpinner.vue';
import WorkSessionControl from './components/work-session/WorkSessionControl.vue';
import GoogleCalendarSettings from './components/settings/GoogleCalendarSettings.vue';
import GitHubSettings from './components/settings/GitHubSettings.vue';
import PingDialog from './components/ping/PingDialog.vue';
import MissedPingsDialog from './components/ping/MissedPingsDialog.vue';

const { isInitialized, initError } = useDatabase();

const {
  currentPingIndex,
  currentPingTime,
  showPingDialog,
  showMissedPingsDialog,
  missedPings,
  completePing,
  completeMissedPings,
  dismissPing,
  dismissMissedPings
} = usePoissonScheduler();

// Handle ping completion
const handlePingComplete = async (pingIndex: number) => {
  await completePing(pingIndex);
};

// Handle missed pings completion
const handleMissedPingsComplete = async (pingIndices: number[]) => {
  await completeMissedPings(pingIndices);
};
</script>
