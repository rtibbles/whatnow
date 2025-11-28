# WhatNow Migration Plan: GTK → Vue3 Static Web App

**Updated with Pre-Scheduled Poisson Approach**

---

## Executive Summary

Migrating from GTK3 Python desktop app to Vue3 TypeScript static web app with:
- **Zero backend** - Pure static files
- **Pre-scheduled pings** - Generate schedule upfront, use browser notification APIs
- **Progressive enhancement** - Best experience on Chrome, graceful degradation
- **OAuth 2.1** - PKCE for Google Calendar, Device Flow for GitHub
- **RxDB** - Local-first IndexedDB storage
- **Service Workers** - Background sync and notifications

---

## Architecture Overview

### Current → Target

| Aspect | Current (GTK) | Target (Web) |
|--------|---------------|--------------|
| **Runtime** | Desktop app (Python) | Browser (static SPA) |
| **Storage** | SQLite | RxDB (IndexedDB) |
| **Scheduler** | Background thread | **Pre-generated schedule + browser APIs** |
| **Background** | System tray | **Service Worker + Notification API** |
| **OAuth** | OAuth 2.0 redirect flow | PKCE (Google) + Device Flow (GitHub) |
| **Notifications** | OS native | Web Notifications + Scheduled Notifications |

### Key Innovation: Pre-Scheduled Pings

**Old Approach (Desktop App):**
- Background thread continuously calculates next interval
- Timer runs indefinitely while app is open

**New Approach (Web App):**
1. **Generate entire schedule** when work session starts (next 50 pings)
2. **Store in IndexedDB** - persists across page refreshes
3. **Use browser notification APIs** to trigger at scheduled times
4. **Progressive enhancement** - best API available per browser

**Benefits:**
- ✅ No continuous process needed
- ✅ Works in background (with Scheduled Notifications API)
- ✅ More reliable (survives crashes)
- ✅ Easier to test (deterministic)
- ✅ Can show "upcoming pings" to user

---

## Technology Stack

### Core
- **Vue 3** (Composition API, `<script setup>`)
- **TypeScript** (strict mode)
- **Vite** (build tool, HMR)
- **RxDB 15+** (reactive local database)

### UI
- **Tailwind CSS** (utility-first styling)
- **Headless UI** (`@headlessui/vue` - accessible components)
- **Heroicons** (SVG icons)

### Data & State
- **RxDB** with Dexie.js storage adapter (IndexedDB)
- **No Pinia** - Composition API + RxDB reactivity
- **Day.js** (date manipulation)

### Background Processing
- **Service Workers** (Workbox 7)
- **Scheduled Notifications API** (progressive enhancement)
- **Periodic Background Sync** (fallback)
- **Comlink** (Web Worker communication - if needed for heavy tasks)

### OAuth & APIs
- **oauth4webapi** (official OAuth 2.1 library)
- **GitHub GraphQL API** (Apollo Client or fetch)
- **Google Calendar REST API**

### Development
- **Vitest** (unit testing)
- **Playwright** (E2E testing)
- **ESLint + Prettier**
- **TypeScript ESLint**

---

## Browser Compatibility & UX Tiers

### Tier 1: Best Experience (Chrome 83+, Installed PWA)
- ✅ **Scheduled Notifications** - Pings trigger even when browser closed
- ✅ **Periodic Background Sync** - Auto-sync every ~12-24 hours
- ✅ **Notification Actions** - Log activity directly from notification
- ✅ **Offline Support** - Full functionality offline

### Tier 2: Great Experience (Chrome/Edge/Samsung, Installed PWA)
- ✅ **Periodic Background Sync** - Check schedule periodically
- ✅ **Active Timer** - Precise timing when tab open
- ⚠️ **Manual sync** when returning to closed tab
- ✅ **Offline Support**

### Tier 3: Good Experience (Firefox/Safari, Installed PWA)
- ✅ **Active Timer** - Works when tab open
- ⚠️ **Pauses when tab hidden** - Resumes when visible
- ⚠️ **Missed ping summary** - Batch log on return
- ✅ **Offline Support**

