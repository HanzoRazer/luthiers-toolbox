<template>
  <div class="art-studio-unified">
    <div class="header">
      <h2>🎨 Art Studio</h2>
      <p class="subtitle">
        Visual design tools for guitar decorative elements
      </p>
    </div>

    <!-- Tabs: Domain-based -->
    <div class="tabs">
      <button 
        v-for="domain in domains" 
        :key="domain.id"
        :class="{ active: activeTab === domain.id }"
        @click="activeTab = domain.id"
      >
        {{ domain.label }}
      </button>
    </div>

    <!-- Tab content -->
    <div class="tab-content">
      <RosetteDesigner 
        v-if="activeTab === 'rosette'" 
        @update:geometry="handleRosetteGeometryUpdate"
      />
      <div
        v-else-if="activeTab === 'headstock'"
        class="placeholder"
      >
        <h3>🎸 Headstock Design</h3>
        <p>Logo and inlay artwork design tools (Coming soon)</p>
      </div>
      <div
        v-else-if="activeTab === 'relief'"
        class="placeholder"
      >
        <h3>🗿 Relief Carving</h3>
        <p>3D relief pattern design from images (Coming soon)</p>
      </div>
      <!-- Phase 27.0 + 27.1 + 27.2: Compare Mode tab -->
      <div
        v-else-if="activeTab === 'compare'"
        class="compare-content"
      >
        <RosetteComparePanel
          :current-geometry="rosetteGeometry"
          :job-id="compareJobId"
          @update:job-id="(val: string) => { compareJobId = val }"
        />
        <RosetteCompareHistory
          lane="rosette"
          :job-id="compareJobId"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import RosetteDesigner from '../components/toolbox/RosetteDesigner.vue'
import RosetteComparePanel from '@/components/art/RosetteComparePanel.vue'
import RosetteCompareHistory from '@/components/art/RosetteCompareHistory.vue'
import { usePresetQueryBootstrap } from '@/composables/usePresetQueryBootstrap'

const activeTab = ref('rosette') // Start with Rosette (domain-first)

// Domain-based tabs (lutherie-specific design tools)
const domains = [
  { id: 'rosette', label: '🌹 Rosette' },
  { id: 'headstock', label: '🎸 Headstock' },
  { id: 'relief', label: '🗿 Relief' },
  { id: 'compare', label: '🔍 Compare' } // Phase 27.0: Compare Mode tab
]

// Phase 27.0: Track current rosette geometry for Compare Mode
const rosetteGeometry = ref<any | null>(null)

// Phase 27.2: Shared job ID for Compare Panel and History
const compareJobId = ref<string>("")

// Phase 27.0: Handle geometry updates from RosetteDesigner
function handleRosetteGeometryUpdate(geom: any) {
  rosetteGeometry.value = geom
}

// Phase 27.2: Initialize job ID from localStorage
onMounted(() => {
  const lastJobId = localStorage.getItem("ltb:compare:lastJobId")
  if (lastJobId) {
    compareJobId.value = lastJobId
  }
})

// Phase 28.2: Consume query params for deep linking
usePresetQueryBootstrap({
  onTab: (tab) => {
    activeTab.value = tab
  },
  onJobHint: (hint) => {
    if (!compareJobId.value) {
      compareJobId.value = hint
    }
  },
})
</script>

<style scoped>
.art-studio-unified {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.header {
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.subtitle {
  margin: 0.25rem 0 0;
  opacity: 0.9;
  font-size: 0.875rem;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f3f4f6;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}

.tabs button {
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.tabs button:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.tabs button.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
  font-weight: 600;
}

.tab-content {
  flex: 1;
  overflow: auto;
}

.compare-content {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.placeholder {
  padding: 3rem 1rem;
  text-align: center;
  background: #f9fafb;
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  margin: 1rem;
}

.placeholder h3 {
  margin: 0 0 0.5rem;
  color: #667eea;
  font-size: 1.5rem;
}

.placeholder p {
  color: #6b7280;
  margin: 0;
}
</style>
