<template>
  <div class="mt-2 text-[10px] text-gray-700 flex flex-wrap gap-3">
    <div>
      <span class="font-semibold">Added avg:</span>
      <span class="ml-1 font-mono">
        A {{ pairStats.aAdded.toFixed(1) }} ·
        B {{ pairStats.bAdded.toFixed(1) }}
      </span>
      <span
        class="ml-1 px-1 rounded border"
        :class="pairStats.deltaAdded >= 0 ? 'border-emerald-500 text-emerald-700' : 'border-rose-500 text-rose-700'"
      >
        Δ B–A = {{ formatDelta(pairStats.deltaAdded) }}
      </span>
    </div>

    <div>
      <span class="font-semibold">Removed avg:</span>
      <span class="ml-1 font-mono">
        A {{ pairStats.aRemoved.toFixed(1) }} ·
        B {{ pairStats.bRemoved.toFixed(1) }}
      </span>
      <span
        class="ml-1 px-1 rounded border"
        :class="pairStats.deltaRemoved >= 0 ? 'border-emerald-500 text-emerald-700' : 'border-rose-500 text-rose-700'"
      >
        Δ B–A = {{ formatDelta(pairStats.deltaRemoved) }}
      </span>
    </div>

    <div>
      <span class="font-semibold">Unchanged avg:</span>
      <span class="ml-1 font-mono">
        A {{ pairStats.aUnchanged.toFixed(1) }} ·
        B {{ pairStats.bUnchanged.toFixed(1) }}
      </span>
      <span
        class="ml-1 px-1 rounded border border-gray-400 text-gray-700"
      >
        Δ B–A = {{ formatDelta(pairStats.deltaUnchanged) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
interface PairStats {
  aName: string
  bName: string
  aAdded: number
  bAdded: number
  deltaAdded: number
  aRemoved: number
  bRemoved: number
  deltaRemoved: number
  aUnchanged: number
  bUnchanged: number
  deltaUnchanged: number
}

defineProps<{
  pairStats: PairStats
}>()

function formatDelta(delta: number): string {
  if (delta === 0) return "0.0"
  const s = delta.toFixed(1)
  return delta > 0 ? `+${s}` : s
}
</script>
