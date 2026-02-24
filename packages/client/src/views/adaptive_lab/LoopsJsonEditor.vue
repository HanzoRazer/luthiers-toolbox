<template>
  <div class="border rounded-lg p-3 bg-white space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        Loops JSON
      </h3>
      <button
        class="px-2 py-1 rounded border border-gray-300 text-[11px]"
        @click="$emit('load-demo')"
      >
        Load demo loops
      </button>
    </div>
    <textarea
      :value="modelValue"
      class="w-full h-64 border rounded px-2 py-1 text-[11px] font-mono"
      spellcheck="false"
      @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
}>()

defineEmits<{
  'update:modelValue': [value: string]
  'load-demo': []
}>()
</script>
