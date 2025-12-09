<template>
  <section class="baseline-picker">
    <header class="picker-header">
      <div>
        <h3>Baselines</h3>
        <p class="hint">Select or capture a baseline snapshot for comparison.</p>
      </div>
      <button class="ghost" @click="loadBaselines" :disabled="loading">
        {{ loading ? 'Refreshing…' : 'Refresh' }}
      </button>
    </header>

    <div class="actions">
      <input
        v-model="filterText"
        class="text-input"
        type="text"
        placeholder="Search by name or tag"
      />
      <div class="save-group">
        <input
          v-model="newBaselineName"
          class="text-input"
          type="text"
          placeholder="Baseline name"
        />
        <textarea
          v-model="newBaselineNotes"
          class="text-input"
          rows="2"
          placeholder="Notes (optional)"
        />
        <button class="primary" @click="saveBaseline" :disabled="saveDisabled">
          {{ saving ? 'Saving…' : 'Save Current Geometry' }}
        </button>
      </div>
    </div>

    <div class="baseline-list" v-if="filteredBaselines.length">
      <article
        v-for="baseline in filteredBaselines"
        :key="baseline.id"
        class="baseline-item"
        :class="{ active: baseline.id === selectedId }"
        @click="selectBaseline(baseline)"
      >
        <div>
          <strong>{{ baseline.name }}</strong>
          <span class="created">{{ formatDate(baseline.created_at) }}</span>
        </div>
        <p class="baseline-meta" v-if="baseline.description">{{ baseline.description }}</p>
      </article>
    </div>
    <p v-else class="hint">No baselines yet. Save one using the form above.</p>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { CanonicalGeometry } from '@/utils/geometry'

interface BaselineRecord {
  id: string
  name: string
  type: string
  created_at: string
  description?: string | null
}

interface DiffSummary {
  segments_baseline: number
  segments_current: number
  added: number
  removed: number
  unchanged: number
  overlap_ratio: number
}

interface DiffSegment {
  id: string
  type: string
  status: 'added' | 'removed' | 'match'
  length: number
  path_index: number
}

interface DiffResult {
  baseline_id: string
  baseline_name: string
  summary: DiffSummary
  segments: DiffSegment[]
  baseline_geometry?: CanonicalGeometry
  current_geometry?: CanonicalGeometry
}

const props = defineProps<{
  currentGeometry: CanonicalGeometry | null
}>()

const emit = defineEmits<{
  (e: 'diff-computed', value: DiffResult | null): void
  (e: 'baseline-selected', value: BaselineRecord | null): void
}>()

const API_BASE = '/api/compare/lab'

const baselines = ref<BaselineRecord[]>([])
const loading = ref(false)
const saving = ref(false)
const selectedId = ref<string | null>(null)
const filterText = ref('')
const newBaselineName = ref('Baseline ' + new Date().toLocaleDateString())
const newBaselineNotes = ref('')

const filteredBaselines = computed(() => {
  if (!filterText.value) {
    return baselines.value
  }
  const needle = filterText.value.toLowerCase()
  return baselines.value.filter((baseline) => baseline.name.toLowerCase().includes(needle))
})

const saveDisabled = computed(() => saving.value || !props.currentGeometry)

function formatDate(value: string): string {
  try {
    return new Date(value).toLocaleString()
  } catch (_) {
    return value
  }
}

async function loadBaselines(): Promise<void> {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/baselines`)
    if (!res.ok) {
      throw new Error('Failed to load baselines')
    }
    baselines.value = await res.json()
  } catch (error) {
    console.error('Baseline list error', error)
  } finally {
    loading.value = false
  }
}

async function saveBaseline(): Promise<void> {
  if (!props.currentGeometry) {
    return
  }
  saving.value = true
  try {
    const res = await fetch(`${API_BASE}/baselines`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newBaselineName.value || 'Untitled Baseline',
        description: newBaselineNotes.value,
        geometry: props.currentGeometry,
      }),
    })
    if (!res.ok) {
      throw new Error('Unable to save baseline')
    }
    await loadBaselines()
  } catch (error) {
    console.error('Save baseline failed', error)
  } finally {
    saving.value = false
  }
}

async function fetchDiff(selectedBaseline: BaselineRecord): Promise<void> {
  if (!props.currentGeometry) {
    emit('diff-computed', null)
    return
  }
  try {
    const res = await fetch(`${API_BASE}/diff`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        baseline_id: selectedBaseline.id,
        current_geometry: props.currentGeometry,
      }),
    })
    if (!res.ok) {
      throw new Error('Diff request failed')
    }
    const diff: DiffResult = await res.json()
    emit('diff-computed', diff)
  } catch (error) {
    console.error('Diff error', error)
    emit('diff-computed', null)
  }
}

async function selectBaseline(record: BaselineRecord): Promise<void> {
  selectedId.value = record.id
  emit('baseline-selected', record)
  await fetchDiff(record)
}

watch(
  () => props.currentGeometry,
  async () => {
    if (selectedId.value) {
      const baseline = baselines.value.find((item) => item.id === selectedId.value)
      if (baseline) {
        await fetchDiff(baseline)
      }
    }
  },
  { deep: true },
)

onMounted(() => {
  loadBaselines()
})
</script>

<style scoped>
.baseline-picker {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  border-right: 1px solid #252525;
  padding-right: 1rem;
}

.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hint {
  margin: 0;
  font-size: 0.85rem;
  color: #a0a0a0;
}

.actions {
  display: flex;
  gap: 0.5rem;
  flex-direction: column;
}

.save-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.text-input {
  width: 100%;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  padding: 0.35rem 0.5rem;
  color: #f5f5f5;
}

.primary {
  background: #2563eb;
  color: #fff;
  border: none;
  padding: 0.45rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
}

.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ghost {
  background: transparent;
  border: 1px solid #444;
  color: #ddd;
  padding: 0.35rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
}

.baseline-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 420px;
  overflow-y: auto;
}

.baseline-item {
  padding: 0.5rem;
  border: 1px solid #333;
  border-radius: 6px;
  cursor: pointer;
}

.baseline-item.active {
  border-color: #2563eb;
}

.baseline-meta {
  margin: 0.25rem 0 0;
  color: #b3b3b3;
  font-size: 0.85rem;
}

.created {
  display: inline-block;
  margin-left: 0.5rem;
  color: #777;
  font-size: 0.8rem;
}
</style>