### Tier 4: Basic Experience (Any Browser, Not Installed)
- ✅ **Active Timer** - Only when tab visible
- ❌ **No background** - Must keep tab open
- ⚠️ **Limited offline** - No service worker

**Implementation**: Feature detection with graceful fallback

---

## Core Business Logic: Pre-Scheduled Poisson Scheduler

### Schedule Generation (Pure Function)

**`src/services/poisson-scheduler.ts`**
```typescript
export interface PingSchedule {
  sessionId: string;
  workSessionId: number;
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
  const gaps: number[] = [];

  for (let i = 1; i < schedule.length; i++) {
    const gapMs = schedule[i] - schedule[i - 1];
    gaps.push(gapMs / 1000 / 60); // Convert to minutes
  }

  return {
    averageGapMinutes: gaps.reduce((a, b) => a + b, 0) / gaps.length,
    minGapMinutes: Math.min(...gaps),
    maxGapMinutes: Math.max(...gaps),
    totalDurationHours: (schedule[schedule.length - 1] - schedule[0]) / 1000 / 60 / 60
  };
}
```

### Schedule Manager

**`src/services/ping-scheduler.ts` (continued)**
```typescript
export class PingScheduler {
  private currentSchedule: PingSchedule | null = null;
  private activeTimer: number | null = null;
  private checkInterval: number | null = null;

  /**
   * Start a new work session with ping schedule
   */
  async startWorkSession(
    workSessionId: number,
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
      console.log('✅ Registered Periodic Background Sync');
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

    const registration = await navigator.serviceWorker.ready;
    const { schedule, completedPings, nextPingIndex } = this.currentSchedule;

    // Schedule all future pings
    for (let i = nextPingIndex; i < schedule.length; i++) {
      const pingTime = schedule[i];

      if (pingTime <= Date.now()) continue; // Already passed
      if (completedPings.has(i)) continue;  // Already completed

      await registration.showNotification('WhatNow Ping!', {
        body: 'What are you working on?',
        tag: `ping-${this.currentSchedule.sessionId}-${i}`,
        icon: '/icon-192.png',
        badge: '/badge-72.png',
        // @ts-ignore - TypeScript doesn't have types for this yet
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
    const delay = nextPingTime - now;

    if (delay <= 0) {
      // Ping is due now
      this.triggerPing(nextIndex);
    } else {
      // Schedule next ping
      this.activeTimer = window.setTimeout(() => {
        this.triggerPing(nextIndex);
      }, delay);

      console.log(`Next ping in ${Math.round(delay / 1000 / 60)} minutes`);
    }
  }

  /**
   * Trigger a ping (show dialog or notification)
   */
  private async triggerPing(pingIndex: number): Promise<void> {
    if (!this.currentSchedule) return;

    const pingTime = this.currentSchedule.schedule[pingIndex];

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
    const registration = await navigator.serviceWorker.ready;

    try {
      // @ts-ignore - TypeScript doesn't have full types
      await registration.periodicSync.register('check-ping-schedule', {
        minInterval: 15 * 60 * 1000 // Request every 15 minutes (browser decides actual interval)
      });
    } catch (error) {
      console.error('Periodic sync registration failed:', error);
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

    await getDatabase().then(db =>
      db.config.findOne({ selector: { key: 'current_ping_schedule' } })
        .remove()
    );
  }

  /**
   * Persist schedule to database
   */
  private async saveSchedule(): Promise<void> {
    if (!this.currentSchedule) return;

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
      completedPings: new Set(data.completedPings),
      missedPings: new Set(data.missedPings)
    };

    // Resume notifications
    await this.setupNotifications();

    return true;
  }
}
```

---

## Service Worker Implementation

