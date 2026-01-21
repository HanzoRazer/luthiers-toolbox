<!--
================================================================================
Machine List View
================================================================================

PURPOSE:
--------
Read-only machine profiles list. Displays available CNC machines with their
capabilities (max feed, rapid, accel, jerk, safe Z). Used for reference when
selecting machine ID in CamPipelineRunner or checking machine specifications.

KEY ALGORITHMS:
--------------
1. Fetch on Mount:
   - onMounted() calls GET /cam/machines
   - Populates machines[] array with MachineProfile objects
   - Displays error if fetch fails

2. Grid Layout:
   - Responsive 2-column grid (md:grid-cols-2)
   - Card per machine with ID, name, specs
   - Tailwind styling for clean presentation

SAFETY RULES:
------------
1. Error handling: Catch fetch errors, display in red
2. Empty state: Show "No machines found" if machines.length === 0
3. Optional fields: Check existence before displaying (v-if="m.max_feed_xy")
4. Type safety: TypeScript interface ensures contract

INTEGRATION POINTS:
------------------
**Backend API:**
- GET /cam/machines - Returns MachineProfile[]

**Router:**
- Route: /machines
- Name: Machines
- Purpose: Reference for users configuring pipeline

**Data Flow:**
onMounted() → fetch /cam/machines → machines[] → v-for render cards

DEPENDENCIES:
------------
- Vue 3 Composition API (ref, onMounted)
- Tailwind CSS (grid, card styling)

TYPICAL WORKFLOW:
----------------
1. User navigates to /machines route
2. Component mounts
3. GET /cam/machines fetches profiles
4. Cards display with:
   - Machine name + ID
   - Max feed XY, rapid, accel, jerk, safe Z
5. User references values when configuring CamPipelineRunner

UI STRUCTURE:
------------
┌─ Machines (/machines) ────────────────────┐
│ Read-only machine profiles (alpha)         │
├────────────────────────────────────────────┤
│ ┌─ Machine Card 1 ──┐ ┌─ Machine Card 2 ─┐│
│ │ Tormach PCNC 440  │ │ ShopBot Desktop  ││
│ │ tormach_440       │ │ shopbot_desktop  ││
│ │ • max feed: 2000  │ │ • max feed: 1500 ││
│ │ • rapid: 3000     │ │ • rapid: 2500    ││
│ │ • accel: 400      │ │ • accel: 300     ││
│ │ • jerk: 800       │ │ • jerk: 600      ││
│ │ • safe Z: 5.0     │ │ • safe Z: 10.0   ││
│ └───────────────────┘ └──────────────────┘│
└────────────────────────────────────────────┘

FUTURE ENHANCEMENTS:
-------------------
- Edit machine profiles (admin mode)
- Create new machine profiles
- Export machine JSON
- Import machine JSON from file
- Clone machine profile
- Delete machine profile (with confirmation)
- Test machine connection (if networked CNC)
- Machine capability badges (3-axis, 4-axis, ATC)
================================================================================
-->

<template>
  <div class="p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">
          Machines
        </h2>
        <p class="text-[11px] text-gray-500">
          Read-only machine profiles (alpha)
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/machines</span>
    </div>

    <div
      v-if="error"
      class="text-xs text-red-600"
    >
      {{ error }}
    </div>

    <div
      v-if="machines.length"
      class="grid md:grid-cols-2 gap-3"
    >
      <div
        v-for="m in machines"
        :key="m.id"
        class="border rounded-lg p-3 bg-white text-[11px]"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-800">{{ m.name }}</span>
          <span class="text-[10px] text-gray-400">{{ m.id }}</span>
        </div>
        <ul class="space-y-0.5 text-gray-600">
          <li v-if="m.max_feed_xy">
            max feed XY: {{ m.max_feed_xy }}
          </li>
          <li v-if="m.rapid">
            rapid: {{ m.rapid }}
          </li>
          <li v-if="m.accel">
            accel: {{ m.accel }}
          </li>
          <li v-if="m.jerk">
            jerk: {{ m.jerk }}
          </li>
          <li v-if="m.safe_z_default">
            safe Z: {{ m.safe_z_default }}
          </li>
        </ul>
      </div>
    </div>

    <p
      v-else
      class="text-[11px] text-gray-500"
    >
      No machines found.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface MachineProfile {
  id: string
  name: string
  max_feed_xy?: number
  rapid?: number
  accel?: number
  jerk?: number
  safe_z_default?: number
  [key: string]: any
}

const machines = ref<MachineProfile[]>([])
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const resp = await fetch('/api/cam/machines')
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    machines.value = await resp.json() as MachineProfile[]
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  }
})
</script>
