<template>
  <div class="space-x-2">
    <button
      class="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
      @click="$emit('runFinish')"
    >
      Generate Finishing
    </button>
    <button
      v-if="hasResult"
      class="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
      @click="$emit('runSimBridge')"
    >
      Run Sim Bridge
    </button>
    <button
      v-if="hasSimBridgeOut"
      class="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700"
      @click="$emit('pushSnapshot')"
    >
      Push Snapshot to Timeline
    </button>

    <!-- Phase 24.7: Preset Comparison Button -->
    <button
      :disabled="isComparing"
      class="px-3 py-1 bg-orange-600 text-white rounded hover:bg-orange-700 disabled:opacity-50"
      @click="$emit('runPresetComparison')"
    >
      {{ isComparing ? "Comparing..." : "Run Preset Comparison" }}
    </button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  hasResult: boolean
  hasSimBridgeOut: boolean
  isComparing: boolean
}>()

defineEmits<{
  runFinish: []
  runSimBridge: []
  pushSnapshot: []
  runPresetComparison: []
}>()
</script>