**`src/service-worker.ts`**
```typescript
/// <reference lib="webworker" />
import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst } from 'workbox-strategies';

declare const self: ServiceWorkerGlobalScope;

// Precache app shell
precacheAndRoute(self.__WB_MANIFEST);

// Cache strategies
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({ cacheName: 'images', })
);

registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({ cacheName: 'api-cache' })
);

// ==========================================
// PERIODIC BACKGROUND SYNC
// Checks ping schedule and triggers notifications
// ==========================================

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'check-ping-schedule') {
    event.waitUntil(checkPingSchedule());
  } else if (event.tag === 'sync-external-data') {
    event.waitUntil(syncExternalData());
  }
});

async function checkPingSchedule(): Promise<void> {
  console.log('[Service Worker] Checking ping schedule');

  // Open IndexedDB
  const db = await openIndexedDB();
  const schedule = await getConfig(db, 'current_ping_schedule');

  if (!schedule) {
    console.log('[Service Worker] No active ping schedule');
    return;
  }

  const now = Date.now();
  const { schedule: times, completedPings, missedPings, nextPingIndex } = schedule;

  // Find pings that should have triggered since last check
  const lastCheck = (await getConfig(db, 'last_ping_check'))?.value || schedule.startTime;
  const duePings: Array<{ index: number; time: number }> = [];

  for (let i = nextPingIndex; i < times.length; i++) {
    const pingTime = times[i];

    if (pingTime > now) break; // Future
    if (pingTime < lastCheck) continue; // Already checked
    if (completedPings.includes(i)) continue; // Completed
    if (missedPings.includes(i)) continue; // Already missed

    duePings.push({ index: i, time: pingTime });
  }

  // Show notifications for due pings
  for (const { index, time } of duePings) {
    await self.registration.showNotification('WhatNow Ping!', {
      body: 'What are you working on?',
      tag: `ping-${schedule.sessionId}-${index}`,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      requireInteraction: true,
      timestamp: time,
      actions: [
        { action: 'log', title: 'Log Activity' },
        { action: 'dismiss', title: 'Dismiss' }
      ],
      data: {
        type: 'ping',
        sessionId: schedule.sessionId,
        pingIndex: index,
        pingTime: time
      }
    });
  }

  // Update last check time
  await setConfig(db, 'last_ping_check', now);
}

// ==========================================
// BACKGROUND SYNC (for retry on network restore)
// ==========================================

self.addEventListener('sync', (event) => {
  if (event.tag === 'github-sync') {
    event.waitUntil(syncGitHub());
  } else if (event.tag === 'calendar-sync') {
    event.waitUntil(syncCalendar());
  }
});

async function syncExternalData(): Promise<void> {
  await Promise.all([
    syncGitHub(),
    syncCalendar()
  ]);
}

async function syncGitHub(): Promise<void> {
  console.log('[Service Worker] Syncing GitHub');
  // Import and run GitHub sync
  const { performGitHubSync } = await import('./services/github/sync.js');
  await performGitHubSync();
}

async function syncCalendar(): Promise<void> {
  console.log('[Service Worker] Syncing Calendar');
  const { performCalendarSync } = await import('./services/google-calendar/sync.js');
  await performCalendarSync();
}

// ==========================================
// NOTIFICATION CLICK HANDLERS
// ==========================================

self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const data = event.notification.data;

  if (data.type === 'ping') {
    if (event.action === 'log') {
      // Open app to ping dialog
      event.waitUntil(
        self.clients.openWindow(`/?ping=${data.pingIndex}&session=${data.sessionId}`)
      );
    } else if (event.action === 'dismiss') {
      // Mark as missed
      event.waitUntil(markPingAsMissed(data.sessionId, data.pingIndex));
    } else {
      // No action (clicked notification body)
      event.waitUntil(
        self.clients.openWindow('/')
      );
    }
  }
});

async function markPingAsMissed(sessionId: string, pingIndex: number): Promise<void> {
  const db = await openIndexedDB();
  const schedule = await getConfig(db, 'current_ping_schedule');

  if (schedule && schedule.sessionId === sessionId) {
    schedule.missedPings.push(pingIndex);
    await setConfig(db, 'current_ping_schedule', schedule);
  }
}

// ==========================================
// INDEXEDDB HELPERS
// (Service worker can't use RxDB, need direct IndexedDB access)
// ==========================================

function openIndexedDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('whatnow', 1);
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function getConfig(db: IDBDatabase, key: string): Promise<any> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['config'], 'readonly');
    const store = tx.objectStore('config');
    const request = store.get(key);

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function setConfig(db: IDBDatabase, key: string, value: any): Promise<void> {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(['config'], 'readwrite');
    const store = tx.objectStore('config');
    const request = store.put({ key, value, updatedAt: Date.now() });

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// ==========================================
// PUSH NOTIFICATIONS (future feature)
// ==========================================

self.addEventListener('push', (event) => {
  const data = event.data?.json();

  event.waitUntil(
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: '/icon-192.png',
      badge: '/badge-72.png',
      tag: data.tag,
      data: data.data
    })
  );
});
```

