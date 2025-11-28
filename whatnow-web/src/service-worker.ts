/// <reference lib="webworker" />
import { precacheAndRoute, cleanupOutdatedCaches } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';

declare const self: ServiceWorkerGlobalScope;

// Type definitions for experimental APIs
interface PeriodicSyncEvent extends ExtendableEvent {
  tag: string;
}

interface SyncEvent extends ExtendableEvent {
  tag: string;
}

interface SyncManager {
  register(tag: string): Promise<void>;
  getTags(): Promise<string[]>;
}

interface PeriodicSyncManager {
  register(tag: string, options?: { minInterval?: number }): Promise<void>;
  getTags(): Promise<string[]>;
  unregister(tag: string): Promise<void>;
}

// Extend ServiceWorkerRegistration with experimental APIs
interface ServiceWorkerRegistrationWithSync extends ServiceWorkerRegistration {
  sync?: SyncManager;
  periodicSync?: PeriodicSyncManager;
}

// Precache app shell
precacheAndRoute(self.__WB_MANIFEST);
cleanupOutdatedCaches();

// ==========================================
// CACHING STRATEGIES
// ==========================================

// Cache images with expiration
registerRoute(
  ({ request }) => request.destination === 'image',
  new CacheFirst({
    cacheName: 'images-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 30 * 24 * 60 * 60 // 30 days
      })
    ]
  })
);

// Network-first for API calls with cache fallback
registerRoute(
  ({ url }) => url.hostname === 'api.github.com' || url.hostname === 'www.googleapis.com',
  new NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new ExpirationPlugin({
        maxEntries: 100,
        maxAgeSeconds: 5 * 60 // 5 minutes
      })
    ]
  })
);

// Stale-while-revalidate for fonts
registerRoute(
  ({ request }) => request.destination === 'font',
  new StaleWhileRevalidate({
    cacheName: 'fonts-cache'
  })
);

// ==========================================
// PERIODIC BACKGROUND SYNC
// Runs periodically to sync external data
// ==========================================

self.addEventListener('periodicsync', ((event: PeriodicSyncEvent) => {
  console.log('[Service Worker] Periodic sync triggered:', event.tag);

  if (event.tag === 'sync-external-data') {
    event.waitUntil(syncExternalData());
  }
}) as EventListener);

/**
 * Sync both GitHub and Calendar data
 */
async function syncExternalData(): Promise<void> {
  console.log('[Service Worker] Starting external data sync');

  try {
    await Promise.allSettled([syncGitHub(), syncGoogleCalendar()]);
  } catch (error) {
    console.error('[Service Worker] External sync failed:', error);
  }
}

/**
 * Sync GitHub issues
 */
async function syncGitHub(): Promise<void> {
  try {
    const token = await getConfigValue('github_access_token');
    if (!token) {
      console.log('[Service Worker] GitHub not authenticated, skipping sync');
      return;
    }

    console.log('[Service Worker] Syncing GitHub issues');

    // Fetch assigned issues via GraphQL
    const response = await fetch('https://api.github.com/graphql', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: `
          query {
            viewer {
              issues(first: 50, states: OPEN, filterBy: { assignee: null }) {
                nodes {
                  id
                  title
                  body
                  state
                  url
                  createdAt
                  updatedAt
                  labels(first: 10) {
                    nodes {
                      name
                    }
                  }
                  assignees(first: 5) {
                    nodes {
                      login
                    }
                  }
                }
              }
            }
          }
        `
      })
    });

    if (!response.ok) {
      throw new Error(`GitHub API error: ${response.status}`);
    }

    const data = await response.json();
    console.log('[Service Worker] GitHub sync successful:', data.data.viewer.issues.nodes.length, 'issues');

    // Update last sync time
    await setConfigValue('github_last_sync', Date.now());
  } catch (error) {
    console.error('[Service Worker] GitHub sync failed:', error);
    // Queue for retry
    await queueFailedSync('github', error);
  }
}

