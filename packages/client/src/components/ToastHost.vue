<template>
  <div class="toast-host">
    <div
      v-for="t in toast.toasts"
      :key="t.id"
      class="toast"
      :data-level="t.variant"
    >
      <div class="msg">
        {{ t.message }}
      </div>
      <button
        class="x"
        @click="toast.removeToast(t.id)"
      >
        x
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useToastStore } from "@/stores/toastStore";
const toast = useToastStore();
</script>

<style scoped>
.toast-host {
  position: fixed;
  right: 16px;
  bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 9999;
  max-width: 420px;
}
.toast {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #111;
  color: #fff;
  box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.12);
}
.toast[data-level="success"] {
  border-color: rgba(80, 200, 120, 0.45);
}
.toast[data-level="warning"] {
  border-color: rgba(240, 200, 80, 0.45);
}
.toast[data-level="error"] {
  border-color: rgba(240, 80, 80, 0.55);
}
.msg {
  line-height: 1.25;
}
.x {
  border: none;
  background: transparent;
  color: #fff;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.8;
}
.x:hover {
  opacity: 1;
}
</style>
