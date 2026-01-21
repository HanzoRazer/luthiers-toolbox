<!-- packages/client/src/components/common/ToastHost.vue -->
<!--
  Global toast notification host component.
  
  Mount this near your app root (App.vue) to enable toast notifications.
  Uses toastStore for state management.
  
  Usage:
    <template>
      <router-view />
      <ToastHost />
    </template>
-->

<script setup lang="ts">
import { computed } from "vue";
import { useToastStore } from "@/stores/toastStore";

const store = useToastStore();
const toasts = computed(() => store.toasts);

function onClose(id: number) {
  store.removeToast(id);
}
</script>

<template>
  <div
    class="fixed inset-x-0 bottom-0 z-50 flex justify-center pointer-events-none px-4 pb-4"
  >
    <div class="w-full max-w-sm space-y-2 pointer-events-auto">
      <TransitionGroup
        name="toast-fade"
        tag="div"
        class="space-y-2"
      >
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="flex items-start gap-2 rounded-xl px-3 py-2 text-xs shadow-lg border bg-white dark:bg-gray-800"
          :class="[
            toast.variant === 'success'
              ? 'border-emerald-300 dark:border-emerald-600'
              : toast.variant === 'error'
                ? 'border-red-300 dark:border-red-600'
                : toast.variant === 'warning'
                  ? 'border-amber-300 dark:border-amber-600'
                  : 'border-gray-200 dark:border-gray-600',
          ]"
        >
          <!-- Status dot -->
          <span
            class="mt-0.5 inline-block h-2 w-2 rounded-full flex-shrink-0"
            :class="[
              toast.variant === 'success'
                ? 'bg-emerald-500'
                : toast.variant === 'error'
                  ? 'bg-red-500'
                  : toast.variant === 'warning'
                    ? 'bg-amber-500'
                    : 'bg-blue-500',
            ]"
          />

          <!-- Message -->
          <div class="flex-1 min-w-0">
            <p class="text-[11px] text-gray-900 dark:text-gray-100 break-words">
              {{ toast.message }}
            </p>
          </div>

          <!-- Close button -->
          <button
            type="button"
            class="ml-1 text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 flex-shrink-0"
            @click="onClose(toast.id)"
          >
            ✕
          </button>
        </div>
      </TransitionGroup>
    </div>
  </div>
</template>

<style scoped>
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.2s ease;
}
.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
