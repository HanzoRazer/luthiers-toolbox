<script setup lang="ts">
/**
 * ArtStudioUnified.vue
 *
 * Unified Art Studio view with tabbed access to:
 * - Rosette channel calculator
 * - Fretboard inlay designer
 * - Bracing section calculator
 */
import { ref } from "vue";
import ArtStudioRosette from "@/components/art/ArtStudioRosette.vue";
import ArtStudioInlay from "@/components/art/ArtStudioInlay.vue";
import ArtStudioBracing from "@/components/art/ArtStudioBracing.vue";

type TabId = "rosette" | "inlay" | "bracing";

const activeTab = ref<TabId>("rosette");

const tabs: { id: TabId; label: string; icon: string; desc: string }[] = [
  {
    id: "rosette",
    label: "Rosette",
    icon: "🎸",
    desc: "Soundhole rosette channel calculator",
  },
  {
    id: "inlay",
    label: "Inlays",
    icon: "◆",
    desc: "Fretboard inlay pattern designer",
  },
  {
    id: "bracing",
    label: "Bracing",
    icon: "🪵",
    desc: "Bracing section properties calculator",
  },
];
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b shadow-sm">
      <div class="max-w-7xl mx-auto px-4 py-4">
        <h1 class="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <span class="text-3xl">🎨</span>
          Art Studio
        </h1>
        <p class="text-sm text-gray-500 mt-1">
          Guitar design calculations and DXF export for CNC manufacturing
        </p>
      </div>
    </div>

    <!-- Tab Navigation -->
    <div class="bg-white border-b">
      <div class="max-w-7xl mx-auto px-4">
        <nav class="flex gap-1">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="px-4 py-3 text-sm font-medium border-b-2 transition-colors"
            :class="
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 bg-blue-50'
                : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'
            "
            @click="activeTab = tab.id"
          >
            <span class="mr-2">{{ tab.icon }}</span>
            {{ tab.label }}
          </button>
        </nav>
      </div>
    </div>

    <!-- Tab Description -->
    <div class="bg-gray-100 border-b">
      <div class="max-w-7xl mx-auto px-4 py-2">
        <p class="text-xs text-gray-600">
          {{ tabs.find((t) => t.id === activeTab)?.desc }}
        </p>
      </div>
    </div>

    <!-- Tab Content -->
    <div class="max-w-7xl mx-auto">
      <KeepAlive>
        <ArtStudioRosette v-if="activeTab === 'rosette'" />
        <ArtStudioInlay v-else-if="activeTab === 'inlay'" />
        <ArtStudioBracing v-else-if="activeTab === 'bracing'" />
      </KeepAlive>
    </div>

    <!-- Footer -->
    <div class="bg-white border-t mt-8">
      <div
        class="max-w-7xl mx-auto px-4 py-4 text-center text-xs text-gray-500"
      >
        <p>
          Art Studio • Luthier's Tool Box
          <span class="mx-2">•</span>
          DXF exports are R12 compatible for maximum CAM software compatibility
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Smooth tab transitions */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
