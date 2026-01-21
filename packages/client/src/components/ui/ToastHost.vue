<script setup lang="ts">
import { computed } from "vue";
import { useUiToastStore } from "@/stores/uiToastStore";

const toastStore = useUiToastStore();
const items = computed(() => toastStore.toasts);

function cls(level: string) {
  if (level === "success") return "success";
  if (level === "warn") return "warn";
  if (level === "error") return "error";
  return "info";
}
</script>

<template>
  <div
    class="toast-host"
    aria-live="polite"
    aria-relevant="additions removals"
  >
    <div
      v-for="t in items"
      :key="t.id"
      class="toast"
      :class="cls(t.level)"
      role="status"
      :title="t.detail || 'Click to dismiss'"
      @click="toastStore.dismiss(t.id)"
    >
      <div class="msg">
        {{ t.message }}
      </div>
      <div
        v-if="t.detail"
        class="detail"
      >
        {{ t.detail }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.toast-host {
  position: fixed;
  right: 14px;
  bottom: 14px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-width: 360px;
  pointer-events: none; /* allow underlying UI; toasts still clickable via child */
}

.toast {
  pointer-events: auto;
  cursor: pointer;
  border-radius: 12px;
  border: 1px solid #e6e6e6;
  background: #fff;
  padding: 10px 12px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.10);
  animation: pop 140ms ease-out;
}

@keyframes pop {
  from { transform: translateY(6px); opacity: 0.7; }
  to   { transform: translateY(0);  opacity: 1; }
}

.msg {
  font-size: 12px;
  font-weight: 800;
  color: #111;
}

.detail {
  margin-top: 4px;
  font-size: 11px;
  color: #555;
}

.toast.info { border-color: #dfe6ff; background: #fbfcff; }
.toast.success { border-color: #bfeadd; background: #f3fbf7; }
.toast.warn { border-color: #ffe3a3; background: #fffaf0; }
.toast.error { border-color: #f3bcbc; background: #fff5f5; }
</style>
