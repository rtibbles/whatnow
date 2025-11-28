import { ref, onMounted } from 'vue';
import { GitHubSync } from '../services/github/sync';
import type { DeviceFlowData } from '../services/github/oauth';

/**
 * Composable for GitHub integration
 */
export function useGitHub() {
  const sync = new GitHubSync();
  const oauth = sync.getOAuth();

  const isAuthenticated = ref(false);
  const isSyncing = ref(false);
  const isAuthenticating = ref(false);
  const deviceFlow = ref<DeviceFlowData | null>(null);
  const lastSyncTime = ref<number | null>(null);
  const syncError = ref<string | null>(null);
  const authError = ref<string | null>(null);

  /**
   * Check authentication status
   */
  const checkAuth = async () => {
    isAuthenticated.value = await oauth.isAuthenticated();
  };

  /**
   * Start Device Flow authentication
   */
  const startDeviceFlow = async () => {
    try {
      isAuthenticating.value = true;
      authError.value = null;

      const data = await oauth.startDeviceFlow();
      deviceFlow.value = data;

      // Start polling for token
      pollForToken(data.deviceCode, data.interval);

    } catch (error) {
      console.error('Failed to start device flow:', error);
      authError.value = error instanceof Error ? error.message : 'Failed to start authentication';
      isAuthenticating.value = false;
    }
  };

  /**
   * Poll for access token
   */
  const pollForToken = async (deviceCode: string, interval: number) => {
    try {
      await oauth.pollForToken(deviceCode, interval);
      isAuthenticated.value = true;
      isAuthenticating.value = false;
      deviceFlow.value = null;
      authError.value = null;

      // Perform initial sync after authentication
      await performSync();

    } catch (error) {
      console.error('Device flow failed:', error);
      authError.value = error instanceof Error ? error.message : 'Authentication failed';
      isAuthenticating.value = false;
      deviceFlow.value = null;
    }
  };

  /**
   * Cancel device flow
   */
  const cancelDeviceFlow = () => {
    isAuthenticating.value = false;
    deviceFlow.value = null;
    authError.value = null;
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
   * Perform GitHub sync
   */
  const performSync = async () => {
    if (!isAuthenticated.value) {
      syncError.value = 'Not authenticated';
      return;
    }

    isSyncing.value = true;
    syncError.value = null;

    try {
      const stats = await sync.performSync();
      lastSyncTime.value = Date.now();
      console.log('GitHub sync completed:', stats);
    } catch (error) {
      console.error('Sync failed:', error);
      syncError.value = error instanceof Error ? error.message : 'Sync failed';
    } finally {
      isSyncing.value = false;
    }
  };

  /**
   * Auto-check auth on mount
   */
  onMounted(async () => {
    await checkAuth();

    // Perform initial sync if already authenticated
    if (isAuthenticated.value) {
      await performSync();
    }
  });

  return {
    isAuthenticated,
    isSyncing,
    isAuthenticating,
    deviceFlow,
    lastSyncTime,
    syncError,
    authError,
    startDeviceFlow,
    cancelDeviceFlow,
    signOut,
    performSync,
    checkAuth
  };
}
