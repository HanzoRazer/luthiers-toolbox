<script setup lang="ts">
/**
 * NetworkStatusBanner - Displays offline/online status
 *
 * Automatically detects network status and shows a banner when offline.
 * Includes a queue indicator for pending operations.
 */
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps<{
  /** Number of queued operations waiting for reconnection */
  queuedOperations?: number
}>()

const isOnline = ref(navigator.onLine)
const wasOffline = ref(false)
const showReconnected = ref(false)

function handleOnline() {
  isOnline.value = true
  if (wasOffline.value) {
    showReconnected.value = true
    // Auto-hide reconnected message after 3 seconds
    setTimeout(() => {
      showReconnected.value = false
      wasOffline.value = false
    }, 3000)
  }
}

function handleOffline() {
  isOnline.value = false
  wasOffline.value = true
  showReconnected.value = false
}

onMounted(() => {
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})

const showBanner = computed(() => !isOnline.value || showReconnected.value)
const bannerType = computed(() => isOnline.value ? 'success' : 'warning')
</script>

<template>
  <Transition name="slide">
    <div
      v-if="showBanner"
      class="network-banner"
      :class="`network-banner--${bannerType}`"
      role="alert"
    >
      <div class="network-banner__content">
        <!-- Offline state -->
        <template v-if="!isOnline">
          <svg
            class="network-banner__icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line
              x1="1"
              y1="1"
              x2="23"
              y2="23"
            />
            <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55" />
            <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39" />
            <path d="M10.71 5.05A16 16 0 0 1 22.58 9" />
            <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88" />
            <path d="M8.53 16.11a6 6 0 0 1 6.95 0" />
            <line
              x1="12"
              y1="20"
              x2="12.01"
              y2="20"
            />
          </svg>
          <span class="network-banner__text">
            You're offline
            <span
              v-if="queuedOperations"
              class="network-banner__queue"
            >
              ({{ queuedOperations }} operation{{ queuedOperations > 1 ? 's' : '' }} queued)
            </span>
          </span>
        </template>

        <!-- Reconnected state -->
        <template v-else>
          <svg
            class="network-banner__icon"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <polyline points="22 4 12 14.01 9 11.01" />
          </svg>
          <span class="network-banner__text">
            Back online
          </span>
        </template>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.network-banner {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9998;
  padding: 0.5rem 1rem;
  text-align: center;
}

.network-banner--warning {
  background: #fef3c7;
  border-bottom: 1px solid #f59e0b;
  color: #92400e;
}

.network-banner--success {
  background: #d1fae5;
  border-bottom: 1px solid #10b981;
  color: #065f46;
}

.network-banner__content {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.network-banner__icon {
  flex-shrink: 0;
}

.network-banner__queue {
  font-weight: 400;
  opacity: 0.8;
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  .network-banner--warning {
    background: #78350f;
    border-color: #d97706;
    color: #fde68a;
  }

  .network-banner--success {
    background: #064e3b;
    border-color: #059669;
    color: #a7f3d0;
  }
}
</style>
