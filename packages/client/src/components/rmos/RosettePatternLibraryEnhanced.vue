<template>
  <div class="border rounded-lg p-3 space-y-2 text-xs">
    <div class="flex items-center justify-between">
      <h2 class="text-sm font-semibold">
        Rosette Pattern Library
      </h2>
      <div class="flex gap-1">
        <button
          class="border rounded px-2 py-1 hover:bg-blue-50 text-blue-600 border-blue-300 text-xs font-medium"
          @click="showPresets = true"
        >
          📚 Browse Presets
        </button>
        <button
          class="border rounded px-2 py-1 hover:bg-gray-100"
          @click="createQuickPattern"
        >
          + New
        </button>
      </div>
    </div>

    <!-- Preset Browser Modal -->
    <Teleport to="body">
      <div
        v-if="showPresets"
        class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]"
        @click.self="showPresets = false"
      >
        <div class="bg-white rounded-lg max-w-5xl w-full max-h-[90vh] overflow-hidden mx-4">
          <div class="flex items-center justify-between p-4 border-b">
            <h3 class="text-lg font-semibold">
              Rosette Preset Library
            </h3>
            <button
              class="text-gray-500 hover:text-gray-700 text-3xl leading-none font-light"
              @click="showPresets = false"
            >
              ×
            </button>
          </div>
          <RosettePresetBrowser
            @preset-selected="onPresetSelected"
          />
        </div>
      </div>
    </Teleport>

    <div
      v-if="store.loading"
      class="text-gray-500"
    >
      Loading patterns…
    </div>
    <div
      v-else-if="store.patterns.length === 0"
      class="text-gray-500"
    >
      No patterns yet. Click "Browse Presets" to get started!
    </div>

    <ul
      v-else
      class="divide-y"
    >
      <li
        v-for="p in store.patterns"
        :key="p.id"
        class="py-1 flex items-center justify-between"
      >
        <button
          class="text-left flex-1 hover:underline"
          :class="p.id === store.selectedPatternId ? 'font-semibold text-blue-600' : ''"
          @click="selectPattern(p.id)"
        >
          {{ p.name }}
          <span class="text-gray-400 text-[10px]">({{ p.ring_bands?.length || 0 }} rings)</span>
        </button>
        <button
          class="ml-2 text-red-500 hover:underline text-[10px]"
          @click="deletePattern(p.id)"
        >
          Delete
        </button>
      </li>
    </ul>

    <p
      v-if="store.error"
      class="text-red-600 text-xs"
    >
      {{ store.error }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { useConfirm } from '@/composables/useConfirm'
import { ref, onMounted } from 'vue'
import { useRosettePatternStore } from '@/stores/useRosettePatternStore'
import RosettePresetBrowser from '@/components/rmos/RosettePresetBrowser.vue'
import type { RosettePattern } from '@/models/rmos'

const { confirm } = useConfirm()

const emit = defineEmits<{
  (e: 'pattern-selected', pattern: RosettePattern | null): void
}>()

const store = useRosettePatternStore()
const showPresets = ref(false)

onMounted(async () => {
  await store.fetchPatterns()
  emit('pattern-selected', store.selectedPattern)
})

function selectPattern(id: string) {
  store.selectPattern(id)
  emit('pattern-selected', store.selectedPattern)
}

async function deletePattern(id: string) {
  if (!(await confirm(`Delete pattern ${id}?`))) return
  await store.deletePattern(id)
  emit('pattern-selected', store.selectedPattern)
}

async function createQuickPattern() {
  const id = prompt('Pattern id (e.g. rosette_default):')
  if (!id) return
  const name = prompt('Pattern name:', 'New Rosette Pattern') ?? 'New Rosette Pattern'
  const pattern: RosettePattern = {
    id,
    name,
    center_x_mm: 0,
    center_y_mm: 0,
    ring_bands: [],
    default_slice_thickness_mm: 1.0,
    default_passes: 1,
    default_workholding: 'vacuum',
    default_tool_id: 'saw_default',
  }
  await store.createPattern(pattern)
  emit('pattern-selected', store.selectedPattern)
}

async function onPresetSelected(pattern: Omit<RosettePattern, 'id'>) {
  // Generate unique ID for this preset
  const id = `preset_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`

  const fullPattern: RosettePattern = {
    ...pattern,
    id,
  }

  try {
    await store.createPattern(fullPattern)
  } catch (err) {
    // If API fails (backend not running), add to store locally
    console.warn('API unavailable, adding pattern locally:', err)
    store.patterns.push(fullPattern)
    store.selectedPatternId = fullPattern.id
  }

  showPresets.value = false
  emit('pattern-selected', store.selectedPattern)
}
</script>
