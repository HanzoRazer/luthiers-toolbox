<template>
  <div
    v-if="open"
    class="backdrop"
    @click.self="emit('close')"
  >
    <div
      class="drawer"
      :data-side="side"
    >
      <div class="hdr">
        <div class="title">
          {{ title }}
        </div>
        <div class="actions">
          <slot name="actions" />
          <button
            class="x"
            title="Close"
            @click="emit('close')"
          >
            ×
          </button>
        </div>
      </div>

      <div class="body">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * SideDrawer.vue (Bundle 32.7.4)
 *
 * Reusable slide-in drawer component. Used for Log Viewer split pane.
 * - `open`: Controls visibility
 * - `title`: Optional header text
 * - `side`: "right" (default) or "left"
 * - Backdrop click or × button emits `close`
 * - `actions` slot for extra header buttons
 */
defineProps<{
  open: boolean;
  title?: string;
  side?: "right" | "left";
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();
</script>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.18);
  z-index: 8500;
}

.drawer {
  position: absolute;
  top: 0;
  bottom: 0;
  right: 0;
  width: min(48vw, 780px);
  background: white;
  border-left: 1px solid rgba(0, 0, 0, 0.10);
  box-shadow: -14px 0 40px rgba(0, 0, 0, 0.18);
  display: flex;
  flex-direction: column;
}

.drawer[data-side="left"] {
  left: 0;
  right: auto;
  border-left: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.10);
  box-shadow: 14px 0 40px rgba(0, 0, 0, 0.18);
}

.hdr {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  background: rgba(0, 0, 0, 0.02);
}

.title {
  font-weight: 600;
  font-size: 14px;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.x {
  border: none;
  background: transparent;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
  opacity: 0.6;
  transition: opacity 0.1s;
}

.x:hover {
  opacity: 1;
}

.body {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>
