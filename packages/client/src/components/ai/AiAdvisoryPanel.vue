<template>
  <section class="ai-panel">
    <h3>AI Advisory (Draft)</h3>
    <div v-if="store.loading">Running…</div>
    <div v-if="store.error" class="err">{{ store.error }}</div>
    <pre v-if="store.advisory">{{ store.advisory }}</pre>
    <p class="note">
      Advisory content is informational only and must be reviewed.
    </p>
  </section>
</template>

<script setup lang="ts">
import { useAiAdvisoryStore } from "@/stores/aiAdvisoryStore";
const store = useAiAdvisoryStore();
</script>

<style scoped>
.ai-panel { border: 1px solid #444; padding: 0.75rem; }
.err { color: #f66; }
.note { font-size: 0.8rem; opacity: 0.7; }
</style>