---

## OAuth Implementation with oauth4webapi

### Google Calendar (PKCE Flow)

**`src/services/google-calendar/oauth.ts`**
```typescript
import * as oauth from 'oauth4webapi';
import { getDatabase } from '../../db/database';

export class GoogleCalendarOAuth {
  private readonly issuer = new URL('https://accounts.google.com');
  private readonly clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  private readonly redirectUri = window.location.origin + window.location.pathname;
  private readonly scopes = ['https://www.googleapis.com/auth/calendar.readonly'];

  private client: oauth.Client;
  private authServer: oauth.AuthorizationServer | null = null;

  constructor() {
    this.client = {
      client_id: this.clientId,
      token_endpoint_auth_method: 'none' // Public client, no secret
    };
  }

  /**
   * Initialize by discovering OAuth server metadata
   */
  async initialize(): Promise<void> {
    this.authServer = await oauth
      .discoveryRequest(this.issuer)
      .then((response) => oauth.processDiscoveryResponse(this.issuer, response));
  }

  /**
   * Start PKCE authorization flow
   */
  async startAuthFlow(): Promise<void> {
    if (!this.authServer) await this.initialize();

    // Generate PKCE parameters
    const codeVerifier = oauth.generateRandomCodeVerifier();
    const codeChallenge = await oauth.calculatePKCECodeChallenge(codeVerifier);
    const state = oauth.generateRandomState();

    // Store for callback (session storage is cleared after auth)
    sessionStorage.setItem('gcal_code_verifier', codeVerifier);
    sessionStorage.setItem('gcal_state', state);

    // Build authorization URL
    const authUrl = new URL(this.authServer!.authorization_endpoint!);
    authUrl.searchParams.set('client_id', this.clientId);
    authUrl.searchParams.set('redirect_uri', this.redirectUri);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('scope', this.scopes.join(' '));
    authUrl.searchParams.set('state', state);
    authUrl.searchParams.set('code_challenge', codeChallenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('access_type', 'offline');
    authUrl.searchParams.set('prompt', 'consent');

    // Redirect to Google
    window.location.href = authUrl.toString();
  }

  /**
   * Handle OAuth callback
   */
  async handleCallback(): Promise<oauth.TokenEndpointResponse | null> {
    if (!this.authServer) await this.initialize();

    const params = new URLSearchParams(window.location.search);
    const code = params.get('code');
    const state = params.get('state');

    if (!code) return null;

    // Verify state (CSRF protection)
    const storedState = sessionStorage.getItem('gcal_state');
    if (state !== storedState) {
      throw new Error('State mismatch - possible CSRF attack');
    }

    // Get code verifier
    const codeVerifier = sessionStorage.getItem('gcal_code_verifier');
    if (!codeVerifier) {
      throw new Error('Code verifier not found');
    }

    // Exchange authorization code for tokens
    const tokenResponse = await oauth.authorizationCodeGrantRequest(
      this.authServer!,
      this.client,
      params,
      this.redirectUri,
      codeVerifier
    );

    const result = await oauth.processAuthorizationCodeResponse(
      this.authServer!,
      this.client,
      tokenResponse
    );

    if (oauth.isOAuth2Error(result)) {
      throw new Error(`OAuth error: ${result.error_description || result.error}`);
    }

    // Store tokens
    await this.storeTokens(result);

    // Clean up
    sessionStorage.removeItem('gcal_code_verifier');
    sessionStorage.removeItem('gcal_state');
    window.history.replaceState({}, document.title, window.location.pathname);

    return result;
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken(): Promise<string> {
    if (!this.authServer) await this.initialize();

    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'gcal_refresh_token' } })
      .exec();

    if (!config) {
      throw new Error('No refresh token found - please re-authenticate');
    }

    const response = await oauth.refreshTokenGrantRequest(
      this.authServer!,
      this.client,
      config.value
    );

    const result = await oauth.processRefreshTokenResponse(
      this.authServer!,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(result)) {
      throw new Error(`Token refresh failed: ${result.error_description || result.error}`);
    }

    await this.storeTokens(result);
    return result.access_token;
  }

  /**
   * Get current access token (refresh if expired)
   */
  async getAccessToken(): Promise<string> {
    const db = await getDatabase();

    const [tokenConfig, expiresConfig] = await Promise.all([
      db.config.findOne({ selector: { key: 'gcal_access_token' } }).exec(),
      db.config.findOne({ selector: { key: 'gcal_token_expires_at' } }).exec()
    ]);

    if (!tokenConfig) {
      throw new Error('Not authenticated - please sign in');
    }

    // Check if token expired
    if (expiresConfig && expiresConfig.value < Date.now()) {
      console.log('Access token expired, refreshing...');
      return await this.refreshAccessToken();
    }

    return tokenConfig.value;
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'gcal_refresh_token' } })
      .exec();

    return !!config;
  }

  /**
   * Sign out (clear tokens)
   */
  async signOut(): Promise<void> {
    const db = await getDatabase();

    await Promise.all([
      db.config.findOne({ selector: { key: 'gcal_access_token' } }).remove(),
      db.config.findOne({ selector: { key: 'gcal_refresh_token' } }).remove(),
      db.config.findOne({ selector: { key: 'gcal_token_expires_at' } }).remove()
    ]);
  }

  /**
   * Store tokens in database
   */
  private async storeTokens(tokens: oauth.TokenEndpointResponse): Promise<void> {
    const db = await getDatabase();

    await db.config.upsert({
      key: 'gcal_access_token',
      value: tokens.access_token,
      updatedAt: Date.now()
    });

    if (tokens.refresh_token) {
      await db.config.upsert({
        key: 'gcal_refresh_token',
        value: tokens.refresh_token,
        updatedAt: Date.now()
      });
    }

    if (tokens.expires_in) {
      await db.config.upsert({
        key: 'gcal_token_expires_at',
        value: Date.now() + tokens.expires_in * 1000,
        updatedAt: Date.now()
      });
    }
  }
}
```

