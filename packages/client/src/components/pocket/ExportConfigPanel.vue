<script setup lang="ts">
/**
 * ExportConfigPanel.vue - Export configuration and batch export
 *
 * Job name, export mode checkboxes, batch export button.
 *
 * Example:
 * ```vue
 * <ExportConfigPanel
 *   v-model:job-name="jobName"
 *   v-model:export-modes="exportModes"
 *   :has-moves="moves.length > 0"
 *   @batch-export="batchExport"
 * />
 * ```
 */

export interface ExportModes {
  comment: boolean;
  inline_f: boolean;
  mcode: boolean;
}

defineProps<{
  jobName: string;
  exportModes: ExportModes;
  hasMoves: boolean;
}>();

defineEmits<{
  "update:jobName": [value: string];
  "update:exportModes": [value: ExportModes];
  batchExport: [];
}>();
</script>

<template>
  <div class="space-y-2 pt-2 border-t">
    <div class="flex items-center gap-2">
      <label class="text-sm font-medium">Job name:</label>
      <input
        :value="jobName"
        placeholder="e.g., LP_top_pocket_R3"
        class="border px-2 py-1 rounded w-56 text-sm"
        @input="$emit('update:jobName', ($event.target as HTMLInputElement).value)"
      >
      <span class="text-xs text-gray-500">(optional filename stem)</span>
    </div>

    <div class="flex items-center gap-3 flex-wrap">
      <div class="flex items-center gap-2">
        <label class="text-sm font-medium">Export modes:</label>
        <label class="text-xs flex items-center gap-1">
          <input
            :checked="exportModes.comment"
            type="checkbox"
            class="w-3 h-3"
            @change="$emit('update:exportModes', { ...exportModes, comment: ($event.target as HTMLInputElement).checked })"
          >
          comment
        </label>
        <label class="text-xs flex items-center gap-1">
          <input
            :checked="exportModes.inline_f"
            type="checkbox"
            class="w-3 h-3"
            @change="$emit('update:exportModes', { ...exportModes, inline_f: ($event.target as HTMLInputElement).checked })"
          >
          inline_f
        </label>
        <label class="text-xs flex items-center gap-1">
          <input
            :checked="exportModes.mcode"
            type="checkbox"
            class="w-3 h-3"
            @change="$emit('update:exportModes', { ...exportModes, mcode: ($event.target as HTMLInputElement).checked })"
          >
          mcode
        </label>
      </div>
      <button
        class="px-3 py-1 border rounded bg-orange-50"
        :disabled="!hasMoves"
        @click="$emit('batchExport')"
      >
        Batch Export (subset ZIP)
      </button>
    </div>
  </div>
</template>
