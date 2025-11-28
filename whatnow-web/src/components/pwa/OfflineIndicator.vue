<template>
  <Transition name="slide-up">
    <div
      v-if="!isOnline"
      class="fixed bottom-0 left-0 right-0 z-50 bg-yellow-50 border-t-2 border-yellow-400"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center justify-between gap-3">
          <!-- Offline message -->
          <div class="flex items-center gap-3 flex-1">
            <div class="flex-shrink-0">
              <svg class="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium text-yellow-800">
                You're offline
              </p>
              <p class="text-xs text-yellow-700">
                Some features may be unavailable. Your changes will sync when you're back online.
              </p>
            </div>
          </div>

          <!-- Reconnecting indicator -->
          <div v-if="isReconnecting" class="flex items-center gap-2 flex-shrink-0">
            <div class="animate-spin rounded-full h-4 w-4 border-2 border-yellow-600 border-t-transparent"></div>
            <span class="text-xs text-yellow-700 font-medium">Reconnecting...</span>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Service Worker Update Banner -->
  <Transition name="slide-up">
    <div
      v-if="swUpdateAvailable"
      class="fixed bottom-0 left-0 right-0 z-50 bg-blue-600 text-white"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center justify-between gap-3">
          <!-- Update message -->
          <div class="flex items-center gap-3 flex-1">
            <div class="flex-shrink-0">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </div>
            <div class="flex-1">
              <p class="text-sm font-medium">
                New version available!
              </p>
              <p class="text-xs text-blue-100">
                Click update to get the latest features and improvements
              </p>
            </div>
          </div>

          <!-- Update button -->
          <button
            @click="handleUpdate"
            class="px-4 py-2 bg-white text-blue-700 rounded-lg font-medium text-sm hover:bg-blue-50 transition-colors flex-shrink-0"
          >
            Update Now
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { usePWA } from '../../composables/usePWA';

const {
  isOnline,
  swUpdateAvailable,
  applyUpdate
} = usePWA();

const isReconnecting = ref(false);

// Watch for offline to online transition
watch(isOnline, (newValue, oldValue) => {
  if (!oldValue && newValue) {
    // Just came back online
    isReconnecting.value = true;

    // Show reconnecting for 2 seconds
    setTimeout(() => {
      isReconnecting.value = false;
    }, 2000);
  }
});

const handleUpdate = () => {
  applyUpdate();
};
</script>

<style scoped>
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease-out;
}

.slide-up-enter-from {
  transform: translateY(100%);
  opacity: 0;
}

.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>
