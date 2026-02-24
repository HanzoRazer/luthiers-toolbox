<script setup lang="ts">
/**
 * BraceBatchPanel.vue
 * Batch bracing set panel with brace list and actions.
 */
import type { BraceProfileType } from '@/api/art-studio'
import type { BraceEntry, ProfileTypeInfo } from './bracingTypes'

defineProps<{
  braces: BraceEntry[]
  batchName: string
  loading: boolean
  profileTypes: ProfileTypeInfo[]
}>()

const emit = defineEmits<{
  'update:batchName': [value: string]
  'update:brace': [brace: BraceEntry]
  removeBrace: [id: number]
  calculateBatch: []
}>()
</script>

<template>
  <div class="space-y-4">
    <h2 class="text-lg font-semibold text-gray-800">
      Bracing Set
    </h2>

    <!-- Batch Name -->
    <div class="bg-gray-50 rounded-lg p-4">
      <label class="block text-xs text-gray-600 mb-1">Set Name</label>
      <input
        :value="batchName"
        type="text"
        class="w-full border rounded px-3 py-2 text-sm"
        placeholder="X-Brace Set"
        @input="emit('update:batchName', ($event.target as HTMLInputElement).value)"
      >
    </div>

    <!-- Brace List -->
    <div
      v-if="braces.length > 0"
      class="space-y-2"
    >
      <div
        v-for="brace in braces"
        :key="brace.id"
        class="bg-white border rounded-lg p-3"
      >
        <div class="flex justify-between items-start mb-2">
          <input
            :value="brace.name"
            type="text"
            class="font-medium text-sm border-b border-transparent hover:border-gray-300 focus:border-blue-500 outline-none"
            @input="emit('update:brace', { ...brace, name: ($event.target as HTMLInputElement).value })"
          >
          <button
            class="text-red-500 hover:text-red-700 text-sm"
            @click="emit('removeBrace', brace.id)"
          >
            ✕
          </button>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs">
          <div>
            <label class="text-gray-500">Profile</label>
            <select
              :value="brace.profile_type"
              class="w-full border rounded px-1 py-0.5"
              @change="emit('update:brace', { ...brace, profile_type: ($event.target as HTMLSelectElement).value as BraceProfileType })"
            >
              <option
                v-for="pt in profileTypes"
                :key="pt.value"
                :value="pt.value"
              >
                {{ pt.label }}
              </option>
            </select>
          </div>
          <div>
            <label class="text-gray-500">Length (mm)</label>
            <input
              :value="brace.length_mm"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, length_mm: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
          <div>
            <label class="text-gray-500">Width (mm)</label>
            <input
              :value="brace.width_mm"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, width_mm: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
          <div>
            <label class="text-gray-500">Height (mm)</label>
            <input
              :value="brace.height_mm"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, height_mm: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
        </div>

        <!-- Position for DXF export -->
        <div class="mt-2 grid grid-cols-3 gap-2 text-xs">
          <div>
            <label class="text-gray-500">X</label>
            <input
              :value="brace.x_mm"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, x_mm: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
          <div>
            <label class="text-gray-500">Y</label>
            <input
              :value="brace.y_mm"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, y_mm: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
          <div>
            <label class="text-gray-500">Angle (°)</label>
            <input
              :value="brace.angle_deg"
              type="number"
              class="w-full border rounded px-1 py-0.5"
              @input="emit('update:brace', { ...brace, angle_deg: Number(($event.target as HTMLInputElement).value) })"
            >
          </div>
        </div>

        <!-- Individual Result -->
        <div
          v-if="brace.result"
          class="mt-2 text-xs bg-gray-50 rounded p-2"
        >
          <span class="text-gray-600">Mass:</span>
          <span class="font-mono ml-1">{{ brace.result.mass_grams.toFixed(2) }}g</span>
          <span class="mx-2 text-gray-300">|</span>
          <span class="text-gray-600">Stiffness:</span>
          <span class="font-mono ml-1">{{
            brace.result.stiffness_estimate?.toFixed(0) || "—"
          }}</span>
        </div>
      </div>
    </div>

    <div
      v-else
      class="bg-gray-100 rounded-lg p-8 text-center text-gray-400"
    >
      <div class="text-4xl mb-2">
        📦
      </div>
      <div>No braces added yet</div>
      <div class="text-xs mt-1">
        Use the calculator on the left, then click "Add to Batch"
      </div>
    </div>

    <!-- Batch Action Buttons -->
    <div class="flex gap-3">
      <button
        class="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
        :disabled="loading || braces.length === 0"
        @click="emit('calculateBatch')"
      >
        Calculate All
      </button>
    </div>
  </div>
</template>
