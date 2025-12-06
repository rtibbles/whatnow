import { getDatabase } from '../db/database';

export interface PingSchedule {
  sessionId: string;
  workSessionId: string;
  startTime: number;
  averageGapMinutes: number;
  schedule: number[];          // Array of timestamps
  completedPings: Set<number>; // Pings user responded to
  missedPings: Set<number>;    // Pings that triggered but user didn't respond
  nextPingIndex: number;       // Next ping to trigger
}

/**
 * Generate Poisson-distributed ping schedule
 * Uses exponential distribution: interval = -ln(U) × λ
 */
export function generatePingSchedule(
  startTime: number,
  count: number,
  averageGapMinutes: number
): number[] {
  const schedule: number[] = [];
  let currentTime = startTime;
  const lambdaSeconds = averageGapMinutes * 60;

  for (let i = 0; i < count; i++) {
    // Exponential distribution
    const u = Math.random();
    const intervalSeconds = -Math.log(u) * lambdaSeconds;
    currentTime += intervalSeconds * 1000; // Convert to ms
    schedule.push(Math.floor(currentTime));
  }

  return schedule;
}

/**
 * Calculate statistics for a schedule (for testing)
 */
export function calculateScheduleStats(schedule: number[]): {
  averageGapMinutes: number;
  minGapMinutes: number;
  maxGapMinutes: number;
  totalDurationHours: number;
} {
  if (schedule.length < 2) {
    throw new Error('Schedule must have at least 2 pings to calculate statistics');
  }

  const gaps: number[] = [];

  for (let i = 1; i < schedule.length; i++) {
    const gapMs = schedule[i]! - schedule[i - 1]!;
    gaps.push(gapMs / 1000 / 60); // Convert to minutes
  }

  return {
    averageGapMinutes: gaps.reduce((a, b) => a + b, 0) / gaps.length,
    minGapMinutes: Math.min(...gaps),
    maxGapMinutes: Math.max(...gaps),
    totalDurationHours: (schedule[schedule.length - 1]! - schedule[0]!) / 1000 / 60 / 60
  };
}

export class PingScheduler {
  private currentSchedule: PingSchedule | null = null;
  private activeTimer: number | null = null;

  /**
   * Start a new work session with ping schedule
   */
  async startWorkSession(
    workSessionId: string,
    averageGapMinutes: number = 45
  ): Promise<PingSchedule> {
    const now = Date.now();

    // Generate schedule for ~30 hours (enough for a full day + buffer)
    const pingCount = Math.ceil((30 * 60) / averageGapMinutes);
    const schedule = generatePingSchedule(now, pingCount, averageGapMinutes);

    this.currentSchedule = {
      sessionId: crypto.randomUUID(),
      workSessionId,
      startTime: now,
      averageGapMinutes,
      schedule,
      completedPings: new Set(),
      missedPings: new Set(),
      nextPingIndex: 0
    };

    // Save to database
    await this.saveSchedule();

    // Setup notification strategy
    await this.setupNotifications();

    return this.currentSchedule;
  }

  /**
   * Progressive enhancement: use best available API
   */
  private async setupNotifications(): Promise<void> {
    if (!this.currentSchedule) return;

    // Strategy 1: Scheduled Notifications (Chrome 83+)
    if (this.supportsScheduledNotifications()) {
      await this.scheduleNotificationTriggers();
      console.log('✅ Using Scheduled Notifications API');
    }

    // Strategy 2: Active timer (always, for precise timing when tab open)
    this.startActiveTimer();

    // Strategy 3: Periodic checks via service worker
    if (this.supportsPeriodicBackgroundSync()) {
      await this.registerPeriodicSync();
    }
  }

  /**
   * Feature detection
   */
  private supportsScheduledNotifications(): boolean {
    return 'showTrigger' in Notification.prototype;
  }

  private supportsPeriodicBackgroundSync(): boolean {
    return 'serviceWorker' in navigator &&
           'periodicSync' in ServiceWorkerRegistration.prototype;
  }

