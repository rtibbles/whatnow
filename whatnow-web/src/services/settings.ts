/**
 * Settings Service
 *
 * Manages application configuration and preferences.
 * Stores settings in localStorage for persistence.
 */

import { getDatabase } from '../db/database';

export interface AppSettings {
  // Ping settings
  defaultPingInterval: number;  // Minutes between ping notifications
  enableNotifications: boolean;
  notificationSound: boolean;

  // Work session defaults
  defaultWorkTags: string[];
  autoStartSessions: boolean;

  // UI preferences
  theme: 'light' | 'dark' | 'auto';
  compactMode: boolean;

  // Data management
  autoBackup: boolean;
  backupFrequency: 'daily' | 'weekly' | 'monthly';

  // Integration settings
  syncOnStartup: boolean;
  backgroundSync: boolean;
}

export interface AppInfo {
  version: string;
  buildDate: string;
  database: {
    pingCount: number;
    todoCount: number;
    databaseSize: string;
  };
  features: {
    notifications: boolean;
    periodicSync: boolean;
    backgroundSync: boolean;
    serviceWorker: boolean;
  };
}

export interface ImportError {
  type: 'ping' | 'todo';
  index: number;
  id?: string;
  error: string;
}

export interface ImportResult {
  pings: {
    total: number;
    imported: number;
    failed: number;
  };
  todos: {
    total: number;
    imported: number;
    failed: number;
  };
  errors: ImportError[];
  hasErrors: boolean;
}

const SETTINGS_STORAGE_KEY = 'whatnow_settings';
const DEFAULT_SETTINGS: AppSettings = {
  defaultPingInterval: 45,
  enableNotifications: true,
  notificationSound: true,
  defaultWorkTags: [],
  autoStartSessions: false,
  theme: 'auto',
  compactMode: false,
  autoBackup: false,
  backupFrequency: 'weekly',
  syncOnStartup: true,
  backgroundSync: true
};

export class SettingsService {
  private settings: AppSettings;
  private listeners: Set<(settings: AppSettings) => void> = new Set();

  constructor() {
    this.settings = this.loadSettings();
  }

  /**
   * Load settings from localStorage
   */
  private loadSettings(): AppSettings {
    try {
      const stored = localStorage.getItem(SETTINGS_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        // Merge with defaults to handle new settings in updates
        return { ...DEFAULT_SETTINGS, ...parsed };
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
    return { ...DEFAULT_SETTINGS };
  }

  /**
   * Save settings to localStorage
   */
  private saveSettings(): void {
    try {
      localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(this.settings));
      this.notifyListeners();
    } catch (error) {
      console.error('Failed to save settings:', error);
      throw new Error('Failed to save settings');
    }
  }

  /**
   * Get all current settings
   */
  getSettings(): AppSettings {
    return { ...this.settings };
  }

  /**
   * Update settings (partial update)
   */
  updateSettings(updates: Partial<AppSettings>): void {
    this.settings = { ...this.settings, ...updates };
    this.saveSettings();
  }

  /**
   * Reset settings to defaults
   */
  resetSettings(): void {
    this.settings = { ...DEFAULT_SETTINGS };
    this.saveSettings();
  }

  /**
   * Subscribe to settings changes
   */
  subscribe(callback: (settings: AppSettings) => void): () => void {
    this.listeners.add(callback);
    // Return unsubscribe function
    return () => {
      this.listeners.delete(callback);
    };
  }

  /**
   * Notify all listeners of settings changes
   */
  private notifyListeners(): void {
    this.listeners.forEach(callback => {
      try {
        callback(this.getSettings());
      } catch (error) {
        console.error('Settings listener error:', error);
      }
    });
  }

  /**
   * Get app information and statistics
   */
  async getAppInfo(): Promise<AppInfo> {
    const db = getDatabase();

    // Get database statistics
    const pingCount = await db.pings.count().exec();
    const todoCount = await db.local_todos.count().exec();

    // Estimate database size
    let databaseSize = 'Unknown';
    try {
      if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        if (estimate.usage) {
          const mb = (estimate.usage / (1024 * 1024)).toFixed(2);
          databaseSize = `${mb} MB`;
        }
      }
    } catch (error) {
      console.error('Failed to estimate storage:', error);
    }

    // Check feature support
    const features = {
      notifications: 'Notification' in window,
      periodicSync: 'serviceWorker' in navigator && 'periodicSync' in ServiceWorkerRegistration.prototype,
      backgroundSync: 'serviceWorker' in navigator && 'sync' in ServiceWorkerRegistration.prototype,
      serviceWorker: 'serviceWorker' in navigator
    };

    return {
      version: '1.0.0',
      buildDate: new Date().toISOString().split('T')[0] || '',
      database: {
        pingCount,
        todoCount,
        databaseSize
      },
      features
    };
  }

