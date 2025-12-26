<script setup lang="ts">
/**
 * SvgPathDiffViewer.vue
 *
 * Visual diff between two SVG variants.
 * Shows side-by-side comparison with path-level highlighting.
 */
import { computed, onMounted, ref, watch } from "vue";
import SvgPreview from "@/components/rmos/SvgPreview.vue";

const props = defineProps<{
  runId: string;
  leftAdvisoryId: string;
  rightAdvisoryId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const loading = ref(false);
const error = ref<string | null>(null);

// For now, show side-by-side previews
// TODO: Implement actual path-level diff visualization
</script>

<template>
  <div class="diff-box">
    <div class="header">
      <div class="title">SVG Comparison</div>
      <div class="subtitle">
        <code>{{ leftAdvisoryId.slice(0, 12) }}...</code>
        vs
        <code>{{ rightAdvisoryId.slice(0, 12) }}...</code>
      </div>
    </div>

    <div class="diff-grid">
      <div class="diff-side">
        <div class="side-label">Left</div>
        <SvgPreview
          :runId="runId"
          :advisoryId="leftAdvisoryId"
          :apiBase="apiBase"
        />
      </div>

      <div class="diff-side">
        <div class="side-label">Right</div>
        <SvgPreview
          :runId="runId"
          :advisoryId="rightAdvisoryId"
          :apiBase="apiBase"
        />
      </div>
    </div>

    <div class="hint subtle">
      Path-level diff visualization coming soon. Currently showing side-by-side preview.
    </div>
  </div>
</template>

<style scoped>
.diff-box {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 12px;
}

.header {
  margin-bottom: 12px;
}

.title {
  font-weight: 700;
}

.subtitle {
  font-size: 0.85rem;
  margin-top: 4px;
}

.diff-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.diff-side {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.side-label {
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  opacity: 0.8;
}

.hint {
  margin-top: 12px;
  font-size: 0.85rem;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 6px;
  text-align: center;
}

.subtle {
  opacity: 0.7;
}

code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85em;
  background: #f4f4f4;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

@media (max-width: 768px) {
  .diff-grid {
    grid-template-columns: 1fr;
  }
}
</style>
