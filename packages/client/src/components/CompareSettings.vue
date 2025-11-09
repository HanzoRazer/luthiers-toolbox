<template>
  <div v-if="modelValue" class="fixed inset-0 z-50">
    <div class="absolute inset-0 bg-black/40" @click="$emit('update:modelValue', false)"></div>
    <div class="absolute inset-0 sm:inset-8 bg-white rounded-xl shadow-xl flex flex-col">
      <!-- Header -->
      <div class="px-4 py-3 border-b flex items-center justify-between">
        <h3 class="text-lg font-semibold">Compare Settings: Baseline vs Recommendation</h3>
        <button 
          class="px-3 py-1 border rounded hover:bg-gray-100" 
          @click="$emit('update:modelValue', false)">
          Close
        </button>
      </div>

      <!-- Side-by-side NC previews -->
      <div class="grow grid md:grid-cols-2 gap-0 overflow-hidden">
        <PreviewPane 
          title="Baseline" 
          :text="baselineNc" 
          mode="baseline" 
          @make-default="()=>{}"
        />
        <PreviewPane 
          title="Recommendation" 
          :text="optNc" 
          mode="opt" 
          @make-default="()=>{}"
        />
      </div>

      <!-- Footer with time comparison -->
      <div class="px-4 py-2 border-t text-sm flex gap-6 bg-slate-50">
        <div>
          Baseline time: <b>{{ baselineTime.toFixed(1) }} s</b>
        </div>
        <div>
          Recommended time: <b>{{ optTime.toFixed(1) }} s</b>
        </div>
        <div class="ml-auto">
          Improvement: 
          <b :class="improvement > 0 ? 'text-green-600' : 'text-gray-500'">
            {{ improvement > 0 ? '-' : '' }}{{ Math.abs(improvement).toFixed(1) }}%
          </b>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import PreviewPane from './PreviewPane.vue'

const props = defineProps<{
  modelValue: boolean
  baselineNc: string
  optNc: string
  baselineTime: number
  optTime: number
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
}>()

const improvement = computed(() => {
  if (props.baselineTime === 0) return 0
  return ((props.baselineTime - props.optTime) / props.baselineTime) * 100
})
</script>