/**
 * Sync Google Calendar events
 */
async function syncGoogleCalendar(): Promise<void> {
  try {
    const token = await getConfigValue('gcal_access_token');
    if (!token) {
      console.log('[Service Worker] Google Calendar not authenticated, skipping sync');
      return;
    }

    console.log('[Service Worker] Syncing Google Calendar events');

    // Get events for next 7 days
    const timeMin = new Date().toISOString();
    const timeMax = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString();

    const response = await fetch(
      `https://www.googleapis.com/calendar/v3/calendars/primary/events?` +
        new URLSearchParams({
          timeMin,
          timeMax,
          singleEvents: 'true',
          orderBy: 'startTime'
        }),
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    if (!response.ok) {
      if (response.status === 401) {
        console.log('[Service Worker] Calendar token expired, needs refresh');
        // Main app will handle token refresh
        return;
      }
      throw new Error(`Calendar API error: ${response.status}`);
    }

    const data = await response.json();
    console.log('[Service Worker] Calendar sync successful:', data.items?.length || 0, 'events');

    // Update last sync time
    await setConfigValue('gcal_last_sync', Date.now());
  } catch (error) {
    console.error('[Service Worker] Calendar sync failed:', error);
    // Queue for retry
    await queueFailedSync('calendar', error);
  }
}

// ==========================================
// BACKGROUND SYNC (for retry on network restore)
// ==========================================

self.addEventListener('sync', ((event: SyncEvent) => {
  console.log('[Service Worker] Background sync triggered:', event.tag);

  if (event.tag === 'github-sync') {
    event.waitUntil(syncGitHub());
  } else if (event.tag === 'calendar-sync') {
    event.waitUntil(syncGoogleCalendar());
  } else if (event.tag.startsWith('retry-')) {
    event.waitUntil(retryFailedSync(event.tag));
  }
}) as EventListener);

/**
 * Retry a previously failed sync
 */
async function retryFailedSync(tag: string): Promise<void> {
  const syncType = tag.replace('retry-', '');

  console.log('[Service Worker] Retrying failed sync:', syncType);

  if (syncType === 'github') {
    await syncGitHub();
  } else if (syncType === 'calendar') {
    await syncGoogleCalendar();
  }

  // Clear from failed queue if successful
  const queue = ((await getConfigValue('failed_sync_queue')) as Array<{ type: string }>) || [];
  const updated = queue.filter((item) => item.type !== syncType);
  await setConfigValue('failed_sync_queue', updated);
}

/**
 * Queue a failed sync for retry
 */
async function queueFailedSync(type: string, error: unknown): Promise<void> {
  const queue =
    ((await getConfigValue('failed_sync_queue')) as Array<{
      type: string;
      timestamp: number;
      error: string;
    }>) || [];

  queue.push({
    type,
    timestamp: Date.now(),
    error: error instanceof Error ? error.message : String(error)
  });

  await setConfigValue('failed_sync_queue', queue);

  // Register for background sync retry
  try {
    const registration = self.registration as ServiceWorkerRegistrationWithSync;
    if (registration.sync) {
      await registration.sync.register(`retry-${type}`);
    }
  } catch (e) {
    console.warn('[Service Worker] Background sync not supported:', e);
  }
}

// ==========================================
// NOTIFICATION CLICK HANDLERS
// ==========================================

self.addEventListener('notificationclick', (event: NotificationEvent) => {
  console.log('[Service Worker] Notification clicked:', event.notification.tag);

  event.notification.close();

  const data = event.notification.data;

  if (data?.type === 'ping') {
    if (event.action === 'log') {
      // Open app to ping dialog
      event.waitUntil(
        (async () => {
          const clients = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });

          // Check if app is already open
          for (const client of clients) {
            if (client.url.includes(self.registration.scope) && 'focus' in client) {
              await client.focus();
              // Send message to open ping dialog
              client.postMessage({
                type: 'open-ping-dialog',
                pingIndex: data.pingIndex,
                sessionId: data.sessionId
              });
              return;
            }
          }

          // App not open, open new window
          await self.clients.openWindow(
            `${self.registration.scope}?ping=${data.pingIndex}&session=${data.sessionId}`
          );
        })()
      );
    } else if (event.action === 'dismiss') {
      // Mark as missed
      event.waitUntil(markPingAsMissed(data.sessionId, data.pingIndex));
    } else {
      // No action (clicked notification body)
      event.waitUntil(
        (async () => {
          const clients = await self.clients.matchAll({ type: 'window' });
          if (clients.length > 0) {
            await clients[0]!.focus();
          } else {
            await self.clients.openWindow(self.registration.scope);
          }
        })()
      );
    }
  }
});

