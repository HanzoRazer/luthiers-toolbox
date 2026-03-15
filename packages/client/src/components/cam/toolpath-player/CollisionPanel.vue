<script setup lang="ts">
/**
 * CollisionPanel — Collision detection results panel for ToolpathPlayer
 *
 * Extracted from ToolpathPlayer.vue to reduce component size.
 * Shows detected collisions with severity, line numbers, and messages.
 */
import type { CollisionReport } from '@/util/collisionDetector';

interface Props {
  report: CollisionReport;
  maxItems?: number;
}

const props = withDefaults(defineProps<Props>(), {
  maxItems: 10,
});

const emit = defineEmits<{
  close: [];
}>();

function formatTime(ms: number): string {
  const totalSecs = ms / 1000;
  const mins = Math.floor(totalSecs / 60);
  const secs = (totalSecs % 60).toFixed(1);
  return `${mins}:${secs.padStart(4, '0')}`;
}
</script>

<template>
  <div class="p4-panel collision-panel">
    <div class="panel-header">
      <span>{{ report.summary }}</span>
      <button @click="emit('close')">✕</button>
    </div>
    <ul class="panel-list">
      <li
        v-for="(coll, i) in report.collisions.slice(0, maxItems)"
        :key="i"
        :class="'severity-' + coll.severity"
      >
        <span class="coll-type">{{ coll.type }}</span>
        <span class="coll-line">L{{ coll.lineNumber }}</span>
        <span class="coll-msg">{{ coll.message }}</span>
      </li>
    </ul>
    <div
      v-if="report.collisions.length > maxItems"
      class="panel-more"
    >
      +{{ report.collisions.length - maxItems }} more...
    </div>
  </div>
</template>

<style scoped>
.p4-panel {
  position: absolute;
  right: 10px;
  bottom: 90px;
  width: 360px;
  max-height: 280px;
  background: #1a1a2e;
  border: 1px solid #3a3a5c;
  border-radius: 8px;
  overflow: hidden;
  z-index: 10;
  font-size: 11px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #252538;
  border-bottom: 1px solid #3a3a5c;
  font-weight: 600;
  color: #ddd;
}

.panel-header button {
  background: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.panel-header button:hover { color: #e74c3c; }

.panel-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
}

.panel-list li {
  display: flex;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid #252538;
  color: #aaa;
}
.panel-list li:last-child { border-bottom: none; }

.panel-list li.severity-critical { background: rgba(231, 76, 60, 0.1); }
.panel-list li.severity-high { background: rgba(231, 76, 60, 0.1); }
.panel-list li.severity-warning { background: rgba(243, 156, 18, 0.1); }
.panel-list li.severity-medium { background: rgba(243, 156, 18, 0.1); }
.panel-list li.severity-low { background: transparent; }
.panel-list li.severity-info { background: transparent; }

.coll-type {
  color: #4a90d9;
  font-weight: 600;
  min-width: 90px;
  white-space: nowrap;
}

.coll-line {
  color: #666;
  min-width: 40px;
}

.coll-msg {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.panel-more {
  padding: 6px 12px;
  color: #666;
  text-align: center;
  background: #13131f;
}
</style>
