<template>
  <div class="cam-production">
    <div class="cam-header">
      <h2>⚙️ CAM Production</h2>
      <p class="subtitle">
        CNC toolpath generation & export
      </p>
    </div>

    <!-- Sidebar Navigation -->
    <div class="cam-layout">
      <aside class="cam-sidebar">
        <button 
          v-for="tool in tools" 
          :key="tool.id"
          :class="{ active: activeTool === tool.id }"
          class="sidebar-btn"
          @click="activeTool = tool.id"
        >
          <span class="icon">{{ tool.icon }}</span>
          <span class="label">{{ tool.label }}</span>
        </button>
      </aside>

      <!-- Main Content Area -->
      <main class="cam-main">
        <!-- Pipeline Lab (Primary Workflow) -->
        <!-- <PipelineLabView v-if="activeTool === 'pipeline'" /> -->
        <div
          v-if="activeTool === 'pipeline'"
          class="p-4 space-y-4"
        >
          <div class="text-gray-500">
            Pipeline Lab temporarily disabled (file corrupted)
          </div>
          <PresetManagerPanel />
          <CompareRunsPanel />
        </div>
        
        <!-- Adaptive Pocket -->
        <AdaptiveLabView v-else-if="activeTool === 'adaptive'" />
        
        <!-- Art Studio (Nested) -->
        <ArtStudioUnified v-else-if="activeTool === 'art-studio'" />
        
        <!-- Machine Profiles -->
        <MachineListView v-else-if="activeTool === 'machines'" />
        
        <!-- Post Processors -->
        <PostListView v-else-if="activeTool === 'posts'" />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
// import PipelineLabView from './PipelineLabView.vue' // Temporarily disabled - file corrupted
import AdaptiveLabView from './AdaptiveLabView.vue'
import ArtStudioUnified from './ArtStudioUnified.vue'
import MachineListView from './MachineListView.vue'
import PostListView from './PostListView.vue'
import PresetManagerPanel from '@/cnc_production/PresetManagerPanel.vue'
import CompareRunsPanel from '@/cnc_production/CompareRunsPanel.vue'

const activeTool = ref('pipeline')

const tools = [
  { id: 'pipeline', icon: '⚙️', label: 'Pipeline Lab' },
  { id: 'adaptive', icon: '🔬', label: 'Adaptive Pocket' },
  { id: 'art-studio', icon: '🎨', label: 'Art Studio' },
  { id: 'machines', icon: '🏭', label: 'Machines' },
  { id: 'posts', icon: '📋', label: 'Posts' }
]
</script>

<style scoped>
.cam-production {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.cam-header {
  padding: 1rem 1.5rem;
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  color: white;
  border-bottom: 2px solid #2563eb;
}

.cam-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
}

.subtitle {
  margin: 0.25rem 0 0;
  opacity: 0.9;
  font-size: 0.875rem;
}

.cam-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.cam-sidebar {
  width: 200px;
  background: #f9fafb;
  border-right: 1px solid #e5e7eb;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.sidebar-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border: none;
  background: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  text-align: left;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.sidebar-btn:hover {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.sidebar-btn.active {
  background: #3b82f6;
  color: white;
  font-weight: 600;
  border-color: #2563eb;
}

.sidebar-btn .icon {
  font-size: 1.25rem;
}

.sidebar-btn .label {
  flex: 1;
}

.cam-main {
  flex: 1;
  overflow: auto;
  background: white;
}
</style>