/**
 * Mark a ping as missed
 */
async function markPingAsMissed(sessionId: string, pingIndex: number): Promise<void> {
  try {
    const schedule = (await getConfigValue('current_ping_schedule')) as {
      sessionId: string;
      missedPings: number[];
    } | null;

    if (schedule && schedule.sessionId === sessionId) {
      if (!schedule.missedPings) {
        schedule.missedPings = [];
      }
      schedule.missedPings.push(pingIndex);
      await setConfigValue('current_ping_schedule', schedule);

      console.log('[Service Worker] Marked ping as missed:', pingIndex);
    }
  } catch (error) {
    console.error('[Service Worker] Failed to mark ping as missed:', error);
  }
}

// ==========================================
// INDEXEDDB HELPERS
// Service worker can't use RxDB, need direct IndexedDB access
// ==========================================

/**
 * Open IndexedDB connection
 */
function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('whatnow', 1);

    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;

      // Create config store if it doesn't exist
      if (!db.objectStoreNames.contains('config')) {
        db.createObjectStore('config', { keyPath: 'key' });
      }
    };
  });
}

/**
 * Get config value from database
 */
async function getConfigValue(key: string): Promise<unknown> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(['config'], 'readonly');
    const store = tx.objectStore('config');
    const request = store.get(key);

    request.onsuccess = () => {
      const result = request.result;
      resolve(result ? result.value : null);
    };
    request.onerror = () => reject(request.error);
  });
}

/**
 * Set config value in database
 */
async function setConfigValue(key: string, value: unknown): Promise<void> {
  const db = await openDatabase();

  return new Promise((resolve, reject) => {
    const tx = db.transaction(['config'], 'readwrite');
    const store = tx.objectStore('config');
    const request = store.put({
      key,
      value,
      updatedAt: Date.now()
    });

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

// ==========================================
// MESSAGE HANDLER
// Listen for messages from main app
// ==========================================

self.addEventListener('message', (event: ExtendableMessageEvent) => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting();
  } else if (event.data?.type === 'SYNC_NOW') {
    event.waitUntil(syncExternalData());
  } else if (event.data?.type === 'REGISTER_PERIODIC_SYNC') {
    event.waitUntil(registerPeriodicSync());
  }
});

/**
 * Register periodic background sync
 */
async function registerPeriodicSync(): Promise<void> {
  try {
    const registration = self.registration as ServiceWorkerRegistrationWithSync;

    if (registration.periodicSync) {
      await registration.periodicSync.register('sync-external-data', {
        minInterval: 12 * 60 * 60 * 1000 // 12 hours
      });
      console.log('[Service Worker] Periodic sync registered');
    } else {
      console.warn('[Service Worker] Periodic sync not supported');
    }
  } catch (error) {
    console.error('[Service Worker] Failed to register periodic sync:', error);
  }
}

// ==========================================
// ACTIVATION
// ==========================================

self.addEventListener('activate', (event: ExtendableEvent) => {
  console.log('[Service Worker] Activated');

  event.waitUntil(
    Promise.all([
      self.clients.claim(), // Take control of all clients
      registerPeriodicSync() // Register periodic sync on activation
    ])
  );
});

console.log('[Service Worker] Loaded');
