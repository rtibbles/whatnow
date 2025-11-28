import { ref, onMounted, onUnmounted } from 'vue';

/**
 * Composable for tracking document visibility state
 * Uses Page Visibility API to detect when tab is hidden/visible
 */
export function useVisibility() {
  const isVisible = ref(!document.hidden);

  const handleVisibilityChange = () => {
    isVisible.value = !document.hidden;
  };

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibilityChange);
  });

  onUnmounted(() => {
    document.removeEventListener('visibilitychange', handleVisibilityChange);
  });

  return {
    isVisible
  };
}
