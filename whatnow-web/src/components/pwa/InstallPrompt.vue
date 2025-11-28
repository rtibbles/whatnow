<template>
  <Transition name="slide-down">
    <div
      v-if="shouldShowInstall"
      class="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg"
    >
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center justify-between flex-wrap gap-3">
          <!-- Icon and message -->
          <div class="flex items-center gap-3 flex-1 min-w-0">
            <div class="flex-shrink-0">
              <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="text-sm font-semibold">Install WhatNow</h3>
              <p class="text-xs text-blue-100 mt-0.5">
                Install this app on your device for a better experience and offline access
              </p>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 flex-shrink-0">
            <button
              @click="handleInstall"
              :disabled="isInstalling"
              class="px-4 py-2 bg-white text-blue-700 rounded-lg font-medium text-sm hover:bg-blue-50 transition-colors disabled:opacity-50"
            >
              {{ isInstalling ? 'Installing...' : 'Install' }}
            </button>
            <button
              @click="handleDismiss"
              class="px-3 py-2 text-blue-100 hover:text-white hover:bg-blue-800 rounded-lg transition-colors"
              aria-label="Dismiss install prompt"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { usePWA } from '../../composables/usePWA';

const {
  shouldShowInstall,
  showInstallPrompt,
  dismissInstallPrompt
} = usePWA();

const isInstalling = ref(false);

const handleInstall = async () => {
  isInstalling.value = true;
  try {
    await showInstallPrompt();
  } finally {
    isInstalling.value = false;
  }
};

const handleDismiss = () => {
  dismissInstallPrompt();
};
</script>

<style scoped>
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease-out;
}

.slide-down-enter-from {
  transform: translateY(-100%);
  opacity: 0;
}

.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}
</style>
