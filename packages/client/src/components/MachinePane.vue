<template>
  <div class="border rounded-md">
    <div class="p-2 border-b flex gap-2 items-center bg-gray-50">
      <span class="text-sm font-semibold">{{ slot }}</span>
      <select
        v-model="pid"
        class="border px-2 py-1 rounded grow"
      >
        <option :value="''">
          (none)
        </option>
        <option
          v-for="m in machines"
          :key="m.id"
          :value="m.id"
        >
          {{ m.title }}
        </option>
      </select>
      <button 
        class="px-2 py-1 text-xs border rounded hover:bg-white disabled:opacity-50" 
        :disabled="!pid || loading" 
        @click="run"
      >
        {{ loading ? '...' : 'Run' }}
      </button>
    </div>
    <div
      v-if="stats"
      class="p-3 text-sm"
    >
      <div class="font-semibold mb-2">
        {{ selectedMachine?.title }}
      </div>
      <div class="grid gap-1">
        <div class="flex justify-between">
          <span class="text-gray-600">Classic:</span>
          <b>{{ stats.time_s_classic }} s</b>
        </div>
        <div class="flex justify-between">
          <span class="text-gray-600">Jerk-aware:</span>
          <b>{{ stats.time_s_jerk }} s</b>
        </div>
        <div
          v-if="stats.time_s_jerk && stats.time_s_classic"
          class="flex justify-between text-xs text-gray-500"
        >
          <span>Speedup:</span>
          <span>{{ (stats.time_s_classic / stats.time_s_jerk).toFixed(2) }}x</span>
        </div>
      </div>
      
      <div class="mt-3 pt-3 border-t">
        <div class="text-xs font-semibold mb-1 text-gray-600">
          Bottlenecks (Caps)
        </div>
        <div class="grid grid-cols-2 gap-1 text-xs">
          <div class="flex items-center gap-1">
            <span
              class="inline-block w-3 h-3 rounded"
              style="background:#f59e0b"
            />
            Feed: {{ stats.caps.feed_cap }}
          </div>
          <div class="flex items-center gap-1">
            <span
              class="inline-block w-3 h-3 rounded"
              style="background:#14b8a6"
            />
            Accel: {{ stats.caps.accel }}
          </div>
          <div class="flex items-center gap-1">
            <span
              class="inline-block w-3 h-3 rounded"
              style="background:#ec4899"
            />
            Jerk: {{ stats.caps.jerk }}
          </div>
          <div class="flex items-center gap-1">
            <span class="inline-block w-3 h-3 rounded bg-gray-300" />
            None: {{ stats.caps.none }}
          </div>
        </div>
      </div>
      
      <div class="mt-3 pt-3 border-t text-xs text-gray-600">
        <div>Length: {{ stats.length_mm }} mm</div>
        <div>Moves: {{ stats.move_count }}</div>
      </div>
    </div>
    <div
      v-else-if="!pid"
      class="p-3 text-sm text-gray-500"
    >
      Select a machine and click Run
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{ 
  slot: string
  machines: any[]
  body: any 
}>()

const pid = ref<string>('')
const stats = ref<any>(null)
const loading = ref(false)

const selectedMachine = computed(() => 
  props.machines.find((m: any) => m.id === pid.value)
)

async function run() {
  if (!pid.value) return
  
  loading.value = true
  stats.value = null
  
  try {
    const b = JSON.parse(JSON.stringify(props.body))
    b.machine_profile_id = pid.value
    
    const r = await fetch('/api/cam/pocket/adaptive/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(b)
    })
    
    if (!r.ok) throw new Error(await r.text())
    
    const out = await r.json()
    stats.value = out.stats
  } catch (e: any) {
    alert(`Plan failed: ${e.message || e}`)
  } finally {
    loading.value = false
  }
}
</script>