### GitHub (Device Flow)

**`src/services/github/oauth.ts`**
```typescript
import * as oauth from 'oauth4webapi';
import { getDatabase } from '../../db/database';

export interface DeviceFlowData {
  userCode: string;
  verificationUri: string;
  verificationUriComplete?: string;
  deviceCode: string;
  expiresIn: number;
  interval: number;
}

export class GitHubOAuth {
  private readonly clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;
  private readonly authServer: oauth.AuthorizationServer = {
    issuer: 'https://github.com',
    device_authorization_endpoint: 'https://github.com/login/device/code',
    token_endpoint: 'https://github.com/login/oauth/access_token'
  };

  private client: oauth.Client;

  constructor() {
    this.client = {
      client_id: this.clientId,
      token_endpoint_auth_method: 'none'
    };
  }

  /**
   * Start device authorization flow
   */
  async startDeviceFlow(): Promise<DeviceFlowData> {
    const response = await oauth.deviceAuthorizationRequest(
      this.authServer,
      this.client,
      {
        scope: 'repo read:project'
      }
    );

    const deviceAuth = await oauth.processDeviceAuthorizationResponse(
      this.authServer,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(deviceAuth)) {
      throw new Error(`Device flow error: ${deviceAuth.error_description || deviceAuth.error}`);
    }

    return {
      userCode: deviceAuth.user_code,
      verificationUri: deviceAuth.verification_uri,
      verificationUriComplete: deviceAuth.verification_uri_complete,
      deviceCode: deviceAuth.device_code,
      expiresIn: deviceAuth.expires_in,
      interval: deviceAuth.interval || 5
    };
  }

  /**
   * Poll for access token (recursive)
   */
  async pollForToken(deviceCode: string, interval: number = 5): Promise<string> {
    const response = await oauth.deviceCodeGrantRequest(
      this.authServer,
      this.client,
      deviceCode
    );

    const result = await oauth.processDeviceCodeResponse(
      this.authServer,
      this.client,
      response
    );

    if (oauth.isOAuth2Error(result)) {
      if (result.error === 'authorization_pending') {
        // User hasn't authorized yet, keep polling
        await new Promise(resolve => setTimeout(resolve, interval * 1000));
        return this.pollForToken(deviceCode, interval);
      } else if (result.error === 'slow_down') {
        // GitHub asking us to slow down
        await new Promise(resolve => setTimeout(resolve, (interval + 5) * 1000));
        return this.pollForToken(deviceCode, interval + 5);
      } else {
        // Other error (expired, denied, etc.)
        throw new Error(`OAuth error: ${result.error_description || result.error}`);
      }
    }

    // Success!
    await this.storeToken(result.access_token);
    return result.access_token;
  }

  /**
   * Get current access token
   */
  async getAccessToken(): Promise<string> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .exec();

    if (!config) {
      throw new Error('Not authenticated - please sign in');
    }

    return config.value;
  }

  /**
   * Check if authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    const db = await getDatabase();
    const config = await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .exec();

    return !!config;
  }

  /**
   * Sign out
   */
  async signOut(): Promise<void> {
    const db = await getDatabase();
    await db.config
      .findOne({ selector: { key: 'github_access_token' } })
      .remove();
  }

  /**
   * Store token
   */
  private async storeToken(token: string): Promise<void> {
    const db = await getDatabase();
    await db.config.upsert({
      key: 'github_access_token',
      value: token,
      updatedAt: Date.now()
    });
  }
}
```

