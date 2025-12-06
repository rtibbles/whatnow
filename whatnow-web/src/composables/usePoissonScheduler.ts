import { ref, onMounted, onUnmounted, watch } from 'vue';
import { PingScheduler } from '../services/poisson-scheduler';
import { useWorkSession } from './useWorkSession';
import { useVisibility } from './useVisibility';

/**
 * Composable for managing the Poisson ping scheduler
 */
export function usePoissonScheduler() {
  const scheduler = new PingScheduler();
  const { currentSession } = useWorkSession();
  const { isVisible } = useVisibility();

  const isActive = ref(false);
  const nextPingTime = ref<number | null>(null);
  const missedPingCount = ref(0);
  const missedPings = ref<Array<{ index: number; time: number }>>([]);
  const currentPingIndex = ref<number | null>(null);
  const currentPingTime = ref<number | null>(null);
  const showPingDialog = ref(false);
  const showMissedPingsDialog = ref(false);

  // Handle ping events from scheduler
  const handlePingEvent = (event: Event) => {
    const customEvent = event as CustomEvent;
    const { pingIndex, pingTime } = customEvent.detail;

    console.log(`📥 usePoissonScheduler received ping event #${pingIndex}, showing dialog`);

    currentPingIndex.value = pingIndex;
    currentPingTime.value = pingTime;
    showPingDialog.value = true;

    console.log(`✅ Dialog state updated: showPingDialog=${showPingDialog.value}, pingIndex=${pingIndex}`);

    // Update next ping time
    updateNextPingTime();
  };

  // Auto-pause/resume based on visibility
  watch(isVisible, (visible) => {
    if (!isActive.value) return;

    if (visible) {
      scheduler.resume();
      checkForMissedPings();
      updateNextPingTime();
    } else {
      scheduler.pause();
    }
  });

  // Check for missed pings when returning to app
  const checkForMissedPings = () => {
    const missed = scheduler.getMissedPings();
    missedPingCount.value = missed.length;
    missedPings.value = missed;

    if (missed.length > 0) {
      showMissedPingsDialog.value = true;
    }
  };

  // Update next ping time
  const updateNextPingTime = () => {
    nextPingTime.value = scheduler.getNextPingTime();
  };

  // Start scheduler with work session
  const start = async (workSessionId: string, averageGapMinutes: number = 45) => {
    await scheduler.startWorkSession(workSessionId, averageGapMinutes);
    isActive.value = true;
    updateNextPingTime();
  };

  // Stop scheduler
  const stop = async () => {
    await scheduler.endWorkSession();
    isActive.value = false;
    nextPingTime.value = null;
    currentPingIndex.value = null;
    showPingDialog.value = false;
  };

  // Mark ping as completed
  const completePing = async (pingIndex: number) => {
    await scheduler.completePing(pingIndex);
    missedPingCount.value = scheduler.getMissedPings().length;
    updateNextPingTime();

    if (currentPingIndex.value === pingIndex) {
      showPingDialog.value = false;
      currentPingIndex.value = null;
    }
  };

  // Mark ping as missed
  const markPingMissed = async (pingIndex: number) => {
    await scheduler.markPingMissed(pingIndex);
    missedPingCount.value = scheduler.getMissedPings().length;
    updateNextPingTime();

    if (currentPingIndex.value === pingIndex) {
      showPingDialog.value = false;
      currentPingIndex.value = null;
    }
  };

  // Dismiss ping dialog
  const dismissPing = () => {
    showPingDialog.value = false;
    currentPingIndex.value = null;
    currentPingTime.value = null;
  };

  // Complete multiple missed pings
  const completeMissedPings = async (pingIndices: number[]) => {
    for (const index of pingIndices) {
      await scheduler.completePing(index);
    }
    missedPingCount.value = scheduler.getMissedPings().length;
    missedPings.value = scheduler.getMissedPings();
    showMissedPingsDialog.value = false;
    updateNextPingTime();
  };

  // Dismiss missed pings dialog
  const dismissMissedPings = async () => {
    // Mark all as missed
    for (const ping of missedPings.value) {
      await scheduler.markPingMissed(ping.index);
    }
    missedPingCount.value = 0;
    missedPings.value = [];
    showMissedPingsDialog.value = false;
    updateNextPingTime();
  };

  // Request notification permission
  const requestNotificationPermission = async (): Promise<NotificationPermission> => {
    if (!('Notification' in window)) {
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission !== 'denied') {
      const permission = await Notification.requestPermission();
      return permission;
    }

    return Notification.permission;
  };

  // Load existing schedule on mount
  onMounted(async () => {
    const loaded = await scheduler.loadSchedule();
    if (loaded) {
      isActive.value = true;
      checkForMissedPings();
      updateNextPingTime();
    }

    window.addEventListener('whatnow:ping', handlePingEvent);
  });

  onUnmounted(() => {
    window.removeEventListener('whatnow:ping', handlePingEvent);
  });

  return {
    isActive,
    nextPingTime,
    missedPingCount,
    missedPings,
    currentPingIndex,
    currentPingTime,
    showPingDialog,
    showMissedPingsDialog,
    start,
    stop,
    completePing,
    completeMissedPings,
    markPingMissed,
    dismissPing,
    dismissMissedPings,
    checkForMissedPings,
    requestNotificationPermission
  };
}
