<template>
  <div>
    <div class="mb-2 text-xs text-gray-500">
      Inline SVG preview
    </div>
    <div
      class="border rounded bg-white p-2 max-h-[300px] overflow-auto"
      v-html="svgText"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{ svgText: string }>()
</script>
