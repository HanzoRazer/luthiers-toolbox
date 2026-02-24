<template>
  <div class="border rounded-lg p-3 bg-white flex items-center justify-between text-[11px]">
    <div>
      <p class="font-semibold text-gray-700">
        Send to PipelineLab / CompareLab
      </p>
      <p class="text-gray-500">
        Persist loops snapshot locally to reopen in other labs.
      </p>
    </div>
    <div class="flex gap-2">
      <button
        class="px-3 py-1.5 rounded border border-gray-300 text-gray-800"
        @click="$emit('open-compare')"
      >
        Open Compare Lab
      </button>
      <button
        class="px-3 py-1.5 rounded bg-gray-900 text-white"
        @click="$emit('open-pipeline')"
      >
        Open PipelineLab
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineEmits<{
  'open-compare': []
  'open-pipeline': []
}>()
</script>