---

## Composables (Vue Integration)

### usePoissonScheduler

**`src/composables/usePoissonScheduler.ts`**
```typescript
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { PingScheduler } from '../services/poisson-scheduler';
import { useWorkSession } from './useWorkSession';
import { useVisibility } from './useVisibility';

export function usePoissonScheduler() {
  const scheduler = new PingScheduler();
  const { currentSession } = useWorkSession();
  const { isVisible } = useVisibility();

  const isActive = ref(false);
  const nextPingTime = ref<number | null>(null);
  const missedPingCount = ref(0);

  // Handle ping events from scheduler
  const handlePingEvent = (event: CustomEvent) => {
    const { pingIndex, pingTime } = event.detail;

    // Emit to parent component to show dialog
    window.dispatchEvent(new CustomEvent('whatnow:show-ping-dialog', {
      detail: { pingIndex, pingTime }
    }));
  };

  // Auto-pause/resume based on visibility
  watch(isVisible, (visible) => {
    if (!isActive.value) return;

    if (visible) {
      scheduler.resume();
      checkForMissedPings();
    } else {
      scheduler.pause();
    }
  });

  // Check for missed pings when returning to app
  const checkForMissedPings = () => {
    const missed = scheduler.getMissedPings();
    missedPingCount.value = missed.length;

    if (missed.length > 0) {
      window.dispatchEvent(new CustomEvent('whatnow:missed-pings', {
        detail: { missed }
      }));
    }
  };

  // Start scheduler with work session
  const start = async (workSessionId: number, averageGapMinutes: number = 45) => {
    await scheduler.startWorkSession(workSessionId, averageGapMinutes);
    isActive.value = true;
  };

  // Stop scheduler
  const stop = async () => {
    await scheduler.endWorkSession();
    isActive.value = false;
    nextPingTime.value = null;
  };

  // Mark ping as completed
  const completePing = async (pingIndex: number) => {
    await scheduler.completePing(pingIndex);
    missedPingCount.value = scheduler.getMissedPings().length;
  };

  // Load existing schedule on mount
  onMounted(async () => {
    const loaded = await scheduler.loadSchedule();
    if (loaded) {
      isActive.value = true;
      checkForMissedPings();
    }

    window.addEventListener('whatnow:ping', handlePingEvent as EventListener);
  });

  onUnmounted(() => {
    window.removeEventListener('whatnow:ping', handlePingEvent as EventListener);
  });

  return {
    isActive,
    nextPingTime,
    missedPingCount,
    start,
    stop,
    completePing,
    checkForMissedPings
  };
}
```

