<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <!-- Header -->
    <div class="px-6 py-4 border-b border-gray-200">
      <h2 class="text-xl font-semibold text-gray-900">Settings</h2>
      <p class="mt-1 text-sm text-gray-600">
        Configure your WhatNow preferences and manage your data
      </p>
    </div>

    <!-- Error Display -->
    <div v-if="error" class="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
      <div class="flex">
        <div class="flex-shrink-0">
          <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
        </div>
        <div class="ml-3">
          <p class="text-sm text-red-800">{{ error }}</p>
        </div>
      </div>
    </div>

    <!-- Settings Sections -->
    <div class="px-6 py-6 space-y-8">
      <!-- Notifications Section -->
      <section>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Notifications</h3>
        <div class="space-y-4">
          <!-- Enable Notifications -->
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700">Enable Notifications</label>
              <p class="text-sm text-gray-500">Get reminded to record your activity</p>
            </div>
            <div class="flex items-center gap-3">
              <span v-if="notificationPermission === 'denied'" class="text-xs text-red-600">
                Permission denied
              </span>
              <button
                v-if="notificationPermission !== 'granted'"
                @click="handleRequestPermission"
                class="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Enable
              </button>
              <label class="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  :checked="settings.enableNotifications"
                  @change="handleToggle('enableNotifications', $event)"
                  :disabled="notificationPermission !== 'granted'"
                  class="sr-only peer"
                >
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
              </label>
            </div>
          </div>

          <!-- Notification Sound -->
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700">Notification Sound</label>
              <p class="text-sm text-gray-500">Play sound with notifications</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="settings.notificationSound"
                @change="handleToggle('notificationSound', $event)"
                :disabled="!settings.enableNotifications"
                class="sr-only peer"
              >
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
            </label>
          </div>

          <!-- Ping Interval -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              Default Ping Interval: {{ settings.defaultPingInterval }} minutes
            </label>
            <input
              type="range"
              min="15"
              max="120"
              step="15"
              :value="settings.defaultPingInterval"
              @input="handleRangeChange('defaultPingInterval', $event)"
              class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
            >
            <div class="flex justify-between text-xs text-gray-500 mt-1">
              <span>15 min</span>
              <span>45 min</span>
              <span>120 min</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Background Sync Section -->
      <section>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Synchronization</h3>
        <div class="space-y-4">
          <!-- Sync on Startup -->
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700">Sync on Startup</label>
              <p class="text-sm text-gray-500">Automatically sync GitHub and Calendar when app starts</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="settings.syncOnStartup"
                @change="handleToggle('syncOnStartup', $event)"
                class="sr-only peer"
              >
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>

          <!-- Background Sync -->
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700">Background Sync</label>
              <p class="text-sm text-gray-500">
                Periodically sync data in the background
                <span v-if="!featureSupport.periodicSync" class="text-red-600">(Not supported)</span>
              </p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="settings.backgroundSync"
                @change="handleBackgroundSyncToggle($event)"
                :disabled="!featureSupport.periodicSync"
                class="sr-only peer"
              >
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600 peer-disabled:opacity-50"></div>
            </label>
          </div>
        </div>
      </section>

      <!-- UI Preferences Section -->
      <section>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Appearance</h3>
        <div class="space-y-4">
          <!-- Theme -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Theme</label>
            <select
              :value="settings.theme"
              @change="handleSelectChange('theme', $event)"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>

          <!-- Compact Mode -->
          <div class="flex items-center justify-between">
            <div class="flex-1">
              <label class="text-sm font-medium text-gray-700">Compact Mode</label>
              <p class="text-sm text-gray-500">Use smaller spacing and fonts</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                :checked="settings.compactMode"
                @change="handleToggle('compactMode', $event)"
                class="sr-only peer"
              >
              <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </section>

      <!-- Data Management Section -->
      <section>
        <h3 class="text-lg font-medium text-gray-900 mb-4">Data Management</h3>
        <div class="space-y-4">
          <!-- Database Info -->
          <div v-if="appInfo" class="bg-gray-50 rounded-lg p-4">
            <div class="grid grid-cols-3 gap-4 text-center">
              <div>
                <p class="text-2xl font-bold text-gray-900">{{ appInfo.database.pingCount }}</p>
                <p class="text-sm text-gray-600">Pings</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-gray-900">{{ appInfo.database.todoCount }}</p>
                <p class="text-sm text-gray-600">TODOs</p>
              </div>
              <div>
                <p class="text-2xl font-bold text-gray-900">{{ formatDatabaseSize }}</p>
                <p class="text-sm text-gray-600">Storage</p>
              </div>
            </div>
          </div>

          <!-- Export/Import -->
          <div class="flex gap-3">
            <button
              @click="handleExport"
              :disabled="isLoading"
              class="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span v-if="!isLoading">Export All Data</span>
              <span v-else>Exporting...</span>
            </button>
            <button
              @click="handleImportClick"
              :disabled="isLoading"
              class="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Import Data
            </button>
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              @change="handleImportFile"
              class="hidden"
            >
          </div>

          <!-- Clear Data -->
          <div class="border-t border-gray-200 pt-4">
            <p class="text-sm font-medium text-gray-700 mb-3">Clear Data</p>
            <div class="flex gap-3">
              <button
                @click="handleClearPings"
                :disabled="isLoading"
                class="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
              >
                Clear Pings
              </button>
              <button
                @click="handleClearTodos"
                :disabled="isLoading"
                class="flex-1 px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 disabled:opacity-50"
              >
                Clear TODOs
              </button>
              <button
                @click="handleClearAll"
                :disabled="isLoading"
                class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- About Section -->
      <section v-if="appInfo">
        <h3 class="text-lg font-medium text-gray-900 mb-4">About</h3>
        <div class="space-y-3">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Version</span>
            <span class="font-medium text-gray-900">{{ appInfo.version }}</span>
          </div>
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">Build Date</span>
            <span class="font-medium text-gray-900">{{ appInfo.buildDate }}</span>
          </div>

          <!-- Feature Support -->
          <div class="border-t border-gray-200 pt-3">
            <p class="text-sm font-medium text-gray-700 mb-2">Browser Features</p>
            <div class="grid grid-cols-2 gap-2">
              <div class="flex items-center gap-2">
                <span class="text-lg" :class="appInfo.features.notifications ? 'text-green-600' : 'text-red-600'">
                  {{ appInfo.features.notifications ? '✓' : '✗' }}
                </span>
                <span class="text-sm text-gray-600">Notifications</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-lg" :class="appInfo.features.serviceWorker ? 'text-green-600' : 'text-red-600'">
                  {{ appInfo.features.serviceWorker ? '✓' : '✗' }}
                </span>
                <span class="text-sm text-gray-600">Service Worker</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-lg" :class="appInfo.features.periodicSync ? 'text-green-600' : 'text-red-600'">
                  {{ appInfo.features.periodicSync ? '✓' : '✗' }}
                </span>
                <span class="text-sm text-gray-600">Periodic Sync</span>
              </div>
              <div class="flex items-center gap-2">
                <span class="text-lg" :class="appInfo.features.backgroundSync ? 'text-green-600' : 'text-red-600'">
                  {{ appInfo.features.backgroundSync ? '✓' : '✗' }}
                </span>
                <span class="text-sm text-gray-600">Background Sync</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Reset Settings -->
      <section class="border-t border-gray-200 pt-6">
        <button
          @click="handleReset"
          :disabled="isLoading"
          class="w-full px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50"
        >
          Reset All Settings
        </button>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSettings } from '../../composables/useSettings';

