<script setup lang="ts">
/**
 * MemoryWarning — overlay banner for large-file memory alerts.
 * Shown when segment count exceeds WARNING_THRESHOLD (75k).
 */
import { computed } from "vue";
import type { MemoryInfo } from "@/stores/useToolpathPlayerStore";

const props = defineProps<{ memoryInfo: MemoryInfo }>();
const emit = defineEmits<{
  (e: "close"): void;
  (e: "optimize"): void;
}>();

const message = computed(() => {
  const n = props.memoryInfo.segmentCount.toLocaleString();
  const mb = props.memoryInfo.estimatedMB.toFixed(1);
  if (props.memoryInfo.isCritical)
    return `⚠️ ${n} segments (${mb} MB) — auto-downsampled for stability.`;
  return `⚠️ ${n} segments (${mb} MB) — performance may degrade.`;
});
</script>

<template>
  <div
    class="mem-warn"
    :class="{ critical: memoryInfo.isCritical }"
  >
    <span class="msg">{{ message }}</span>
    <div class="actions">
      <button
        class="opt-btn"
        @click="emit('optimize')"
      >
        ⚡ Optimize
      </button>
      <button
        class="close-btn"
        @click="emit('close')"
      >
        ✕
      </button>
    </div>
  </div>
</template>

<style scoped>
.mem-warn {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 12px;
  z-index: 20;
  background: #5c4a1a;
  border: 1px solid #f39c12;
  color: #f39c12;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  animation: slideDown 0.3s ease;
}
.mem-warn.critical {
  background: #5c1a1a;
  border-color: #e74c3c;
  color: #e74c3c;
}
@keyframes slideDown {
  from { transform: translate(-50%, -100%); opacity: 0; }
  to   { transform: translate(-50%, 0);     opacity: 1; }
}
.msg { white-space: nowrap; }
.actions { display: flex; gap: 6px; }
.opt-btn,
.close-btn {
  padding: 3px 10px;
  background: #252538;
  border: 1px solid #3a3a5c;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
}
.opt-btn:hover { background: #33334a; border-color: #4a90d9; }
.close-btn { color: #999; }
.close-btn:hover { background: #33334a; color: #fff; }
</style>