  /**
   * Schedule notifications using Notification Trigger API (Chrome)
   */
  private async scheduleNotificationTriggers(): Promise<void> {
    if (!this.currentSchedule) return;

    try {
      const registration = await navigator.serviceWorker.ready;
      const { schedule, completedPings, nextPingIndex } = this.currentSchedule;

      // Schedule all future pings
      for (let i = nextPingIndex; i < schedule.length; i++) {
        const pingTime = schedule[i];
        if (!pingTime) continue;

        if (pingTime <= Date.now()) continue; // Already passed
        if (completedPings.has(i)) continue;  // Already completed

        // @ts-expect-error - TypeScript doesn't have types for Scheduled Notifications API yet
        await registration.showNotification('WhatNow Ping!', {
          body: 'What are you working on?',
          tag: `ping-${this.currentSchedule.sessionId}-${i}`,
          icon: '/icon-192.png',
          badge: '/badge-72.png',
          // @ts-expect-error - TypeScript doesn't have types for this yet
          showTrigger: new TimestampTrigger(pingTime),
          requireInteraction: true,
          actions: [
            { action: 'log', title: 'Log Activity', icon: '/action-log.png' },
            { action: 'snooze', title: 'Snooze 5min', icon: '/action-snooze.png' }
          ],
          data: {
            type: 'ping',
            sessionId: this.currentSchedule.sessionId,
            pingIndex: i,
            pingTime
          }
        });
      }
    } catch (error) {
      console.log('⚠️ Scheduled Notifications API failed (will use active timer instead):', error);
      // Graceful degradation - active timer will handle pings
    }
  }

  /**
   * Active timer for precise timing when tab is open
   */
  private startActiveTimer(): void {
    if (!this.currentSchedule) return;

    // Clear existing timer
    if (this.activeTimer) {
      clearTimeout(this.activeTimer);
    }

    const now = Date.now();
    const { schedule, nextPingIndex, completedPings } = this.currentSchedule;

    // Find next uncompleted ping
    let nextIndex = nextPingIndex;
    while (nextIndex < schedule.length && completedPings.has(nextIndex)) {
      nextIndex++;
    }

    if (nextIndex >= schedule.length) {
      console.log('All pings completed or no more pings in schedule');
      return;
    }

    const nextPingTime = schedule[nextIndex];
    if (!nextPingTime) {
      console.log('Invalid ping time');
      return;
    }

    const delay = nextPingTime - now;

    if (delay <= 0) {
      // Ping is due now
      this.triggerPing(nextIndex);
    } else {
      // Schedule next ping
      this.activeTimer = window.setTimeout(() => {
        this.triggerPing(nextIndex);
      }, delay);

      const minutes = Math.floor(delay / 1000 / 60);
      const seconds = Math.floor((delay / 1000) % 60);
      console.log(`⏰ Next ping #${nextIndex} scheduled in ${minutes}m ${seconds}s (at ${new Date(nextPingTime).toLocaleTimeString()})`);
    }
  }

  /**
   * Trigger a ping (show dialog or notification)
   */
  private async triggerPing(pingIndex: number): Promise<void> {
    if (!this.currentSchedule) return;

    const pingTime = this.currentSchedule.schedule[pingIndex];
    if (!pingTime) return;

    console.log(`🔔 PING #${pingIndex} triggered! Time: ${new Date(pingTime).toLocaleTimeString()}`);

    // Update next ping index
    this.currentSchedule.nextPingIndex = pingIndex + 1;
    await this.saveSchedule();

    // Emit event for UI to show dialog
    window.dispatchEvent(new CustomEvent('whatnow:ping', {
      detail: {
        sessionId: this.currentSchedule.sessionId,
        pingIndex,
        pingTime
      }
    }));

    console.log(`📤 Emitted 'whatnow:ping' event for ping #${pingIndex}`);

    // If tab is hidden, show notification
    if (document.hidden) {
      await this.showPingNotification(pingIndex, pingTime);
    }

    // Schedule next ping
    this.startActiveTimer();
  }

  /**
   * Show notification for ping (when tab is hidden)
   */
  private async showPingNotification(pingIndex: number, pingTime: number): Promise<void> {
    if (!this.currentSchedule) return;

    if (Notification.permission === 'granted') {
      new Notification('WhatNow Ping!', {
        body: 'What are you working on?',
        tag: `ping-${this.currentSchedule.sessionId}-${pingIndex}`,
        requireInteraction: true,
        data: {
          type: 'ping',
          sessionId: this.currentSchedule.sessionId,
          pingIndex,
          pingTime
        }
      });
    }
  }

