<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <div class="text-[11px] text-gray-600">
        Backplot
        <span v-if="mode==='2d'">(2D)</span>
        <span v-else>(3D)</span>
      </div>
      <div class="flex items-center gap-2">
        <button
          class="px-2 py-1 rounded text-[11px] border"
          :class="mode==='2d' ? 'bg-gray-900 text-white' : 'bg-white'"
          @click="mode='2d'"
        >2D</button>
        <button
          class="px-2 py-1 rounded text-[11px] border"
          :class="mode==='3d' ? 'bg-gray-900 text-white' : 'bg-white'"
          @click="mode='3d'"
        >3D</button>
      </div>
    </div>

    <CamBackplotViewer
      v-if="mode==='2d'"
      :loops="[]"
      :moves="moves || []"
      :stats="stats"
      :overlays="overlays"
      :sim-issues="simIssues"
    />

    <CamBackplot3D
      v-else
      :moves="(moves || []) as any"
      :metrics="metrics as any"
      :units="units"
      :tool-d="toolD"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import CamBackplotViewer from './CamBackplotViewer.vue'
import CamBackplot3D from './CamBackplot3D.vue'

type Move = { code: string, x?: number, y?: number, z?: number, f?: number }
type SimIssue = any
type Stats = Record<string, any>
type Overlay = Record<string, any>
type Metrics = Record<string, any>

defineProps<{
  moves: Move[] | null
  stats?: Stats | null
  overlays?: Overlay[] | null
  simIssues?: SimIssue[] | null
  metrics?: Metrics | null
  units?: 'mm' | 'inch'
  toolD?: number
}>()

const mode = ref<'2d'|'3d'>('2d')
</script>
