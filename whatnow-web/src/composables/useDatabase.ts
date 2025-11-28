import { ref, onMounted } from 'vue';
import { initDatabase, getDatabase, type WhatNowDatabase } from '../db/database';

const db = ref<WhatNowDatabase | null>(null);
const isInitialized = ref(false);
const initError = ref<Error | null>(null);
let isInitializing = false;

/**
 * Composable for accessing RxDB database
 */
export function useDatabase() {
  const initDb = async () => {
    // Prevent concurrent initialization
    if (isInitializing || isInitialized.value) {
      console.warn('Database initialization already in progress or completed');
      return;
    }

    isInitializing = true;
    try {
      const database = await initDatabase();
      db.value = database;
      isInitialized.value = true;
    } catch (error) {
      console.error('Failed to initialize database:', error);
      initError.value = error as Error;
      throw error;
    } finally {
      isInitializing = false;
    }
  };

  // Auto-initialize on mount
  onMounted(async () => {
    if (!isInitialized.value && !db.value && !isInitializing) {
      await initDb();
    }
  });

  return {
    db,
    isInitialized,
    initError,
    initDb,
    getDb: () => getDatabase()
  };
}
