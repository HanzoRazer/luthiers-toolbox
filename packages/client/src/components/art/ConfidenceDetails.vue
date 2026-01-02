<template>
  <div class="confidence-details">
    <div class="header">
      <ConfidenceBadge :level="reason.level" :tooltip="reason.detail" />
      <span class="short">{{ reason.short }}</span>
    </div>
    <p class="detail">{{ reason.detail }}</p>

    <div v-if="diff" class="diff-section">
      <div class="diff-title">Compared to previous:</div>
      <div class="diff-row">
        <span class="label">Score:</span>
        <span :class="scoreDeltaClass">
          {{ diff.aScore.toFixed(0) }} &rarr; {{ diff.bScore.toFixed(0) }}
          ({{ diff.scoreDelta >= 0 ? "+" : "" }}{{ diff.scoreDelta.toFixed(0) }})
        </span>
      </div>
      <div class="diff-row" v-if="diff.riskChanged">
        <span class="label">Risk:</span>
        <span>{{ diff.aRisk }} &rarr; {{ diff.bRisk }}</span>
      </div>
      <div class="diff-row" v-if="diff.warnDelta !== 0">
        <span class="label">Warnings:</span>
        <span :class="warnDeltaClass">
          {{ diff.aWarn }} &rarr; {{ diff.bWarn }}
          ({{ diff.warnDelta >= 0 ? "+" : "" }}{{ diff.warnDelta }})
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import ConfidenceBadge from "./ConfidenceBadge.vue";
import type { ConfidenceReason } from "@/utils/confidenceReasons";

const props = defineProps<{
  reason: ConfidenceReason;
  diff?: {
    scoreDelta: number;
    aScore: number;
    bScore: number;
    aRisk: string;
    bRisk: string;
    aWarn: number;
    bWarn: number;
    warnDelta: number;
    riskChanged: boolean;
  } | null;
}>();

const scoreDeltaClass = computed(() => {
  if (!props.diff) return "";
  if (props.diff.scoreDelta > 0) return "positive";
  if (props.diff.scoreDelta < 0) return "negative";
  return "";
});

const warnDeltaClass = computed(() => {
  if (!props.diff) return "";
  if (props.diff.warnDelta < 0) return "positive"; // fewer warnings is good
  if (props.diff.warnDelta > 0) return "negative";
  return "";
});
</script>

<style scoped>
.confidence-details {
  padding: 12px;
  background: #fafafa;
  border: 1px solid #eee;
  border-radius: 10px;
}

.header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.short {
  font-weight: 600;
  font-size: 14px;
}

.detail {
  font-size: 13px;
  color: #555;
  margin: 0;
}

.diff-section {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid #ddd;
}

.diff-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 6px;
}

.diff-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  margin: 4px 0;
}

.label {
  color: #888;
  min-width: 70px;
}

.positive {
  color: #22c55e;
}

.negative {
  color: #ef4444;
}
</style>
