<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <!-- Header -->
    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3">
          <svg class="w-8 h-8" viewBox="0 0 16 16" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
          <div>
            <h2 class="text-lg font-semibold text-gray-900">GitHub Integration</h2>
            <p class="text-sm text-gray-600">Sync your assigned issues and project tasks</p>
          </div>
        </div>

        <!-- Connection Status -->
        <div v-if="isAuthenticated" class="flex items-center gap-2 text-sm">
          <div class="w-2 h-2 rounded-full bg-green-500"></div>
          <span class="text-green-700 font-medium">Connected</span>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="px-6 py-4">
      <!-- Not Authenticated -->
      <div v-if="!isAuthenticated && !isAuthenticating">
        <p class="text-gray-600 mb-4">
          Connect your GitHub account to automatically sync assigned issues and project tasks to
          WhatNow.
        </p>

        <button
          @click="handleConnect"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 transition-colors"
        >
          <svg class="w-5 h-5 mr-2" viewBox="0 0 16 16" fill="currentColor">
            <path
              fill-rule="evenodd"
              d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
            />
          </svg>
          Connect GitHub
        </button>
      </div>

      <!-- Authenticating - Device Flow -->
      <div v-else-if="isAuthenticating && deviceFlow">
        <div class="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 class="text-lg font-semibold text-blue-900 mb-4">Complete GitHub Authorization</h3>

          <div class="space-y-4">
            <!-- Step 1: User Code -->
            <div>
              <p class="text-sm text-blue-800 mb-2 font-medium">1. Copy this code:</p>
              <div class="flex items-center gap-2">
                <code
                  class="flex-1 px-4 py-3 bg-white border border-blue-300 rounded-md font-mono text-2xl font-bold text-blue-900 text-center tracking-wider"
                >
                  {{ deviceFlow.userCode }}
                </code>
                <button
                  @click="copyUserCode"
                  class="px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                  :class="{ 'bg-green-600 hover:bg-green-700': codeCopied }"
                >
                  {{ codeCopied ? 'Copied!' : 'Copy' }}
                </button>
              </div>
            </div>

            <!-- Step 2: Open GitHub -->
            <div>
              <p class="text-sm text-blue-800 mb-2 font-medium">
                2. Click here to open GitHub and paste the code:
              </p>
              <a
                :href="deviceFlow.verificationUri"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center px-4 py-2 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                  />
                </svg>
                Open GitHub
              </a>
            </div>

            <!-- Waiting indicator -->
            <div class="flex items-center gap-2 text-sm text-blue-700 pt-2">
              <svg
                class="animate-spin h-4 w-4"
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
              <span>Waiting for authorization...</span>
            </div>

            <!-- Expires info -->
            <p class="text-xs text-blue-600 pt-2">
              Code expires in {{ deviceFlow.expiresIn }} seconds
            </p>
          </div>

          <!-- Cancel button -->
          <div class="mt-6 pt-4 border-t border-blue-200">
            <button
              @click="handleCancelAuth"
              class="text-sm text-blue-700 hover:text-blue-800 font-medium"
            >
              Cancel
            </button>
          </div>
        </div>

        <!-- Auth Error -->
        <div v-if="authError" class="mt-4 bg-red-50 border border-red-200 rounded-lg p-4">
          <p class="text-sm text-red-800">{{ authError }}</p>
        </div>
      </div>

      <!-- Authenticated -->
      <div v-else-if="isAuthenticated">
        <!-- Sync Controls -->
        <div class="space-y-4">
          <!-- Sync Button -->
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-gray-900">Manual Sync</p>
              <p class="text-sm text-gray-600">Sync your GitHub issues now</p>
            </div>
            <button
              @click="handleSync"
              :disabled="isSyncing"
              class="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <svg
                class="w-4 h-4 mr-2"
                :class="{ 'animate-spin': isSyncing }"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              {{ isSyncing ? 'Syncing...' : 'Sync Now' }}
            </button>
          </div>

          <!-- Last Sync -->
          <div v-if="lastSyncTime" class="text-sm text-gray-600">
            Last synced: {{ formatLastSync(lastSyncTime) }}
          </div>

          <!-- Sync Error -->
          <div v-if="syncError" class="bg-red-50 border border-red-200 rounded-lg p-4">
            <p class="text-sm text-red-800">{{ syncError }}</p>
          </div>

          <!-- Disconnect -->
          <div class="pt-4 border-t border-gray-200">
            <button
              @click="handleDisconnect"
              class="text-sm text-red-600 hover:text-red-700 font-medium"
            >
              Disconnect GitHub
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useGitHub } from '../../composables/useGitHub';

const {
  isAuthenticated,
  isSyncing,
  isAuthenticating,
  deviceFlow,
  lastSyncTime,
  syncError,
  authError,
  startDeviceFlow,
  cancelDeviceFlow,
  signOut,
  performSync
} = useGitHub();

const codeCopied = ref(false);

/**
 * Handle connect button click
 */
const handleConnect = async () => {
  await startDeviceFlow();
};

/**
 * Handle cancel authentication
 */
const handleCancelAuth = () => {
  cancelDeviceFlow();
};

/**
 * Handle sync button click
 */
const handleSync = async () => {
  await performSync();
};

/**
 * Handle disconnect button click
 */
const handleDisconnect = async () => {
  if (confirm('Are you sure you want to disconnect GitHub?')) {
    await signOut();
  }
};

/**
 * Copy user code to clipboard
 */
const copyUserCode = async () => {
  if (!deviceFlow.value) return;

  try {
    await navigator.clipboard.writeText(deviceFlow.value.userCode);
    codeCopied.value = true;
    setTimeout(() => {
      codeCopied.value = false;
    }, 2000);
  } catch (error) {
    console.error('Failed to copy user code:', error);
  }
};

/**
 * Format last sync time
 */
const formatLastSync = (timestamp: number): string => {
  const now = Date.now();
  const diff = now - timestamp;

  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return 'just now';
  if (minutes === 1) return '1 minute ago';
  if (minutes < 60) return `${minutes} minutes ago`;
  if (hours === 1) return '1 hour ago';
  if (hours < 24) return `${hours} hours ago`;
  if (days === 1) return '1 day ago';
  return `${days} days ago`;
};
</script>
