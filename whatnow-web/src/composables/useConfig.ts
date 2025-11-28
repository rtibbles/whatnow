import { ref } from 'vue';
import { getDatabase } from '../db/database';
import type { ConfigDocument } from '../db/schemas/config.schema';

/**
 * Composable for reactive config values
 */
export function useConfig<T = any>(key: string, defaultValue?: T) {
  const value = ref<T | undefined>(defaultValue);
  const loading = ref(true);
  const error = ref<Error | null>(null);

  // Load initial value
  const load = async () => {
    try {
      loading.value = true;
      const db = getDatabase();
      const doc = await db.config.findOne({ selector: { key } }).exec();

      if (doc) {
        value.value = doc.value as T;
      } else {
        value.value = defaultValue;
      }
    } catch (err) {
      console.error(`Failed to load config: ${key}`, err);
      error.value = err as Error;
    } finally {
      loading.value = false;
    }
  };

  // Save value
  const save = async (newValue: T) => {
    try {
      const db = getDatabase();
      await db.config.upsert({
        key,
        value: newValue,
        updatedAt: Date.now()
      });
      value.value = newValue;
    } catch (err) {
      console.error(`Failed to save config: ${key}`, err);
      error.value = err as Error;
      throw err;
    }
  };

  // Remove value
  const remove = async () => {
    try {
      const db = getDatabase();
      const doc = await db.config.findOne({ selector: { key } }).exec();
      if (doc) {
        await doc.remove();
      }
      value.value = defaultValue;
    } catch (err) {
      console.error(`Failed to remove config: ${key}`, err);
      error.value = err as Error;
      throw err;
    }
  };

  // Subscribe to changes
  const subscribe = () => {
    const db = getDatabase();
    const subscription = db.config
      .findOne({ selector: { key } })
      .$.subscribe((doc: ConfigDocument | null) => {
        if (doc) {
          value.value = doc.value as T;
        } else {
          value.value = defaultValue;
        }
      });

    return () => subscription.unsubscribe();
  };

  return {
    value,
    loading,
    error,
    load,
    save,
    remove,
    subscribe
  };
}