  /**
   * Export all data as JSON
   */
  async exportAllData(): Promise<string> {
    const db = getDatabase();

    const pings = await db.pings.find().exec();
    const todos = await db.local_todos.find().exec();

    const exportData = {
      version: '1.0.0',
      exportDate: new Date().toISOString(),
      settings: this.getSettings(),
      data: {
        pings: pings.map((p: any) => p.toJSON()),
        todos: todos.map((t: any) => t.toJSON())
      }
    };

    return JSON.stringify(exportData, null, 2);
  }

  /**
   * Import data from JSON
   */
  async importData(jsonData: string): Promise<ImportResult> {
    const db = getDatabase();

    let data: any;
    try {
      data = JSON.parse(jsonData);
    } catch (error) {
      throw new Error('Invalid JSON data');
    }

    if (!data.version || !data.data) {
      throw new Error('Invalid data format');
    }

    // Import settings if present
    if (data.settings) {
      this.updateSettings(data.settings);
    }

    const errors: ImportError[] = [];

    // Import pings
    let pingCount = 0;
    const totalPings = data.data.pings?.length || 0;
    if (data.data.pings && Array.isArray(data.data.pings)) {
      for (let i = 0; i < data.data.pings.length; i++) {
        const ping = data.data.pings[i];
        try {
          await db.pings.upsert(ping);
          pingCount++;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          console.error(`Failed to import ping #${i + 1}:`, errorMsg);
          errors.push({
            type: 'ping',
            index: i,
            id: ping.id,
            error: errorMsg
          });
        }
      }
    }

    // Import todos
    let todoCount = 0;
    const totalTodos = data.data.todos?.length || 0;
    if (data.data.todos && Array.isArray(data.data.todos)) {
      for (let i = 0; i < data.data.todos.length; i++) {
        const todo = data.data.todos[i];
        try {
          await db.local_todos.upsert(todo);
          todoCount++;
        } catch (error) {
          const errorMsg = error instanceof Error ? error.message : String(error);
          console.error(`Failed to import todo #${i + 1}:`, errorMsg);
          errors.push({
            type: 'todo',
            index: i,
            id: todo.id,
            error: errorMsg
          });
        }
      }
    }

    return {
      pings: {
        total: totalPings,
        imported: pingCount,
        failed: totalPings - pingCount
      },
      todos: {
        total: totalTodos,
        imported: todoCount,
        failed: totalTodos - todoCount
      },
      errors,
      hasErrors: errors.length > 0
    };
  }

  /**
   * Clear all database data
   */
  async clearAllData(): Promise<void> {
    const db = getDatabase();

    await db.pings.find().remove();
    await db.local_todos.find().remove();
  }

  /**
   * Clear specific data types
   */
  async clearData(type: 'pings' | 'todos' | 'both'): Promise<void> {
    const db = getDatabase();

    if (type === 'pings' || type === 'both') {
      await db.pings.find().remove();
    }

    if (type === 'todos' || type === 'both') {
      await db.local_todos.find().remove();
    }
  }

  /**
   * Request notification permission
   */
  async requestNotificationPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      throw new Error('Notifications not supported');
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission;
    }

    return Notification.permission;
  }

  /**
   * Schedule periodic background sync (if supported)
   */
  async scheduleBackgroundSync(): Promise<boolean> {
    if (!('serviceWorker' in navigator)) {
      return false;
    }

    try {
      const registration = await navigator.serviceWorker.ready;

      // Check for Periodic Sync support
      if ('periodicSync' in registration) {
        const periodicSync = (registration as any).periodicSync;
        await periodicSync.register('sync-external-data', {
          minInterval: 12 * 60 * 60 * 1000 // 12 hours
        });
        return true;
      }
    } catch (error) {
      console.error('Failed to schedule background sync:', error);
    }

    return false;
  }

  /**
   * Unregister background sync
   */
  async unregisterBackgroundSync(): Promise<void> {
    if (!('serviceWorker' in navigator)) {
      return;
    }

    try {
      const registration = await navigator.serviceWorker.ready;

      if ('periodicSync' in registration) {
        const periodicSync = (registration as any).periodicSync;
        await periodicSync.unregister('sync-external-data');
      }
    } catch (error) {
      console.error('Failed to unregister background sync:', error);
    }
  }
}

// Export singleton instance
export const settingsService = new SettingsService();
