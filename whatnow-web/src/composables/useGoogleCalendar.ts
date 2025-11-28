import { ref, onMounted } from 'vue';
import { GoogleCalendarSync } from '../services/google-calendar/sync';

/**
 * Composable for Google Calendar integration
 */
export function useGoogleCalendar() {
  const sync = new GoogleCalendarSync();
  const oauth = sync.getOAuth();

  const isAuthenticated = ref(false);
  const isSyncing = ref(false);
  const lastSyncTime = ref<number | null>(null);
  const syncError = ref<string | null>(null);

  /**
   * Check authentication status
   */
  const checkAuth = async () => {
    isAuthenticated.value = await oauth.isAuthenticated();
  };

  /**
   * Start OAuth flow
   */
  const signIn = async () => {
    try {
      await oauth.startAuthFlow();
    } catch (error) {
      console.error('Failed to start OAuth flow:', error);
      syncError.value = error instanceof Error ? error.message : 'Failed to sign in';
    }
  };

  /**
   * Handle OAuth callback
   */
  const handleCallback = async (): Promise<boolean> => {
    try {
      const result = await oauth.handleCallback();
      if (result) {
        isAuthenticated.value = true;
        // Perform initial sync after authentication
        await performSync();
        return true;
      }
      return false;
    } catch (error) {
      console.error('OAuth callback failed:', error);
      syncError.value = error instanceof Error ? error.message : 'Authentication failed';
      return false;
    }
  };

  /**
   * Sign out
   */
  const signOut = async () => {
    try {
      await oauth.signOut();
      isAuthenticated.value = false;
      lastSyncTime.value = null;
    } catch (error) {
      console.error('Failed to sign out:', error);
      syncError.value = error instanceof Error ? error.message : 'Failed to sign out';
    }
  };

  /**
   * Perform calendar sync
   */
  const performSync = async (days: number = 7) => {
    if (!isAuthenticated.value) {
      syncError.value = 'Not authenticated';
      return;
    }

    isSyncing.value = true;
    syncError.value = null;

    try {
      const stats = await sync.performSync(days);
      lastSyncTime.value = Date.now();
      console.log('Calendar sync completed:', stats);
    } catch (error) {
      console.error('Sync failed:', error);
      syncError.value = error instanceof Error ? error.message : 'Sync failed';
    } finally {
      isSyncing.value = false;
    }
  };

  /**
   * Auto-sync on mount if authenticated
   */
  onMounted(async () => {
    await checkAuth();

    // Check for OAuth callback
    const params = new URLSearchParams(window.location.search);
    if (params.has('code')) {
      await handleCallback();
    } else if (isAuthenticated.value) {
      // Perform initial sync if already authenticated
      await performSync();
    }
  });

  return {
    isAuthenticated,
    isSyncing,
    lastSyncTime,
    syncError,
    signIn,
    signOut,
    performSync,
    checkAuth
  };
}
