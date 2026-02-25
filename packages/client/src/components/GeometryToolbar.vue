<!--
  GeometryToolbar.vue - Floating Action Panel for Design → CAM Workflow
  
  CRITICAL SAFETY RULES:
  1. CAM routing MUST validate tool type before navigation
  2. Export operations MUST handle network failures gracefully
  3. Confirmation MUST be required before clearing geometry
  4. Status messages MUST auto-dismiss to prevent UI clutter
  5. Dropdown menu MUST close after selection to prevent stale state
  
  This toolbar provides:
  - Geometry metadata display (source, dimensions, path count)
  - Clipboard copy functionality
  - CAM tool routing with dropdown menu
  - DXF export with auto-download
  - Geometry clearing with confirmation
  - Status feedback with auto-dismiss
  
  Visibility:
  - Only shown when geometryStore.hasGeometry is true
  - Fixed position (bottom-right corner)
  - z-index: 1000 (above most UI elements)
  
  Usage:
  - Automatically appears when setGeometry() is called
  - Integrates with useGeometryStore for state management
  - Routes to CAM tools via Vue Router
-->

<template>
  <div
    v-if="geometryStore.hasGeometry"
    class="geometry-toolbar"
  >
    <!-- ======================================================================
         HEADER - Geometry Metadata Display
         ====================================================================== -->
    <div class="toolbar-header">
      <span class="geometry-icon">📐</span>
      <div class="geometry-info">
        <strong>{{ geometryStore.geometrySource }}</strong>
        <span class="geometry-meta">
          {{ geometryStore.pathCount }} paths • 
          {{ summary?.width }} × {{ summary?.height }} {{ geometryStore.geometryUnits }}
        </span>
      </div>
    </div>

    <!-- ======================================================================
         ACTIONS - Toolbar Button Row
         ====================================================================== -->
    <div class="toolbar-actions">
      <!-- Copy to Clipboard -->
      <button 
        class="btn-icon" 
        title="Copy geometry JSON to clipboard"
        :disabled="isLoading"
        @click="copyGeometry"
      >
        📋 Copy
      </button>

      <!-- Send to CAM Menu (Dropdown) -->
      <div class="dropdown">
        <button 
          class="btn-primary" 
          :disabled="isLoading"
          @click="toggleCAMMenu"
        >
          🔧 Send to CAM {{ camMenuOpen ? '▲' : '▼' }}
        </button>
        
        <div
          v-if="camMenuOpen"
          class="dropdown-menu"
        >
          <button 
            v-for="target in geometryStore.camTargets" 
            :key="target.tool"
            class="dropdown-item"
            @click="sendToCAM(target.tool)"
          >
            {{ target.icon }} {{ target.label }}
          </button>
        </div>
      </div>

      <!-- Export DXF -->
      <button 
        class="btn-secondary" 
        title="Export as DXF R12 for CAM software"
        :disabled="isLoading"
        @click="exportDXF"
      >
        📄 DXF
      </button>

      <!-- Clear Geometry (with confirmation) -->
      <button 
        class="btn-danger-outline" 
        title="Clear current geometry"
        :disabled="isLoading"
        @click="clearGeometry"
      >
        ✕
      </button>
    </div>

    <!-- ======================================================================
         STATUS - Feedback Messages
         ====================================================================== -->
    <div
      v-if="statusMessage"
      class="status-message"
      :class="statusType"
    >
      {{ statusMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * GeometryToolbar — Floating action panel for Design → CAM workflow.
 * Features: metadata display, clipboard copy, CAM routing, DXF export, clear.
 */
import { api } from '@/services/apiBase'
import { ref, computed } from 'vue'
import { useGeometryStore } from '@/stores/geometry'
import { useRouter } from 'vue-router'
import type { CAMTarget } from '@/stores/geometry'

type StatusType = 'success' | 'error' | 'info'

const geometryStore = useGeometryStore()
const router = useRouter()

const camMenuOpen = ref(false)
const statusMessage = ref('')
const statusType = ref<StatusType>('info')
const isLoading = ref(false)

const summary = computed(() => geometryStore.geometrySummary)

function toggleCAMMenu(): void {
  camMenuOpen.value = !camMenuOpen.value
}

/** Copy geometry JSON to clipboard with status feedback. */
async function copyGeometry(): Promise<void> {
  const success = await geometryStore.copyToClipboard()
  showStatus(
    success ? 'Copied to clipboard!' : 'Failed to copy',
    success ? 'success' : 'error'
  )
}

/** Send geometry to a CAM tool via sessionStorage and navigate. */
function sendToCAM(tool: string): void {
  geometryStore.sendToCAM(tool as any)
  camMenuOpen.value = false
  const target = geometryStore.camTargets.find((t: CAMTarget) => t.tool === tool)
  if (target) {
    router.push(target.route)
    showStatus(`Sent to ${target.label}`, 'success')
  }
}

/** Export geometry as DXF R12 with auto-download. Revokes blob URL after use. */
async function exportDXF(): Promise<void> {
  const geometry = geometryStore.currentGeometry
  if (!geometry) return

  isLoading.value = true
  try {
    const response = await api('/api/geometry/export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        geometry,
        format: 'dxf',
        filename: `${geometryStore.geometrySource}_${Date.now()}.dxf`
      })
    })
    if (response.ok) {
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${geometryStore.geometrySource}.dxf`
      a.click()
      URL.revokeObjectURL(url)
      showStatus('DXF exported!', 'success')
    } else {
      const errorText = await response.text()
      console.error('DXF export HTTP error:', response.status, errorText)
      showStatus(`DXF export failed (${response.status})`, 'error')
    }
  } catch (error) {
    console.error('DXF export network error:', error)
    showStatus('DXF export error (network)', 'error')
  } finally {
    isLoading.value = false
  }
}

/** Clear geometry with confirmation dialog. */
function clearGeometry(): void {
  if (confirm('Clear current geometry? This cannot be undone.')) {
    geometryStore.clearGeometry()
    showStatus('Geometry cleared', 'info')
  }
}

/** Show status message with 3-second auto-dismiss. */
function showStatus(message: string, type: StatusType): void {
  statusMessage.value = message
  statusType.value = type
  setTimeout(() => { statusMessage.value = '' }, 3000)
}
</script>

<style scoped>
/* Floating action panel — fixed bottom-right */
.geometry-toolbar {
  position: fixed;
  bottom: 20px;
  right: 20px;
  background: white;
  border: 2px solid #667eea;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  max-width: 400px;
  z-index: 1000;
}
.toolbar-header { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.geometry-icon  { font-size: 24px; }
.geometry-info  { display: flex; flex-direction: column; gap: 4px; }
.geometry-info strong { color: #333; font-size: 14px; }
.geometry-meta  { color: #666; font-size: 12px; }
.toolbar-actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* Buttons — shared base */
.btn-icon, .btn-primary, .btn-secondary, .btn-danger-outline {
  padding: 8px 12px; border-radius: 6px; border: none;
  cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.2s;
}
.btn-icon:disabled, .btn-primary:disabled,
.btn-secondary:disabled, .btn-danger-outline:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-icon                       { background: #f3f4f6; color: #374151; }
.btn-icon:hover:not(:disabled)  { background: #e5e7eb; }
.btn-primary                       { background: #667eea; color: white; }
.btn-primary:hover:not(:disabled)  { background: #5568d3; }
.btn-secondary                       { background: #10b981; color: white; }
.btn-secondary:hover:not(:disabled)  { background: #059669; }
.btn-danger-outline                       { background: transparent; color: #ef4444; border: 1px solid #ef4444; }
.btn-danger-outline:hover:not(:disabled)  { background: #fef2f2; }

/* Dropdown */
.dropdown      { position: relative; }
.dropdown-menu {
  position: absolute; bottom: 100%; left: 0; margin-bottom: 8px;
  background: white; border: 1px solid #e5e7eb; border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); min-width: 200px; z-index: 10;
}
.dropdown-item {
  width: 100%; padding: 10px 16px; text-align: left;
  background: none; border: none; cursor: pointer; font-size: 14px; transition: background 0.2s;
}
.dropdown-item:hover       { background: #f3f4f6; }
.dropdown-item:first-child { border-radius: 8px 8px 0 0; }
.dropdown-item:last-child  { border-radius: 0 0 8px 8px; }

/* Status */
.status-message          { margin-top: 12px; padding: 8px 12px; border-radius: 6px; font-size: 13px; text-align: center; }
.status-message.success  { background: #d1fae5; color: #065f46; }
.status-message.error    { background: #fee2e2; color: #991b1b; }
.status-message.info     { background: #dbeafe; color: #1e40af; }
</style>
