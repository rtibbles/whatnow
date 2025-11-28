/**
 * PWA Composable
 *
 * Provides PWA installation prompt and offline status detection.
 */

import { ref, onMounted, onUnmounted, computed } from 'vue';

// Types for BeforeInstallPromptEvent
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>;
}

export function usePWA() {
  // Installation state
  const deferredPrompt = ref<BeforeInstallPromptEvent | null>(null);
  const isInstallable = ref(false);
  const isInstalled = ref(false);

  // Online/offline state
  const isOnline = ref(navigator.onLine);

  // Service worker state
  const swRegistration = ref<ServiceWorkerRegistration | null>(null);
  const swUpdateAvailable = ref(false);

  /**
   * Check if app is already installed
   */
  const checkIfInstalled = (): boolean => {
    // Check for standalone mode (PWA installed)
    if (window.matchMedia('(display-mode: standalone)').matches) {
      return true;
    }

    // Check for iOS standalone
    if ((navigator as any).standalone === true) {
      return true;
    }

    return false;
  };

  /**
   * Handle beforeinstallprompt event
   */
  const handleBeforeInstallPrompt = (e: Event) => {
    // Prevent the default browser install prompt
    e.preventDefault();

    // Store the event for later use
    deferredPrompt.value = e as BeforeInstallPromptEvent;
    isInstallable.value = true;
  };

  /**
   * Handle app installed event
   */
  const handleAppInstalled = () => {
    deferredPrompt.value = null;
    isInstallable.value = false;
    isInstalled.value = true;
    console.log('PWA installed successfully');
  };

  /**
   * Show install prompt
   */
  const showInstallPrompt = async (): Promise<boolean> => {
    if (!deferredPrompt.value) {
      console.warn('Install prompt not available');
      return false;
    }

    try {
      // Show the install prompt
      await deferredPrompt.value.prompt();

      // Wait for user choice
      const choiceResult = await deferredPrompt.value.userChoice;

      if (choiceResult.outcome === 'accepted') {
        console.log('User accepted the install prompt');
        isInstallable.value = false;
        isInstalled.value = true;
        return true;
      } else {
        console.log('User dismissed the install prompt');
        return false;
      }
    } catch (error) {
      console.error('Error showing install prompt:', error);
      return false;
    } finally {
      // Clear the deferred prompt
      deferredPrompt.value = null;
    }
  };

  /**
   * Dismiss install prompt (hide banner)
   */
  const dismissInstallPrompt = () => {
    isInstallable.value = false;
    // Store dismissal in localStorage to avoid showing again soon
    localStorage.setItem('pwa_install_dismissed', Date.now().toString());
  };

  /**
   * Check if install prompt was recently dismissed
   */
  const wasRecentlyDismissed = (): boolean => {
    const dismissedTime = localStorage.getItem('pwa_install_dismissed');
    if (!dismissedTime) return false;

    const dismissedDate = new Date(parseInt(dismissedTime, 10));
    const daysSinceDismissal = (Date.now() - dismissedDate.getTime()) / (1000 * 60 * 60 * 24);

    // Don't show again for 7 days
    return daysSinceDismissal < 7;
  };

  /**
   * Should show install prompt
   */
  const shouldShowInstall = computed(() => {
    return isInstallable.value && !isInstalled.value && !wasRecentlyDismissed();
  });

  /**
   * Handle online/offline events
   */
  const handleOnline = () => {
    isOnline.value = true;
    console.log('App is online');
  };

  const handleOffline = () => {
    isOnline.value = false;
    console.log('App is offline');
  };

  /**
   * Check for service worker updates
   */
  const checkForUpdates = async () => {
    if (!swRegistration.value) return;

    try {
      await swRegistration.value.update();
    } catch (error) {
      console.error('Error checking for updates:', error);
    }
  };

  /**
   * Handle service worker updates
   */
  const handleSWUpdate = (registration: ServiceWorkerRegistration) => {
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (!newWorker) return;

      newWorker.addEventListener('statechange', () => {
        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
          // New service worker available
          swUpdateAvailable.value = true;
          console.log('Service worker update available');
        }
      });
    });
  };

  /**
   * Apply service worker update
   */
  const applyUpdate = () => {
    if (!swRegistration.value?.waiting) return;

    // Send message to service worker to skip waiting
    swRegistration.value.waiting.postMessage({ type: 'SKIP_WAITING' });

    // Reload page when new service worker takes control
    navigator.serviceWorker.addEventListener('controllerchange', () => {
      window.location.reload();
    });
  };

  /**
   * Initialize PWA features
   */
  onMounted(async () => {
    // Check if already installed
    isInstalled.value = checkIfInstalled();

    // Listen for install prompt
    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

    // Listen for app installed
    window.addEventListener('appinstalled', handleAppInstalled);

    // Listen for online/offline
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Register service worker update handler
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.ready;
        swRegistration.value = registration;
        handleSWUpdate(registration);

        // Check for updates every hour
        setInterval(() => {
          checkForUpdates();
        }, 60 * 60 * 1000);
      } catch (error) {
        console.error('Service worker registration error:', error);
      }
    }
  });

  /**
   * Cleanup on unmount
   */
  onUnmounted(() => {
    window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.removeEventListener('appinstalled', handleAppInstalled);
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  });

  return {
    // Installation
    isInstallable,
    isInstalled,
    shouldShowInstall,
    showInstallPrompt,
    dismissInstallPrompt,

    // Network status
    isOnline,

    // Service worker updates
    swUpdateAvailable,
    applyUpdate,
    checkForUpdates
  };
}