---

## Updated Project Structure

```
whatnow-web/
├── public/
│   ├── manifest.json
│   ├── icon-192.png
│   ├── icon-512.png
│   └── badge-72.png
├── src/
│   ├── main.ts
│   ├── App.vue
│   ├── service-worker.ts          # Service worker with Workbox
│   ├── components/
│   │   ├── ping/
│   │   │   ├── PingDialog.vue
│   │   │   ├── MissedPingsDialog.vue
│   │   │   └── UpcomingPings.vue  # Show next scheduled pings
│   │   ├── todos/
│   │   │   └── UnifiedTodoView.vue
│   │   └── settings/
│   │       ├── SchedulerSettings.vue
│   │       └── NotificationSettings.vue
│   ├── composables/
│   │   ├── usePoissonScheduler.ts  # Main scheduler composable
│   │   ├── useWorkSession.ts
│   │   ├── useVisibility.ts
│   │   ├── useNotifications.ts
│   │   ├── useGitHubSync.ts
│   │   └── useGoogleCalendar.ts
│   ├── services/
│   │   ├── poisson-scheduler.ts    # Core scheduling logic
│   │   ├── github/
│   │   │   ├── oauth.ts            # Device flow with oauth4webapi
│   │   │   ├── graphql.ts
│   │   │   └── sync.ts
│   │   └── google-calendar/
│   │       ├── oauth.ts            # PKCE flow with oauth4webapi
│   │       ├── api.ts
│   │       └── sync.ts
│   ├── db/
│   │   ├── database.ts
│   │   └── schemas/
│   │       ├── ping.schema.ts
│   │       ├── local-todo.schema.ts
│   │       └── config.schema.ts
│   └── utils/
│       ├── priority.ts
│       └── activity-resolver.ts
├── tests/
│   └── unit/
│       └── services/
│           └── poisson-scheduler.test.ts
├── .env.example
├── vite.config.ts
├── package.json
└── tsconfig.json
```

---

## Updated Phase-by-Phase Plan

### Phase 2: Core Scheduler & Work Sessions (Week 2)

**Tasks**:
1. ✅ Implement `generatePingSchedule()` function with Poisson distribution
2. ✅ Create `PingScheduler` class with schedule management
3. ✅ Implement scheduled notifications (with feature detection)
4. ✅ Create active timer fallback
5. ✅ Implement `usePoissonScheduler` composable
6. ✅ Build work session UI (start/stop)
7. ✅ Integrate Page Visibility API
8. ✅ Create `useVisibility` composable
9. ✅ Implement missed ping detection
10. ✅ **Unit tests for Poisson distribution statistics**

**Key Deliverable**: Scheduler generates schedule, uses Scheduled Notifications API on Chrome, falls back gracefully

---

### Phase 9: PWA & Background Sync (Week 9)

**Tasks**:
1. ✅ Configure Vite PWA plugin with Workbox
2. ✅ Implement service worker with periodic sync
3. ✅ Create IndexedDB helpers for service worker
4. ✅ Implement `checkPingSchedule()` in service worker
5. ✅ Register Periodic Background Sync
6. ✅ Implement notification click handlers
7. ✅ Create missed pings dialog component
8. ✅ Add "Upcoming Pings" view in UI
9. ✅ Test all browser tiers (Chrome, Firefox, Safari)
10. ✅ Create PWA install prompt

---

## Testing the Scheduler

