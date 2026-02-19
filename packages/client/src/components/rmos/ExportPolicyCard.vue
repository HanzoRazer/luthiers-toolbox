<script setup lang="ts">
/**
 * ExportPolicyCard - Static export policy explainer
 *
 * Extracted from ManufacturingCandidateList.vue
 */
</script>

<template>
  <div class="policy muted">
    <div><strong>Export policy:</strong></div>
    <ul>
      <li>Export is blocked while any candidate is <span class="mono">NEEDS_DECISION</span>.</li>
      <li>Export downloads zips for <strong>GREEN</strong> candidates only.</li>
      <li>Hover the export button to see the exact block reason.</li>
    </ul>
  </div>
</template>

<style scoped>
.policy {
  padding: 10px 12px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.02);
  font-size: 13px;
}

.policy ul {
  margin: 6px 0 0 0;
  padding-left: 20px;
}

.policy li {
  margin: 4px 0;
}

.muted {
  opacity: 0.75;
}

.mono {
  font-family: "SF Mono", Monaco, Consolas, monospace;
  font-size: 12px;
  background: rgba(0, 0, 0, 0.05);
  padding: 1px 4px;
  border-radius: 3px;
}
</style>
