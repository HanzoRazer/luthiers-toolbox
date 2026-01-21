<template>
  <div
    v-if="modelValue"
    class="fixed inset-0 z-50"
  >
    <div
      class="absolute inset-0 bg-black/40"
      @click="$emit('update:modelValue', false)"
    />
    <div class="absolute inset-0 sm:inset-10 bg-white rounded-xl shadow-xl flex flex-col">
      <div class="px-4 py-3 border-b flex items-center justify-between">
        <h3 class="text-lg font-semibold">
          Compare Machines (A/B/C)
        </h3>
        <button
          class="px-3 py-1 border rounded hover:bg-gray-50"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </button>
      </div>
      <div class="p-3 grid md:grid-cols-3 gap-3 overflow-y-auto">
        <MachinePane 
          v-for="slot in ['A', 'B', 'C']" 
          :key="slot" 
          :slot="slot" 
          :machines="machines" 
          :body="body"
        />
      </div>
      <div class="px-4 py-3 border-t bg-gray-50 text-sm text-gray-600">
        💡 <b>Tip:</b> Select different machines to see how accel/jerk/feed limits affect runtime and bottlenecks.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import MachinePane from './MachinePane.vue'

const props = defineProps<{ 
  modelValue: boolean
  machines: any[]
  body: any 
}>()

const emit = defineEmits<{ 
  (e: 'update:modelValue', v: boolean): void 
}>()
</script>
