// composables/useResourceCleanup.js
import { onUnmounted, ref } from 'vue';

export function useResourceCleanup() {
  const resources = ref([]);
  const timers = ref(new Set());
  const eventListeners = ref([]);
  const webSockets = ref(new Set());
  
  const addCleanup = (cleanup) => {
    if (typeof cleanup === 'function') {
      resources.value.push(cleanup);
    }
  };
  
  const addTimer = (timerId) => {
    timers.value.add(timerId);
    return timerId;
  };
  
  const addEventListener = (element, event, handler, options) => {
    element.addEventListener(event, handler, options);
    eventListeners.value.push({ element, event, handler, options });
  };
  
  const addWebSocket = (socket) => {
    webSockets.value.add(socket);
    return socket;
  };
  
  const clearTimer = (timerId) => {
    clearTimeout(timerId);
    clearInterval(timerId);
    timers.value.delete(timerId);
  };
  
  const clearAllTimers = () => {
    timers.value.forEach(timerId => {
      clearTimeout(timerId);
      clearInterval(timerId);
    });
    timers.value.clear();
  };
  
  const clearAllEventListeners = () => {
    eventListeners.value.forEach(({ element, event, handler, options }) => {
      try {
        element.removeEventListener(event, handler, options);
      } catch (error) {
        console.warn('Error removing event listener:', error);
      }
    });
    eventListeners.value.length = 0;
  };
  
  const clearAllWebSockets = () => {
    webSockets.value.forEach(socket => {
      try {
        if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
          socket.close(1000, 'Component unmounted');
        }
      } catch (error) {
        console.warn('Error closing WebSocket:', error);
      }
    });
    webSockets.value.clear();
  };
  
  const cleanupAll = () => {
    // Clear custom cleanup functions
    resources.value.forEach(cleanup => {
      try {
        cleanup();
      } catch (error) {
        console.warn('Cleanup error:', error);
      }
    });
    
    // Clear timers
    clearAllTimers();
    
    // Clear event listeners
    clearAllEventListeners();
    
    // Clear WebSockets
    clearAllWebSockets();
    
    // Clear arrays
    resources.value.length = 0;
  };
  
  // Automatic cleanup on unmount
  onUnmounted(cleanupAll);
  
  // Manual cleanup method
  const cleanup = () => {
    cleanupAll();
  };
  
  return {
    addCleanup,
    addTimer,
    addEventListener,
    addWebSocket,
    clearTimer,
    clearAllTimers,
    clearAllEventListeners,
    clearAllWebSockets,
    cleanup
  };
}

// Utility for creating safe timers
export function useSafeTimer() {
  const { addTimer, clearTimer } = useResourceCleanup();
  
  const setTimeout = (callback, delay) => {
    const timerId = window.setTimeout(callback, delay);
    addTimer(timerId);
    return timerId;
  };
  
  const setInterval = (callback, interval) => {
    const timerId = window.setInterval(callback, interval);
    addTimer(timerId);
    return timerId;
  };
  
  return {
    setTimeout,
    setInterval,
    clearTimeout: clearTimer,
    clearInterval: clearTimer
  };
}