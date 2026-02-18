<script setup lang="ts">
/**
 * HudOverlayControls - L.2 HUD overlay toggles for toolpath visualization
 * Extracted from AdaptivePocketLab.vue
 */

const props = defineProps<{
  showTight: boolean
  showSlow: boolean
  showFillets: boolean
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:showTight': [value: boolean]
  'update:showSlow': [value: boolean]
  'update:showFillets': [value: boolean]
}>()
</script>

<template>
  <div class="hud-overlays border-t pt-4 space-y-2">
    <h3 class="font-semibold text-sm">
      HUD Overlays (L.2)
    </h3>
    <div class="flex items-center gap-2">
      <input
        id="showTight"
        :checked="showTight"
        type="checkbox"
        class="w-4 h-4"
        :disabled="disabled"
        @change="emit('update:showTight', ($event.target as HTMLInputElement).checked)"
      >
      <label
        for="showTight"
        class="text-sm"
      >🔴 Tight Radius</label>
    </div>
    <div class="flex items-center gap-2">
      <input
        id="showSlow"
        :checked="showSlow"
        type="checkbox"
        class="w-4 h-4"
        :disabled="disabled"
        @change="emit('update:showSlow', ($event.target as HTMLInputElement).checked)"
      >
      <label
        for="showSlow"
        class="text-sm"
      >🟠 Slowdown Zone</label>
    </div>
    <div class="flex items-center gap-2">
      <input
        id="showFillets"
        :checked="showFillets"
        type="checkbox"
        class="w-4 h-4"
        :disabled="disabled"
        @change="emit('update:showFillets', ($event.target as HTMLInputElement).checked)"
      >
      <label
        for="showFillets"
        class="text-sm"
      >🟢 Fillets</label>
    </div>
  </div>
</template>
