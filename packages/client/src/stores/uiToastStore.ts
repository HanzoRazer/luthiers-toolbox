import { defineStore } from "pinia";

export type ToastLevel = "info" | "success" | "warn" | "error";

export type UiToast = {
  id: string;
  level: ToastLevel;
  message: string;
  detail?: string;
  createdAt: number;
  durationMs: number;
};

function uid() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const useUiToastStore = defineStore("uiToast", {
  state: () => ({
    toasts: [] as UiToast[],
    maxToasts: 4,
  }),
  actions: {
    push(toast: Omit<UiToast, "id" | "createdAt" | "durationMs"> & { durationMs?: number }) {
      const t: UiToast = {
        ...toast,
        id: uid(),
        createdAt: Date.now(),
        durationMs: toast.durationMs ?? 2600,
      };

      this.toasts.push(t);
      if (this.toasts.length > this.maxToasts) {
        this.toasts = this.toasts.slice(this.toasts.length - this.maxToasts);
      }

      // Auto-dismiss
      window.setTimeout(() => {
        this.dismiss(t.id);
      }, t.durationMs);
    },

    dismiss(id: string) {
      this.toasts = this.toasts.filter((t) => t.id !== id);
    },

    clear() {
      this.toasts = [];
    },

    setMax(n: number) {
      const v = Math.max(1, Math.min(10, n));
      this.maxToasts = v;
      if (this.toasts.length > v) {
        this.toasts = this.toasts.slice(this.toasts.length - v);
      }
    },
  },
});