  /**
   * Register periodic background sync
   */
  private async registerPeriodicSync(): Promise<void> {
    if (!('serviceWorker' in navigator)) return;

    try {
      const registration = await navigator.serviceWorker.ready;

      // @ts-expect-error - TypeScript doesn't have full types for periodicSync
      if ('periodicSync' in registration) {
        // @ts-expect-error - periodicSync not in ServiceWorkerRegistration types
        await registration.periodicSync.register('check-ping-schedule', {
          minInterval: 15 * 60 * 1000 // Request every 15 minutes (browser decides actual interval)
        });
        console.log('✅ Registered Periodic Background Sync');
      }
    } catch (error) {
      // This is expected in non-PWA contexts or browsers without support
      console.log('⚠️ Periodic sync not available (will use active timer instead)');
    }
  }

  /**
   * Mark ping as completed
   */
  async completePing(pingIndex: number): Promise<void> {
    if (!this.currentSchedule) return;

    this.currentSchedule.completedPings.add(pingIndex);
    await this.saveSchedule();
  }

  /**
   * Mark ping as missed
   */
  async markPingMissed(pingIndex: number): Promise<void> {
    if (!this.currentSchedule) return;

    this.currentSchedule.missedPings.add(pingIndex);
    await this.saveSchedule();
  }

  /**
   * Get missed pings since last check
   */
  getMissedPings(): Array<{ index: number; time: number }> {
    if (!this.currentSchedule) return [];

    const now = Date.now();
    const missed: Array<{ index: number; time: number }> = [];

    for (let i = 0; i < this.currentSchedule.schedule.length; i++) {
      const pingTime = this.currentSchedule.schedule[i];
      if (!pingTime) continue;

      if (pingTime > now) break; // Future pings
      if (this.currentSchedule.completedPings.has(i)) continue; // Completed
      if (this.currentSchedule.missedPings.has(i)) continue; // Already marked as missed

      // This ping is in the past and not completed
      missed.push({ index: i, time: pingTime });
    }

    return missed;
  }

  /**
   * Pause scheduler (e.g., when tab hidden)
   */
  pause(): void {
    if (this.activeTimer) {
      clearTimeout(this.activeTimer);
      this.activeTimer = null;
    }
  }

  /**
   * Resume scheduler (e.g., when tab visible again)
   */
  resume(): void {
    this.startActiveTimer();
  }

  /**
   * End work session
   */
  async endWorkSession(): Promise<void> {
    this.pause();
    this.currentSchedule = null;

    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'current_ping_schedule' } })
      .exec();

    if (config) {
      await config.remove();
    }
  }

  /**
   * Persist schedule to database
   */
  private async saveSchedule(): Promise<void> {
    if (!this.currentSchedule) return;

    try {
      const db = await getDatabase();

      await db.config.upsert({
        key: 'current_ping_schedule',
        value: {
          ...this.currentSchedule,
          completedPings: Array.from(this.currentSchedule.completedPings),
          missedPings: Array.from(this.currentSchedule.missedPings)
        },
        updatedAt: Date.now()
      });
    } catch (error) {
      console.error('Failed to save ping schedule:', error);
      // Schedule will be lost if this fails, but app can continue
    }
  }

  /**
   * Load schedule from database (on app start)
   */
  async loadSchedule(): Promise<boolean> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'current_ping_schedule' } })
      .exec();

    if (!config) return false;

    const data = config.value;
    this.currentSchedule = {
      ...data,
      completedPings: new Set(Array.isArray(data.completedPings) ? data.completedPings : []),
      missedPings: new Set(Array.isArray(data.missedPings) ? data.missedPings : [])
    };

    // Resume notifications
    await this.setupNotifications();

    return true;
  }

  /**
   * Get current schedule
   */
  getCurrentSchedule(): PingSchedule | null {
    return this.currentSchedule;
  }

  /**
   * Get next ping time
   */
  getNextPingTime(): number | null {
    if (!this.currentSchedule) return null;

    const { schedule, nextPingIndex, completedPings } = this.currentSchedule;

    // Find next uncompleted ping
    let nextIndex = nextPingIndex;
    while (nextIndex < schedule.length && completedPings.has(nextIndex)) {
      nextIndex++;
    }

    if (nextIndex >= schedule.length) return null;

    return schedule[nextIndex] ?? null;
  }
}