**`tests/unit/services/poisson-scheduler.test.ts`**
```typescript
import { describe, it, expect } from 'vitest';
import { generatePingSchedule, calculateScheduleStats } from '../../../src/services/poisson-scheduler';

describe('Poisson Scheduler', () => {
  it('generates correct number of pings', () => {
    const schedule = generatePingSchedule(Date.now(), 100, 45);
    expect(schedule).toHaveLength(100);
  });

  it('generates increasing timestamps', () => {
    const schedule = generatePingSchedule(Date.now(), 50, 45);

    for (let i = 1; i < schedule.length; i++) {
      expect(schedule[i]).toBeGreaterThan(schedule[i - 1]);
    }
  });

  it('has statistically correct average gap', () => {
    // Large sample for statistical test
    const schedule = generatePingSchedule(Date.now(), 1000, 45);
    const stats = calculateScheduleStats(schedule);

    // Average should be within 10% of expected (45 minutes)
    expect(stats.averageGapMinutes).toBeGreaterThan(40);
    expect(stats.averageGapMinutes).toBeLessThan(50);
  });

  it('follows exponential distribution', () => {
    const schedule = generatePingSchedule(Date.now(), 10000, 45);
    const stats = calculateScheduleStats(schedule);

    // In exponential distribution, min is much less than average
    expect(stats.minGapMinutes).toBeLessThan(stats.averageGapMinutes * 0.1);

    // And max is much greater
    expect(stats.maxGapMinutes).toBeGreaterThan(stats.averageGapMinutes * 3);
  });
});
```

---

## Environment Variables

**`.env.example`**
```env
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_GITHUB_CLIENT_ID=your-github-client-id
```

---

## Package.json

**`package.json`**
```json
{
  "name": "whatnow-web",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint src --ext .ts,.vue",
    "format": "prettier --write src"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "rxdb": "^15.0.0",
    "rxdb-premium": "^15.0.0",
    "dexie": "^4.0.0",
    "oauth4webapi": "^2.11.1",
    "@headlessui/vue": "^1.7.0",
    "@heroicons/vue": "^2.1.0",
    "dayjs": "^1.11.0",
    "comlink": "^4.4.0",
    "workbox-core": "^7.0.0",
    "workbox-precaching": "^7.0.0",
    "workbox-routing": "^7.0.0",
    "workbox-strategies": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0",
    "vite-plugin-pwa": "^0.19.0",
    "typescript": "^5.3.0",
    "vue-tsc": "^1.8.0",
    "@types/node": "^20.0.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "vitest": "^1.0.0",
    "@playwright/test": "^1.40.0",
    "eslint": "^8.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint-plugin-vue": "^9.0.0",
    "prettier": "^3.0.0"
  }
}
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Set environment variables for OAuth client IDs
- [ ] Build production bundle: `npm run build`
- [ ] Test PWA manifest and icons
- [ ] Test service worker in production mode
- [ ] Verify HTTPS (required for service workers)

### OAuth Configuration

**Google Cloud Console:**
- [ ] Add production URL to authorized redirect URIs
- [ ] Add `http://localhost:5173` for development

**GitHub OAuth App:**
- [ ] No redirect URI needed (Device Flow)
- [ ] Note client ID

### Hosting Options

**GitHub Pages:**
```bash
npm run build
git subtree push --prefix dist origin gh-pages
```

**Netlify:**
```toml
# netlify.toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

**Vercel:**
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist"
}
```

---

## Summary of Key Improvements

### 1. **Pre-Scheduled Approach**
- ✅ Generate entire schedule upfront (no continuous timer needed)
- ✅ Store in IndexedDB (persists across crashes)
- ✅ Enable true background notifications

### 2. **Progressive Enhancement**
- ⭐ **Tier 1** (Chrome 83+): Scheduled Notifications API - full background support
- ⭐ **Tier 2** (Chrome/Edge): Periodic Background Sync + active timer
- ⭐ **Tier 3** (Firefox/Safari): Active timer with pause/resume
- ⭐ **Tier 4** (Any browser): Basic active timer

### 3. **oauth4webapi Integration**
- ✅ Official OAuth 2.1 library (no custom crypto)
- ✅ Auto-discovery of OAuth endpoints
- ✅ Built-in error handling
- ✅ Token refresh management

### 4. **Better UX**
- ✅ Missed ping tracking and batch logging
- ✅ Upcoming pings view
- ✅ Notification actions (log from notification)
- ✅ Works offline (PWA)

---

This updated plan provides a solid foundation for a modern, static web app that gracefully handles the constraints of browser-based scheduling while providing the best possible experience on supporting browsers.

Ready to proceed with implementation?
