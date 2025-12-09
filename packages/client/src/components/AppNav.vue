<template>
  <header class="border-b bg-white">
    <div class="max-w-6xl mx-auto flex items-center justify-between px-4 py-2">
      <div class="flex items-center gap-3">
        <span class="font-semibold text-sm">
          Luthier's Tool Box
        </span>
        <span class="text-[10px] text-gray-400 uppercase tracking-wide">
          CAM / LAB
        </span>
      </div>

      <nav class="flex items-center gap-3 text-[11px]">
        <RouterLink
          to="/lab/bridge"
          class="px-2 py-1 rounded hover:bg-gray-100"
          active-class="bg-gray-900 text-white hover:bg-gray-900"
        >
          Bridge Lab
        </RouterLink>

        <RouterLink
          to="/lab/adaptive"
          class="px-2 py-1 rounded hover:bg-gray-100"
          active-class="bg-gray-900 text-white hover:bg-gray-900"
        >
          Adaptive Lab
        </RouterLink>

        <RouterLink
          to="/lab/pipeline"
          class="px-2 py-1 rounded hover:bg-gray-100"
          active-class="bg-gray-900 text-white hover:bg-gray-900"
        >
          Pipeline Lab
        </RouterLink>

        <!-- Saw Lab Dropdown -->
        <div class="relative" @mouseenter="showSawMenu = true" @mouseleave="showSawMenu = false">
          <button
            class="px-2 py-1 rounded hover:bg-gray-100 flex items-center gap-1"
            :class="{ 'bg-gray-900 text-white hover:bg-gray-900': isSawLabActive }"
          >
            Saw Lab
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          <div
            v-if="showSawMenu"
            class="absolute top-full left-0 mt-1 bg-white border rounded shadow-lg py-1 min-w-[140px] z-50"
          >
            <RouterLink
              to="/lab/saw/slice"
              class="block px-3 py-1.5 hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-600"
            >
              Slice
            </RouterLink>
            <RouterLink
              to="/lab/saw/batch"
              class="block px-3 py-1.5 hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-600"
            >
              Batch
            </RouterLink>
            <RouterLink
              to="/lab/saw/contour"
              class="block px-3 py-1.5 hover:bg-gray-100"
              active-class="bg-blue-50 text-blue-600"
            >
              Contour
            </RouterLink>
          </div>
        </div>

        <RouterLink
          to="/lab/risk-timeline"
          class="px-2 py-1 rounded hover:bg-gray-100"
          active-class="bg-gray-900 text-white hover:bg-gray-900"
        >
          Risk Timeline
        </RouterLink>

        <RouterLink
          to="/settings/cam"
          class="px-2 py-1 rounded hover:bg-gray-100"
          active-class="bg-gray-900 text-white hover:bg-gray-900"
        >
          CAM Settings
        </RouterLink>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const showSawMenu = ref(false)
const route = useRoute()

// Highlight Saw Lab button when any saw route is active
const isSawLabActive = computed(() => {
  return route.path.startsWith('/lab/saw/')
})
</script>
