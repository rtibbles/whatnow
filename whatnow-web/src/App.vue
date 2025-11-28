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
          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-2xl font-bold text-gray-900 mb-4">Welcome to WhatNow</h2>
            <p class="text-gray-600">
              Phase 1 setup complete! Database initialized with {{ collectionCount }} collections.
            </p>
          </div>
        </div>
      </template>
    </MainLayout>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useDatabase } from './composables/useDatabase';
import MainLayout from './components/layout/MainLayout.vue';
import AppHeader from './components/layout/AppHeader.vue';
import LoadingSpinner from './components/common/LoadingSpinner.vue';

const { db, isInitialized, initError } = useDatabase();

const collectionCount = computed(() => {
  if (!db.value) return 0;
  return Object.keys(db.value.collections).length;
});
</script>
