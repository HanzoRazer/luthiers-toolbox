<!--
Luthier's Tool Box - CNC Guitar Lutherie CAD/CAM Toolbox
PostManagerView - Post processor CRUD manager (N.0 Smart Post Configurator)

Repository: HanzoRazer/luthiers-toolbox
Updated: January 2025 (Phase 5 Part 2 - N.0 Integration)
-->

<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">
          Post Processor Manager
        </h2>
        <p class="text-[11px] text-gray-500">
          Create, edit, and manage custom CNC post-processor configurations
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/lab/posts (N.0)</span>
    </div>

    <!-- N.0 Smart Post Configurator Component -->
    <PostManager />
  </div>
</template>

<script setup lang="ts">
import PostManager from '@/components/PostManager.vue'
</script>
