<script setup lang="ts">
/**
 * PreviewLinkModePanel - Link mode toggle for N17 preview mode
 * Extracted from AdaptivePoly.vue
 */
defineProps<{
  linkMode: 'arc' | 'linear'
  busy: boolean
}>()

const emit = defineEmits<{
  'update:linkMode': [value: 'arc' | 'linear']
}>()
</script>

<template>
  <div>
    <label class="block text-xs font-medium text-gray-700 mb-1">
      Link Mode
    </label>
    <div class="flex gap-2">
      <button
        :class="[
          'flex-1 px-2 py-1.5 text-xs rounded border transition-colors',
          linkMode === 'arc'
            ? 'bg-gray-700 text-white border-gray-700'
            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
        ]"
        :disabled="busy"
        @click="emit('update:linkMode', 'arc')"
      >
        Arc (G2/G3)
      </button>
      <button
        :class="[
          'flex-1 px-2 py-1.5 text-xs rounded border transition-colors',
          linkMode === 'linear'
            ? 'bg-gray-700 text-white border-gray-700'
            : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
        ]"
        :disabled="busy"
        @click="emit('update:linkMode', 'linear')"
      >
        Linear (G1)
      </button>
    </div>
  </div>
</template>
