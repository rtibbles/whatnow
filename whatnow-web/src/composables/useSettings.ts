/**
 * Settings Composable
 *
 * Provides reactive access to app settings and data management functions.
 */

import { ref, onMounted, onUnmounted, computed } from 'vue';
import { settingsService, type AppSettings, type AppInfo } from '../services/settings';
import { ExportService } from '../services/export';

export function useSettings() {
  // Reactive state
  const settings = ref<AppSettings>(settingsService.getSettings());
  const appInfo = ref<AppInfo | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Feature support
  const supportsNotifications = computed(() => 'Notification' in window);
  const notificationPermission = ref<NotificationPermission>(
    supportsNotifications.value ? Notification.permission : 'denied'
  );

  // Subscribe to settings changes
  let unsubscribe: (() => void) | null = null;

  onMounted(() => {
    unsubscribe = settingsService.subscribe((newSettings) => {
      settings.value = newSettings;
    });

    // Load app info
    loadAppInfo();
  });

  onUnmounted(() => {
    if (unsubscribe) {
      unsubscribe();
    }
  });

  /**
   * Load app information
   */
  const loadAppInfo = async () => {
    try {
      appInfo.value = await settingsService.getAppInfo();
    } catch (err) {
      console.error('Failed to load app info:', err);
    }
  };

  /**
   * Update settings
   */
  const updateSettings = (updates: Partial<AppSettings>) => {
    try {
      settingsService.updateSettings(updates);
      error.value = null;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to update settings';
      console.error('Settings update error:', err);
    }
  };

  /**
   * Reset settings to defaults
   */
  const resetSettings = () => {
    if (confirm('Reset all settings to defaults? This cannot be undone.')) {
      try {
        settingsService.resetSettings();
        error.value = null;
      } catch (err) {
        error.value = err instanceof Error ? err.message : 'Failed to reset settings';
        console.error('Settings reset error:', err);
      }
    }
  };

  /**
   * Request notification permission
   */
  const requestNotificationPermission = async () => {
    try {
      const permission = await settingsService.requestNotificationPermission();
      notificationPermission.value = permission;

      if (permission === 'granted') {
        updateSettings({ enableNotifications: true });
      }

      return permission;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to request permission';
      throw err;
    }
  };

  /**
   * Export all data
   */
  const exportAllData = async () => {
    isLoading.value = true;
    error.value = null;

    try {
      const jsonData = await settingsService.exportAllData();
      const timestamp = new Date().toISOString().split('T')[0];
      const filename = `whatnow-backup-${timestamp}.json`;

      ExportService.downloadFile(jsonData, filename, 'application/json');
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Export failed';
      console.error('Export error:', err);
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Import data from file
   */
  const importData = async (file: File) => {
    isLoading.value = true;
    error.value = null;

    try {
      const text = await file.text();
      const result = await settingsService.importData(text);

      // Reload app info to reflect new data
      await loadAppInfo();

      return result;
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Import failed';
      console.error('Import error:', err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Clear all data
   */
  const clearAllData = async () => {
    const confirmed = confirm(
      'Clear all pings and TODOs? This cannot be undone.\n\n' +
      'Consider exporting your data first.'
    );

    if (!confirmed) {
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      await settingsService.clearAllData();

      // Reload app info
      await loadAppInfo();
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to clear data';
      console.error('Clear data error:', err);
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Clear specific data type
   */
  const clearData = async (type: 'pings' | 'todos') => {
    const typeLabel = type === 'pings' ? 'all pings' : 'all TODOs';
    const confirmed = confirm(
      `Clear ${typeLabel}? This cannot be undone.\n\n` +
      'Consider exporting your data first.'
    );

    if (!confirmed) {
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      await settingsService.clearData(type);

      // Reload app info
      await loadAppInfo();
    } catch (err) {
      error.value = err instanceof Error ? err.message : `Failed to clear ${type}`;
      console.error(`Clear ${type} error:`, err);
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Enable/disable background sync
   */
  const toggleBackgroundSync = async (enabled: boolean) => {
    // Prevent concurrent calls
    if (isLoading.value) {
      console.warn('Background sync toggle already in progress');
      return;
    }

    isLoading.value = true;
    error.value = null;

    try {
      if (enabled) {
        const success = await settingsService.scheduleBackgroundSync();
        if (success) {
          updateSettings({ backgroundSync: true });
        } else {
          error.value = 'Background sync not supported by this browser';
          updateSettings({ backgroundSync: false });
        }
      } else {
        await settingsService.unregisterBackgroundSync();
        updateSettings({ backgroundSync: false });
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Failed to toggle background sync';
      console.error('Background sync error:', err);
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * Format database size for display
   */
  const formatDatabaseSize = computed(() => {
    return appInfo.value?.database.databaseSize || 'Unknown';
  });

  /**
   * Get feature support status
   */
  const featureSupport = computed(() => {
    return appInfo.value?.features || {
      notifications: false,
      periodicSync: false,
      backgroundSync: false,
      serviceWorker: false
    };
  });

  return {
    // State
    settings,
    appInfo,
    isLoading,
    error,
    notificationPermission,

    // Computed
    supportsNotifications,
    formatDatabaseSize,
    featureSupport,

    // Methods
    updateSettings,
    resetSettings,
    requestNotificationPermission,
    exportAllData,
    importData,
    clearAllData,
    clearData,
    toggleBackgroundSync,
    loadAppInfo
  };
}
