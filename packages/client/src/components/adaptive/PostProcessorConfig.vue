<script setup lang="ts">
/**
 * PostProcessorConfig - Post-processor selection and adaptive feed settings
 * Extracted from AdaptivePocketLab.vue
 */

type AfMode = 'inherit' | 'comment' | 'inline_f' | 'mcode'

const props = defineProps<{
  postId: string
  posts: string[]
  afMode: AfMode
  afInlineMinF: number
  afMStart: string
  afMEnd: string
  disabled?: boolean
}>()

const emit = defineEmits<{
  'update:postId': [value: string]
  'update:afMode': [value: AfMode]
  'update:afInlineMinF': [value: number]
  'update:afMStart': [value: string]
  'update:afMEnd': [value: string]
  'savePreset': []
  'loadPreset': []
  'resetPreset': []
}>()
</script>

<template>
  <div class="post-config space-y-2">
    <label class="block text-sm font-medium">Post-Processor</label>
    <select
      :value="postId"
      :disabled="disabled"
      class="border px-2 py-1 rounded w-full"
      @change="emit('update:postId', ($event.target as HTMLSelectElement).value)"
    >
      <option
        v-for="p in posts"
        :key="p"
        :value="p"
      >
        {{ p }}
      </option>
    </select>

    <div class="flex gap-2 mt-2">
      <button
        class="px-2 py-1 border rounded"
        :disabled="disabled"
        @click="emit('savePreset')"
      >
        Save preset
      </button>
      <button
        class="px-2 py-1 border rounded"
        :disabled="disabled"
        @click="emit('loadPreset')"
      >
        Load preset
      </button>
      <button
        class="px-2 py-1 border rounded"
        :disabled="disabled"
        @click="emit('resetPreset')"
      >
        Reset
      </button>
    </div>

    <label class="block text-sm font-medium mt-2">
      Adaptive Feed Mode
      <span class="text-xs text-gray-500">Override</span>
    </label>
    <select
      :value="afMode"
      :disabled="disabled"
      class="border px-2 py-1 rounded w-full"
      @change="emit('update:afMode', ($event.target as HTMLSelectElement).value as AfMode)"
    >
      <option value="inherit">Inherit from post</option>
      <option value="comment">Comment mode</option>
      <option value="inline_f">Inline F</option>
      <option value="mcode">M-code</option>
    </select>

    <div
      v-if="afMode === 'inline_f'"
      class="pl-4"
    >
      <label class="block text-xs">Min feed (mm/min)</label>
      <input
        :value="afInlineMinF"
        type="number"
        step="50"
        :disabled="disabled"
        class="border px-2 py-1 rounded w-full"
        @input="emit('update:afInlineMinF', Number(($event.target as HTMLInputElement).value))"
      >
    </div>

    <div
      v-if="afMode === 'mcode'"
      class="pl-4 grid grid-cols-2 gap-2"
    >
      <div>
        <label class="block text-xs">M-code start</label>
        <input
          :value="afMStart"
          type="text"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          placeholder="M52 P"
          @input="emit('update:afMStart', ($event.target as HTMLInputElement).value)"
        >
      </div>
      <div>
        <label class="block text-xs">M-code end</label>
        <input
          :value="afMEnd"
          type="text"
          :disabled="disabled"
          class="border px-2 py-1 rounded w-full"
          placeholder="M52 P100"
          @input="emit('update:afMEnd', ($event.target as HTMLInputElement).value)"
        >
      </div>
    </div>
  </div>
</template>
