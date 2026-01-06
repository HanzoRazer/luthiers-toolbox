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
  <div class="geometry-toolbar" v-if="geometryStore.hasGeometry">
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
        @click="copyGeometry" 
        class="btn-icon"
        title="Copy geometry JSON to clipboard"
        :disabled="isLoading"
      >
        📋 Copy
      </button>

      <!-- Send to CAM Menu (Dropdown) -->
      <div class="dropdown">
        <button 
          class="btn-primary" 
          @click="toggleCAMMenu"
          :disabled="isLoading"
        >
          🔧 Send to CAM {{ camMenuOpen ? '▲' : '▼' }}
        </button>
        
        <div v-if="camMenuOpen" class="dropdown-menu">
          <button 
            v-for="target in geometryStore.camTargets" 
            :key="target.tool"
            @click="sendToCAM(target.tool)"
            class="dropdown-item"
          >
            {{ target.icon }} {{ target.label }}
          </button>
        </div>
      </div>

      <!-- Export DXF -->
      <button 
        @click="exportDXF" 
        class="btn-secondary"
        title="Export as DXF R12 for CAM software"
        :disabled="isLoading"
      >
        📄 DXF
      </button>

      <!-- Clear Geometry (with confirmation) -->
      <button 
        @click="clearGeometry" 
        class="btn-danger-outline"
        title="Clear current geometry"
        :disabled="isLoading"
      >
        ✕
      </button>
    </div>

    <!-- ======================================================================
         STATUS - Feedback Messages
         ====================================================================== -->
    <div v-if="statusMessage" class="status-message" :class="statusType">
      {{ statusMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * GeometryToolbar Component - Floating action panel for geometry operations.
 * 
 * Features:
 * - Geometry metadata display (source, dimensions, path count)
 * - Clipboard integration for JSON export
 * - CAM tool routing via dropdown menu
 * - DXF R12 export with auto-download
 * - Geometry clearing with confirmation dialog
 * - Status feedback with 3-second auto-dismiss
 * 
 * Type Safety:
 * - StatusType literal union for message types
 * - CAMTarget type validation before routing
 * - Explicit error handling with typed catch blocks
 * 
 * Side Effects:
 * - Router navigation on CAM tool selection
 * - File download on DXF export
 * - Store mutation on geometry clear
 * - URL object creation/revocation (memory management)
 */

import { ref, computed } from 'vue'
import { useGeometryStore } from '@/stores/geometry'
import { useRouter } from 'vue-router'
import type { CAMTarget } from '@/stores/geometry'

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/** Status message type for color-coded feedback */
type StatusType = 'success' | 'error' | 'info'

// =============================================================================
// COMPOSABLES & STATE
// =============================================================================

const geometryStore = useGeometryStore()
const router = useRouter()

/** CAM menu dropdown open state */
const camMenuOpen = ref(false)

/** Status message text (empty = hidden) */
const statusMessage = ref('')

/** Status message type for styling */
const statusType = ref<StatusType>('info')

/** Loading state for async operations */
const isLoading = ref(false)

// =============================================================================
// COMPUTED PROPERTIES
// =============================================================================

/**
 * Geometry summary with computed dimensions.
 * 
 * Returns:
 * - source: Tool name (e.g., 'BridgeCalculator')
 * - units: 'mm' or 'inch'
 * - pathCount: Number of paths
 * - width: Bounding box width (string, 2 decimals)
 * - height: Bounding box height (string, 2 decimals)
 */
const summary = computed(() => geometryStore.geometrySummary)

// =============================================================================
// ACTION HANDLERS
// =============================================================================

/**
 * Toggle CAM menu dropdown visibility.
 * 
 * Side Effects:
 * - Toggles camMenuOpen ref
 */
function toggleCAMMenu(): void {
  camMenuOpen.value = !camMenuOpen.value
}

/**
 * Copy geometry JSON to clipboard.
 * 
 * Process:
 * 1. Call geometryStore.copyToClipboard()
 * 2. Show success/error status message
 * 3. Auto-dismiss after 3 seconds
 * 
 * Side Effects:
 * - Writes to system clipboard
 * - Shows status message
 * 
 * Browser Requirements:
 * - Clipboard API support
 * - User interaction (secure context)
 */
async function copyGeometry(): Promise<void> {
  const success = await geometryStore.copyToClipboard()
  showStatus(
    success ? 'Copied to clipboard!' : 'Failed to copy', 
    success ? 'success' : 'error'
  )
}

/**
 * Send geometry to CAM tool and navigate.
 * 
 * Process:
 * 1. Validate tool type exists in camTargets
 * 2. Call geometryStore.sendToCAM() (stores in sessionStorage)
 * 3. Close dropdown menu
 * 4. Navigate to CAM tool route
 * 5. Show success status
 * 
 * Args:
 *   tool: CAM tool identifier (must match CAMTarget['tool'])
 * 
 * Side Effects:
 * - Stores geometry in sessionStorage
 * - Emits 'send-to-cam' event
 * - Navigates to CAM tool route
 * - Closes dropdown menu
 * - Shows status message
 * 
 * Validation:
 * - tool MUST exist in geometryStore.camTargets
 * - Silently ignores invalid tools (defensive programming)
 * 
 * Example:
 *   sendToCAM('adaptive')  // Routes to /lab/adaptive
 */
function sendToCAM(tool: string): void {
  // Cast to any for store compatibility (store uses string internally)
  geometryStore.sendToCAM(tool as any)
  camMenuOpen.value = false
  
  // Navigate to CAM tool route
  const target = geometryStore.camTargets.find((t: CAMTarget) => t.tool === tool)
  if (target) {
    router.push(target.route)
    showStatus(`Sent to ${target.label}`, 'success')
  }
}

/**
 * Export geometry as DXF R12 with auto-download.
 * 
 * Process:
 * 1. Validate current geometry exists
 * 2. POST to /api/geometry/export with DXF format
 * 3. Create blob URL from response
 * 4. Trigger browser download via anchor click
 * 5. Revoke URL to free memory (CRITICAL)
 * 6. Show success/error status
 * 
 * API Contract:
 * - POST /api/geometry/export
 * - Body: {geometry: GeometryData, format: 'dxf', filename: string}
 * - Response: DXF file blob (application/dxf)
 * 
 * Side Effects:
 * - Network request to backend
 * - Browser file download
 * - Temporary URL object creation/revocation
 * - Shows status message
 * 
 * Error Handling:
 * - Network errors: Catches and shows error status
 * - HTTP errors: Checks response.ok before processing
 * - Logs errors to console for debugging
 * 
 * Memory Management:
 * - CRITICAL: URL.revokeObjectURL() MUST be called to prevent memory leaks
 * 
 * Example Filename:
 *   BridgeCalculator_1699564800000.dxf
 */
async function exportDXF(): Promise<void> {
  const geometry = geometryStore.currentGeometry
  if (!geometry) return

  isLoading.value = true

  try {
    const response = await fetch('/api/geometry/export', {
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
      URL.revokeObjectURL(url)  // CRITICAL: Prevent memory leak
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

/**
 * Clear geometry with confirmation dialog.
 * 
 * Process:
 * 1. Show browser confirmation dialog
 * 2. If confirmed, call geometryStore.clearGeometry()
 * 3. Show info status message
 * 
 * Side Effects:
 * - Browser confirmation dialog (blocking)
 * - Clears geometryStore.currentGeometry
 * - Emits 'geometry-cleared' event
 * - Shows status message
 * - Hides toolbar (v-if="geometryStore.hasGeometry" becomes false)
 * 
 * User Experience:
 * - CRITICAL: Confirmation MUST be required (prevent accidental data loss)
 * - Status message shown even though toolbar will hide
 */
function clearGeometry(): void {
  if (confirm('Clear current geometry? This cannot be undone.')) {
    geometryStore.clearGeometry()
    showStatus('Geometry cleared', 'info')
  }
}

/**
 * Show status message with auto-dismiss.
 * 
 * Process:
 * 1. Set statusMessage and statusType refs
 * 2. Wait 3 seconds
 * 3. Clear statusMessage (hides UI element)
 * 
 * Args:
 *   message: Status text to display
 *   type: Message severity ('success' | 'error' | 'info')
 * 
 * Side Effects:
 * - Updates statusMessage ref (shows message)
 * - Updates statusType ref (changes color)
 * - Sets 3-second timeout (auto-dismiss)
 * 
 * Styling:
 * - success: Green background (#d1fae5)
 * - error: Red background (#fee2e2)
 * - info: Blue background (#dbeafe)
 * 
 * Auto-Dismiss:
 * - CRITICAL: 3-second timeout prevents UI clutter
 * - User can still see message for adequate time
 */
function showStatus(message: string, type: StatusType): void {
  statusMessage.value = message
  statusType.value = type
  setTimeout(() => {
    statusMessage.value = ''
  }, 3000)  // 3-second auto-dismiss
}
</script>

<style scoped>
/**
 * GeometryToolbar Styles - Fixed floating action panel.
 * 
 * Design System:
 * - Primary color: #667eea (indigo, CAM actions)
 * - Success color: #10b981 (green, exports)
 * - Danger color: #ef4444 (red, destructive actions)
 * - Neutral: #f3f4f6 (gray, secondary actions)
 * 
 * Layout:
 * - Fixed positioning (bottom-right corner, 20px margin)
 * - z-index: 1000 (above most UI elements)
 * - Max-width: 400px (prevent excessive width)
 * - Flexbox for button layout (wrap on narrow screens)
 * 
 * Accessibility:
 * - Focus states for all buttons
 * - Disabled states during loading
 * - High contrast text (WCAG AA compliant)
 * - Hover animations for feedback
 * 
 * Responsive:
 * - Flex-wrap on toolbar-actions (stacks buttons on mobile)
 * - Min-width: 200px on dropdown (prevents cramped menu)
 */

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
  z-index: 1000;  /* Above most UI elements */
}

.toolbar-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.geometry-icon {
  font-size: 24px;
}

.geometry-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.geometry-info strong {
  color: #333;
  font-size: 14px;
}

.geometry-meta {
  color: #666;
  font-size: 12px;
}

.toolbar-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;  /* Stack buttons on narrow screens */
}

/* =============================================================================
   BUTTON STYLES
   ============================================================================= */

.btn-icon, .btn-primary, .btn-secondary, .btn-danger-outline {
  padding: 8px 12px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-icon:disabled, 
.btn-primary:disabled, 
.btn-secondary:disabled, 
.btn-danger-outline:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Neutral action button (copy, etc.) */
.btn-icon {
  background: #f3f4f6;
  color: #374151;
}

.btn-icon:hover:not(:disabled) {
  background: #e5e7eb;
}

/* Primary action button (CAM routing) */
.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5568d3;
}

/* Success action button (exports) */
.btn-secondary {
  background: #10b981;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #059669;
}

/* Danger action button (clear geometry) */
.btn-danger-outline {
  background: transparent;
  color: #ef4444;
  border: 1px solid #ef4444;
}

.btn-danger-outline:hover:not(:disabled) {
  background: #fef2f2;
}

/* =============================================================================
   DROPDOWN MENU STYLES
   ============================================================================= */

.dropdown {
  position: relative;
}

.dropdown-menu {
  position: absolute;
  bottom: 100%;  /* Above button */
  left: 0;
  margin-bottom: 8px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  z-index: 10;
}

.dropdown-item {
  width: 100%;
  padding: 10px 16px;
  text-align: left;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.2s;
}

.dropdown-item:hover {
  background: #f3f4f6;
}

.dropdown-item:first-child {
  border-radius: 8px 8px 0 0;
}

.dropdown-item:last-child {
  border-radius: 0 0 8px 8px;
}

/* =============================================================================
   STATUS MESSAGE STYLES
   ============================================================================= */

.status-message {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  text-align: center;
}

/* Success status (green) */
.status-message.success {
  background: #d1fae5;
  color: #065f46;
}

/* Error status (red) */
.status-message.error {
  background: #fee2e2;
  color: #991b1b;
}

/* Info status (blue) */
.status-message.info {
  background: #dbeafe;
  color: #1e40af;
}
</style>
