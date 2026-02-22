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
        >
          2D
        </button>
        <button
          class="px-2 py-1 rounded text-[11px] border"
          :class="mode==='3d' ? 'bg-gray-900 text-white' : 'bg-white'"
          @click="mode='3d'"
        >
          3D
        </button>
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
import CamBackplotViewer from '@/components/cam/CamBackplotViewer.vue'
import CamBackplot3D from './CamBackplot3D.vue'
import type { BackplotMove, BackplotOverlay } from '@/types/cam'

type Metrics = Record<string, any>

defineProps<{
  moves: BackplotMove[] | null
  stats?: { move_count?: number; time_s?: number } | null
  overlays?: BackplotOverlay[] | null
  simIssues?: any[] | null
  metrics?: Metrics | null
  units?: 'mm' | 'inch'
  toolD?: number
}>()

const mode = ref<'2d'|'3d'>('2d')
</script>
