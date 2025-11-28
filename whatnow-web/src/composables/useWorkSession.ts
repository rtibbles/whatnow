import { ref, computed, onMounted } from 'vue';
import { getDatabase } from '../db/database';
import type { WorkSessionDocument } from '../db/schemas/work-session.schema';

/**
 * Composable for managing work sessions
 */
export function useWorkSession() {
  const currentSession = ref<WorkSessionDocument | null>(null);
  const isActive = computed(() => currentSession.value !== null && currentSession.value.endTime === null);

  /**
   * Start a new work session
   */
  const startSession = async (): Promise<WorkSessionDocument> => {
    const db = await getDatabase();

    const session: WorkSessionDocument = {
      id: crypto.randomUUID(),
      startTime: Date.now(),
      endTime: null,
      totalSeconds: 0
    };

    await db.work_sessions.insert(session);
    currentSession.value = session;

    return session;
  };

  /**
   * End the current work session
   */
  const endSession = async (): Promise<void> => {
    if (!currentSession.value) return;

    const db = await getDatabase();
    const endTime = Date.now();
    const totalSeconds = Math.floor((endTime - currentSession.value.startTime) / 1000);

    const doc = await db.work_sessions
      .findOne({ selector: { id: currentSession.value.id } })
      .exec();

    if (doc) {
      await doc.update({
        $set: {
          endTime,
          totalSeconds
        }
      });
    }

    currentSession.value = null;
  };

  /**
   * Load active session on mount (if exists)
   */
  const loadActiveSession = async (): Promise<void> => {
    const db = await getDatabase();

    const session = await db.work_sessions
      .findOne({
        selector: {
          endTime: null
        },
        sort: [{ startTime: 'desc' }]
      })
      .exec();

    if (session) {
      currentSession.value = session.toJSON();
    }
  };

  /**
   * Get current session duration in seconds
   */
  const getCurrentDuration = computed(() => {
    if (!currentSession.value) return 0;
    return Math.floor((Date.now() - currentSession.value.startTime) / 1000);
  });

  onMounted(() => {
    loadActiveSession();
  });

  return {
    currentSession,
    isActive,
    startSession,
    endSession,
    getCurrentDuration
  };
}
