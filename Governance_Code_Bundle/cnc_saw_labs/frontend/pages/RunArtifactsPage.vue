<template>
  <RunArtifactPanel />
</template>

<script setup lang="ts">
import RunArtifactPanel from "@/components/runArtifacts/RunArtifactPanel.vue";
</script>
Optional route entry
Add to your router:
// packages/client/src/router/index.ts
{
  path: "/runs",
  name: "runs",
  component: () => import("@/pages/RunArtifactsPage.vue"),
}