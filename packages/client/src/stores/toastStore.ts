// packages/client/src/stores/toastStore.ts
/**
 * Toast/Snackbar notification store.
 *
 * Provides a global notification system using Pinia.
 * Toasts auto-dismiss after a configurable timeout.
 */

import { defineStore } from "pinia";
import { ref } from "vue";

export type ToastVariant = "info" | "success" | "warning" | "error";

export interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
  timeoutMs: number;
}

let nextId = 1;

export const useToastStore = defineStore("toast", () => {
  const toasts = ref<Toast[]>([]);

  /**
   * Push a new toast notification.
   *
   * @param message - Toast message text
   * @param variant - Type: info, success, warning, error
   * @param timeoutMs - Auto-dismiss timeout (default 4000ms)
   * @returns Toast ID for manual removal
   */
  function pushToast(
    message: string,
    variant: ToastVariant = "info",
    timeoutMs = 4000
  ): number {
    const id = nextId++;
    const toast: Toast = { id, message, variant, timeoutMs };
    toasts.value.push(toast);

    // Auto-remove after timeout
    window.setTimeout(() => {
      removeToast(id);
    }, timeoutMs);

    return id;
  }

  /**
   * Remove a toast by ID.
   */
  function removeToast(id: number) {
    toasts.value = toasts.value.filter((t) => t.id !== id);
  }

  // Convenience helpers
  function info(msg: string, timeoutMs?: number) {
    return pushToast(msg, "info", timeoutMs);
  }

  function success(msg: string, timeoutMs?: number) {
    return pushToast(msg, "success", timeoutMs);
  }

  function warning(msg: string, timeoutMs?: number) {
    return pushToast(msg, "warning", timeoutMs);
  }

  function error(msg: string, timeoutMs?: number) {
    return pushToast(msg, "error", timeoutMs);
  }

  return {
    toasts,
    pushToast,
    removeToast,
    info,
    success,
    warning,
    error,
  };
});