const {
  settings,
  appInfo,
  isLoading,
  error,
  notificationPermission,
  formatDatabaseSize,
  featureSupport,
  updateSettings,
  resetSettings,
  requestNotificationPermission,
  exportAllData,
  importData,
  clearAllData,
  clearData,
  toggleBackgroundSync
} = useSettings();

const fileInput = ref<HTMLInputElement | null>(null);

// Event handlers
const handleToggle = (key: string, event: Event) => {
  const target = event.target as HTMLInputElement;
  updateSettings({ [key]: target.checked });
};

const handleRangeChange = (key: string, event: Event) => {
  const target = event.target as HTMLInputElement;
  updateSettings({ [key]: parseInt(target.value, 10) });
};

const handleSelectChange = (key: string, event: Event) => {
  const target = event.target as HTMLSelectElement;
  updateSettings({ [key]: target.value });
};

const handleRequestPermission = async () => {
  try {
    await requestNotificationPermission();
  } catch (err) {
    console.error('Permission request failed:', err);
  }
};

const handleBackgroundSyncToggle = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  await toggleBackgroundSync(target.checked);
};

const handleExport = async () => {
  await exportAllData();
};

const handleImportClick = () => {
  fileInput.value?.click();
};

const handleImportFile = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (file) {
    try {
      const result = await importData(file);

      // Build detailed message
      let message = '';

      if (result.hasErrors) {
        message = '⚠️ Import completed with errors!\n\n';
        message += `Pings: ${result.pings.imported}/${result.pings.total} imported`;
        if (result.pings.failed > 0) {
          message += ` (${result.pings.failed} failed)`;
        }
        message += `\nTODOs: ${result.todos.imported}/${result.todos.total} imported`;
        if (result.todos.failed > 0) {
          message += ` (${result.todos.failed} failed)`;
        }

        // Show first few errors
        if (result.errors.length > 0) {
          message += '\n\nFirst errors:';
          const errorPreview = result.errors.slice(0, 5);
          errorPreview.forEach(err => {
            const recordType = err.type.toUpperCase();
            const recordId = err.id ? ` (${err.id})` : ` #${err.index + 1}`;
            message += `\n• ${recordType}${recordId}: ${err.error}`;
          });

          if (result.errors.length > 5) {
            message += `\n... and ${result.errors.length - 5} more errors`;
          }
        }

        message += '\n\nCheck browser console for full error details.';
      } else {
        message = '✓ Import successful!\n\n';
        message += `Pings: ${result.pings.imported} imported\n`;
        message += `TODOs: ${result.todos.imported} imported`;
      }

      alert(message);
    } catch (err) {
      console.error('Import failed:', err);
    }

    // Reset file input
    target.value = '';
  }
};

const handleClearPings = async () => {
  await clearData('pings');
};

const handleClearTodos = async () => {
  await clearData('todos');
};

const handleClearAll = async () => {
  await clearAllData();
};

const handleReset = () => {
  resetSettings();
};
</script>
