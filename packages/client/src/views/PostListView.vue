<!--
================================================================================
Post List View
================================================================================

PURPOSE:
--------
Read-only post-processor presets list. Displays available G-code post configs
with their settings (dialect, mode, line numbers). Used for reference when
selecting post ID in CamPipelineRunner or checking post specifications.

KEY ALGORITHMS:
--------------
1. Fetch on Mount:
   - onMounted() calls GET /cam/posts
   - Populates posts[] array with PostProfile objects
   - Displays error if fetch fails

2. Grid Layout:
   - Responsive 2-column grid (md:grid-cols-2)
   - Card per post with ID, name, specs
   - Tailwind styling for clean presentation

SAFETY RULES:
------------
1. Error handling: Catch fetch errors, display in red
2. Empty state: Show "No posts found" if posts.length === 0
3. Optional fields: Check existence before displaying (v-if="p.post")
4. Type safety: TypeScript interface ensures contract
5. Boolean display: line_numbers shown as 'on' or 'off'

INTEGRATION POINTS:
------------------
**Backend API:**
- GET /cam/posts - Returns PostProfile[]

**Router:**
- Route: /posts
- Name: Posts
- Purpose: Reference for users configuring pipeline

**Data Flow:**
onMounted() → fetch /cam/posts → posts[] → v-for render cards

DEPENDENCIES:
------------
- Vue 3 Composition API (ref, onMounted)
- Tailwind CSS (grid, card styling)

TYPICAL WORKFLOW:
----------------
1. User navigates to /posts route
2. Component mounts
3. GET /cam/posts fetches profiles
4. Cards display with:
   - Post name + ID
   - Dialect (GRBL, Mach4, LinuxCNC, PathPilot, MASSO)
   - Mode (standard, helical, etc.)
   - Line numbers (on/off)
5. User references values when configuring CamPipelineRunner

UI STRUCTURE:
------------
┌─ Posts (/posts) ───────────────────────────┐
│ Read-only post presets (alpha)             │
├─────────────────────────────────────────────┤
│ ┌─ Post Card 1 ────┐ ┌─ Post Card 2 ──────┐│
│ │ GRBL 1.1 CNC    │ │ Mach4 Standard     ││
│ │ GRBL            │ │ Mach4              ││
│ │ • dialect: GRBL │ │ • dialect: Mach4   ││
│ │ • mode: std     │ │ • mode: standard   ││
│ │ • line#: off    │ │ • line#: on        ││
│ └─────────────────┘ └────────────────────┘│
└─────────────────────────────────────────────┘

FUTURE ENHANCEMENTS:
-------------------
- Edit post profiles (admin mode)
- Create new post profiles
- Export post JSON
- Import post JSON from file
- Clone post profile
- Delete post profile (with confirmation)
- Preview post header/footer
- Test post with sample G-code
- Post capability badges (helical, arcs, trochoidal)
================================================================================
-->

<template>
  <div class="p-4 space-y-3">
    <div class="flex items-center justify-between">
      <div>
        <h2 class="text-sm font-semibold">
          Posts
        </h2>
        <p class="text-[11px] text-gray-500">
          Read-only post presets (alpha)
        </p>
      </div>
      <span class="text-[10px] text-gray-400">/posts</span>
    </div>

    <div
      v-if="error"
      class="text-xs text-red-600"
    >
      {{ error }}
    </div>

    <div
      v-if="posts.length"
      class="grid md:grid-cols-2 gap-3"
    >
      <div
        v-for="p in posts"
        :key="p.id"
        class="border rounded-lg p-3 bg-white text-[11px]"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-gray-800">{{ p.name }}</span>
          <span class="text-[10px] text-gray-400">{{ p.id }}</span>
        </div>
        <ul class="space-y-0.5 text-gray-600">
          <li v-if="p.post">
            dialect: {{ p.post }}
          </li>
          <li v-if="p.post_mode">
            mode: {{ p.post_mode }}
          </li>
          <li v-if="p.line_numbers !== undefined">
            line numbers: {{ p.line_numbers ? 'on' : 'off' }}
          </li>
        </ul>
      </div>
    </div>

    <p
      v-else
      class="text-[11px] text-gray-500"
    >
      No posts found.
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface PostProfile {
  id: string
  name: string
  post?: string
  post_mode?: string
  line_numbers?: boolean
  [key: string]: any
}

const posts = ref<PostProfile[]>([])
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const resp = await fetch('/api/cam/posts')
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(text || `HTTP ${resp.status}`)
    }
    posts.value = await resp.json() as PostProfile[]
  } catch (e: any) {
    error.value = e?.message ?? String(e)
  }
})
</script>
