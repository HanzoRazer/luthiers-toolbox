/**
 * Geometry Store - Design → CAM Workflow Integration
 * 
 * CRITICAL SAFETY RULES:
 * 1. All coordinates MUST be validated against MIN/MAX bounds
 * 2. Units MUST be explicitly typed as 'mm' | 'inch' (no loose strings)
 * 3. All geometry operations MUST preserve coordinate precision
 * 4. History size MUST be bounded to prevent memory issues
 * 5. All exports MUST include metadata with timestamp
 * 
 * This store enables seamless geometry transfer between toolbox design tools 
 * (Bridge Calculator, Rosette Designer) and Art Studio CAM features 
 * (Helical Ramping, Adaptive Pocketing, V-Carve, Relief Mapping).
 * 
 * Data Flow:
 * 1. Design tool → setGeometry() → currentGeometry
 * 2. currentGeometry → sendToCAM() → sessionStorage
 * 3. CAM tool → receivePendingCAMGeometry() → process
 */

import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

// =============================================================================
// VALIDATION CONSTANTS
// =============================================================================

/** Minimum coordinate value in mm (prevent coordinate overflow) */
const MIN_COORDINATE_MM = -10000.0

/** Maximum coordinate value in mm (prevent coordinate overflow) */
const MAX_COORDINATE_MM = 10000.0

/** Maximum number of paths in a geometry (prevent memory issues) */
const MAX_PATH_COUNT = 10000

/** Maximum number of points in a path (prevent memory issues) */
const MAX_POINTS_PER_PATH = 100000

/** Maximum history entries (prevent unbounded growth) */
const MAX_HISTORY_SIZE = 10

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * Geometry path segment representing line, arc, or polyline.
 * 
 * Path Types:
 * - line: Requires x1, y1, x2, y2
 * - arc: Requires cx, cy, r, startAngle, endAngle
 * - polyline: Requires points array
 */
export interface GeometryPath {
  type: 'line' | 'arc' | 'polyline'
  points?: number[][]        // [[x1,y1], [x2,y2], ...] for polylines
  x1?: number                // Line segment start X
  y1?: number                // Line segment start Y
  x2?: number                // Line segment end X
  y2?: number                // Line segment end Y
  cx?: number                // Arc center X
  cy?: number                // Arc center Y
  r?: number                 // Arc radius
  startAngle?: number        // Arc start angle (radians)
  endAngle?: number          // Arc end angle (radians)
  closed?: boolean           // Polyline closure flag
}

/**
 * Complete geometry data structure with metadata.
 * 
 * Units:
 * - Internal storage: Always validate coordinates
 * - Export format: Preserve original units
 * - CAM integration: Convert as needed per tool requirements
 */
export interface GeometryData {
  units: 'mm' | 'inch'       // MUST be explicit type (no loose strings)
  paths: GeometryPath[]
  metadata?: {
    source?: string          // e.g., 'BridgeCalculator', 'RosetteDesigner'
    timestamp?: string       // ISO 8601 format
    description?: string
    boundingBox?: {
      minX: number
      minY: number
      maxX: number
      maxY: number
    }
  }
}

/**
 * CAM target tool configuration for routing geometry to specialized processors.
 * 
 * Available Tools:
 * - helical: Helical hole drilling with ramping
 * - adaptive: Adaptive pocket clearing with variable stepover
 * - vcarve: V-bit engraving and carving
 * - relief: 3D relief mapping from images
 * - svg-editor: SVG path editing and manipulation
 */
export interface CAMTarget {
  tool: 'helical' | 'adaptive' | 'vcarve' | 'relief' | 'svg-editor' | 'compare-runs'
  label: string      // Display name
  icon: string       // Emoji or icon character
  route: string      // Vue Router path
}

// =============================================================================
// PINIA STORE DEFINITION
// =============================================================================

/**
 * Geometry Store - Central state management for Design → CAM workflow.
 * 
 * Features:
 * - Geometry storage with automatic bounding box calculation
 * - History management with size limits
 * - Import/export to JSON
 * - Clipboard integration
 * - CAM tool routing via sessionStorage
 * - Custom event emission for reactive updates
 * 
 * Usage Example:
 * ```typescript
 * const geoStore = useGeometryStore()
 * geoStore.setGeometry({
 *   units: 'mm',
 *   paths: [{type: 'line', x1: 0, y1: 0, x2: 100, y2: 0}],
 *   metadata: {source: 'BridgeCalculator'}
 * })
 * geoStore.sendToCAM('adaptive')
 * ```
 */
export const useGeometryStore = defineStore('geometry', () => {
  // ===========================================================================
  // STATE
  // ===========================================================================

  /** Current active geometry (null if no geometry loaded) */
  const currentGeometry = ref<GeometryData | null>(null)

  /** Geometry history stack (most recent first, bounded by MAX_HISTORY_SIZE) */
  const geometryHistory = ref<GeometryData[]>([])

  /** Maximum history size (prevent unbounded growth) */
  const maxHistorySize = MAX_HISTORY_SIZE

  /** Available CAM targets with routing information */
  const camTargets = ref<CAMTarget[]>([
    { tool: 'helical', label: 'Helical Ramping', icon: '🌀', route: '/lab/helical' },
    { tool: 'adaptive', label: 'Adaptive Pocketing', icon: '⚡', route: '/lab/adaptive' },
    { tool: 'vcarve', label: 'V-Carve', icon: '🎨', route: '/lab/vcarve' },
    { tool: 'relief', label: 'Relief Mapping', icon: '🗺️', route: '/lab/relief' },
    { tool: 'svg-editor', label: 'SVG Editor', icon: '✏️', route: '/lab/svg-editor' },
    { tool: 'compare-runs', label: 'Multi-Run Comparison', icon: '📊', route: '/lab/compare-runs' }
  ])

  // ===========================================================================
  // COMPUTED PROPERTIES
  // ===========================================================================

  /** True if geometry is currently loaded */
  const hasGeometry = computed(() => currentGeometry.value !== null)
  
  /** Source tool name (e.g., 'BridgeCalculator', 'RosetteDesigner') */
  const geometrySource = computed(() => 
    currentGeometry.value?.metadata?.source || 'Unknown'
  )

  /** Current geometry units ('mm' or 'inch') */
  const geometryUnits = computed(() => 
    currentGeometry.value?.units || 'mm'
  )

  /** Number of paths in current geometry */
  const pathCount = computed(() => 
    currentGeometry.value?.paths?.length || 0
  )

  /**
   * Bounding box of current geometry (auto-calculated if not provided).
   * 
   * Algorithm:
   * 1. Check metadata.boundingBox (if pre-calculated)
   * 2. Otherwise, iterate all paths and find min/max X/Y
   * 3. Handle points arrays (polylines) and individual coordinates (lines/arcs)
   * 
   * Returns:
   * - {minX, minY, maxX, maxY} if geometry exists
   * - null if no geometry loaded
   */
  const boundingBox = computed(() => {
    if (!currentGeometry.value || !currentGeometry.value.paths.length) {
      return null
    }
    
    // Auto-calculate if not provided in metadata
    if (currentGeometry.value.metadata?.boundingBox) {
      return currentGeometry.value.metadata.boundingBox
    }

    let minX = Infinity, minY = Infinity
    let maxX = -Infinity, maxY = -Infinity

    currentGeometry.value.paths.forEach((path: GeometryPath) => {
      if (path.points) {
        path.points.forEach((point: number[]) => {
          const [x, y] = point
          minX = Math.min(minX, x)
          minY = Math.min(minY, y)
          maxX = Math.max(maxX, x)
          maxY = Math.max(maxY, y)
        })
      }
      if (path.x1 !== undefined) {
        minX = Math.min(minX, path.x1, path.x2!)
        minY = Math.min(minY, path.y1!, path.y2!)
        maxX = Math.max(maxX, path.x1, path.x2!)
        maxY = Math.max(maxY, path.y1!, path.y2!)
      }
    })

    return { minX, minY, maxX, maxY }
  })

  /**
   * Geometry summary with computed dimensions.
   * 
   * Returns:
   * - source: Tool that generated geometry
   * - units: 'mm' or 'inch'
   * - pathCount: Number of paths
   * - width: Bounding box width (formatted to 2 decimals)
   * - height: Bounding box height (formatted to 2 decimals)
   */
  const geometrySummary = computed(() => {
    if (!currentGeometry.value) return null
    
    const bbox = boundingBox.value
    return {
      source: geometrySource.value,
      units: geometryUnits.value,
      pathCount: pathCount.value,
      width: bbox ? (bbox.maxX - bbox.minX).toFixed(2) : '0',
      height: bbox ? (bbox.maxY - bbox.minY).toFixed(2) : '0'
    }
  })

  // ===========================================================================
  // ACTIONS - GEOMETRY MANAGEMENT
  // ===========================================================================

  /**
   * Set current geometry and add to history.
   * 
   * Validation:
   * - Path count must be <= MAX_PATH_COUNT
   * - Points per path must be <= MAX_POINTS_PER_PATH
   * - Coordinates should be within MIN/MAX bounds (warning only)
   * 
   * Side Effects:
   * - Adds timestamp to metadata if missing
   * - Deep clones geometry to prevent mutation
   * - Emits 'geometry-updated' event for reactive components
   * - Adds to history stack (bounded by MAX_HISTORY_SIZE)
   * 
   * Args:
   *   geometry: Complete geometry data with units and paths
   * 
   * Throws:
   *   Error: If path count exceeds MAX_PATH_COUNT
   *   Error: If points per path exceeds MAX_POINTS_PER_PATH
   * 
   * Example:
   *   setGeometry({
   *     units: 'mm',
   *     paths: [{type: 'line', x1: 0, y1: 0, x2: 100, y2: 0}],
   *     metadata: {source: 'BridgeCalculator'}
   *   })
   */
  function setGeometry(geometry: GeometryData): void {
    // Validation
    if (geometry.paths.length > MAX_PATH_COUNT) {
      throw new Error(`Path count ${geometry.paths.length} exceeds maximum ${MAX_PATH_COUNT}`)
    }

    geometry.paths.forEach((path: GeometryPath, idx: number) => {
      if (path.points && path.points.length > MAX_POINTS_PER_PATH) {
        throw new Error(`Path ${idx} has ${path.points.length} points, exceeds maximum ${MAX_POINTS_PER_PATH}`)
      }

      // Coordinate bounds warning (non-fatal)
      const coords: number[] = []
      if (path.points) {
        path.points.forEach((point: number[]) => {
          const [x, y] = point
          coords.push(x, y)
        })
      }
      if (path.x1 !== undefined) coords.push(path.x1, path.y1!, path.x2!, path.y2!)
      if (path.cx !== undefined) coords.push(path.cx, path.cy!)

      coords.forEach((coord: number) => {
        if (coord < MIN_COORDINATE_MM || coord > MAX_COORDINATE_MM) {
          console.warn(`Coordinate ${coord} outside safe bounds [${MIN_COORDINATE_MM}, ${MAX_COORDINATE_MM}]`)
        }
      })
    })

    // Add timestamp if not provided
    if (!geometry.metadata) {
      geometry.metadata = {}
    }
    if (!geometry.metadata.timestamp) {
      geometry.metadata.timestamp = new Date().toISOString()
    }

    // Store current geometry (deep clone to prevent mutation)
    currentGeometry.value = JSON.parse(JSON.stringify(geometry))

    // Add to history (bounded stack)
    geometryHistory.value.unshift(JSON.parse(JSON.stringify(geometry)))
    if (geometryHistory.value.length > maxHistorySize) {
      geometryHistory.value.pop()
    }

    // Emit custom event for components listening
    window.dispatchEvent(new CustomEvent('geometry-updated', { 
      detail: { geometry: currentGeometry.value }
    }))
  }

  /**
   * Clear current geometry and emit event.
   * 
   * Side Effects:
   * - Sets currentGeometry to null
   * - Emits 'geometry-cleared' event
   * - Does NOT clear history (use loadFromHistory to restore)
   */
  function clearGeometry(): void {
    currentGeometry.value = null
    window.dispatchEvent(new CustomEvent('geometry-cleared'))
  }

  /**
   * Load geometry from history by index.
   * 
   * Args:
   *   index: History position (0 = most recent)
   * 
   * Side Effects:
   * - Sets currentGeometry to history entry (deep clone)
   * - Emits 'geometry-updated' event with fromHistory: true flag
   * 
   * Notes:
   * - Does NOT validate bounds (assumes history entries were validated)
   * - Silently ignores invalid indices
   */
  function loadFromHistory(index: number): void {
    if (index >= 0 && index < geometryHistory.value.length) {
      currentGeometry.value = JSON.parse(JSON.stringify(geometryHistory.value[index]))
      window.dispatchEvent(new CustomEvent('geometry-updated', { 
        detail: { geometry: currentGeometry.value, fromHistory: true }
      }))
    }
  }

  // ===========================================================================
  // ACTIONS - IMPORT/EXPORT
  // ===========================================================================

  /**
   * Export current geometry to JSON string.
   * 
   * Returns:
   *   Pretty-printed JSON with 2-space indentation
   * 
   * Example:
   *   const json = exportToJSON()
   *   console.log(json)  // {"units":"mm","paths":[...],"metadata":{...}}
   */
  function exportToJSON(): string {
    return JSON.stringify(currentGeometry.value, null, 2)
  }

  /**
   * Import geometry from JSON string with validation.
   * 
   * Validation:
   * - Must parse as valid JSON
   * - Must have 'units' field
   * - Must have 'paths' array
   * - Paths array must not exceed MAX_PATH_COUNT
   * 
   * Args:
   *   jsonString: JSON representation of GeometryData
   * 
   * Returns:
   *   true if import successful, false if validation fails
   * 
   * Side Effects:
   * - Calls setGeometry() on success (triggers validation and history)
   * - Logs errors to console on failure
   * 
   * Example:
   *   const success = importFromJSON('{"units":"mm","paths":[...]}')
   *   if (!success) console.error('Import failed')
   */
  function importFromJSON(jsonString: string): boolean {
    try {
      const geometry = JSON.parse(jsonString)
      
      // Basic validation
      if (!geometry.units || !geometry.paths || !Array.isArray(geometry.paths)) {
        throw new Error('Invalid geometry format: missing units or paths')
      }

      setGeometry(geometry as GeometryData)
      return true
    } catch (error) {
      console.error('Failed to import geometry:', error)
      return false
    }
  }

  /**
   * Copy current geometry to clipboard as JSON.
   * 
   * Returns:
   *   Promise<boolean> - true if copy successful, false if failed
   * 
   * Browser Requirements:
   * - Requires Clipboard API support
   * - May require user interaction (secure context)
   * 
   * Example:
   *   const copied = await copyToClipboard()
   *   if (copied) showToast('Copied to clipboard')
   */
  function copyToClipboard(): Promise<boolean> {
    if (!currentGeometry.value) return Promise.resolve(false)
    
    const json = exportToJSON()
    return navigator.clipboard.writeText(json)
      .then(() => true)
      .catch(() => false)
  }

  /**
   * Paste geometry from clipboard and import.
   * 
   * Returns:
   *   Promise<boolean> - true if paste and import successful, false if failed
   * 
   * Browser Requirements:
   * - Requires Clipboard API support
   * - May require user permission
   * 
   * Example:
   *   const pasted = await pasteFromClipboard()
   *   if (!pasted) showToast('Failed to paste')
   */
  async function pasteFromClipboard(): Promise<boolean> {
    try {
      const text = await navigator.clipboard.readText()
      return importFromJSON(text)
    } catch (error) {
      console.error('Failed to paste from clipboard:', error)
      return false
    }
  }

  // ===========================================================================
  // ACTIONS - CAM INTEGRATION
  // ===========================================================================

  /**
   * Send geometry to CAM tool via sessionStorage and event.
   * 
   * Workflow:
   * 1. Package geometry with target tool and timestamp
   * 2. Store in sessionStorage as 'pending_cam_geometry'
   * 3. Emit 'send-to-cam' event with target route
   * 4. CAM tool retrieves via receivePendingCAMGeometry()
   * 
   * Args:
   *   target: CAM tool identifier ('helical', 'adaptive', etc.)
   * 
   * Side Effects:
   * - Overwrites previous pending geometry
   * - Emits custom event with route information
   * - Does nothing if no geometry loaded or invalid target
   * 
   * Example:
   *   sendToCAM('adaptive')  // Routes to /lab/adaptive with geometry
   */
  function sendToCAM(target: CAMTarget['tool']): void {
    if (!currentGeometry.value) return

    // Store geometry for CAM tool to pick up
    const camData = {
      geometry: currentGeometry.value,
      targetTool: target,
      sentAt: new Date().toISOString()
    }

    // Store in sessionStorage for CAM tool retrieval
    sessionStorage.setItem('pending_cam_geometry', JSON.stringify(camData))

    // Emit event with target route
    const targetConfig = camTargets.value.find((t: CAMTarget) => t.tool === target)
    if (targetConfig) {
      window.dispatchEvent(new CustomEvent('send-to-cam', { 
        detail: { 
          geometry: currentGeometry.value,
          tool: target,
          route: targetConfig.route
        }
      }))
    }
  }

  /**
   * Retrieve pending geometry from CAM routing.
   * 
   * Workflow:
   * 1. Read 'pending_cam_geometry' from sessionStorage
   * 2. Parse JSON and extract geometry
   * 3. Clear sessionStorage entry (one-time retrieval)
   * 
   * Returns:
   *   GeometryData if pending geometry exists, null otherwise
   * 
   * Side Effects:
   * - Removes 'pending_cam_geometry' from sessionStorage after retrieval
   * - Logs errors to console if parsing fails
   * 
   * Notes:
   * - Should be called by CAM tools on mount/activation
   * - Returns null if already retrieved or no pending geometry
   * 
   * Example:
   *   // In CAM tool component:
   *   onMounted(() => {
   *     const pendingGeo = receivePendingCAMGeometry()
   *     if (pendingGeo) processGeometry(pendingGeo)
   *   })
   */
  function receivePendingCAMGeometry(): GeometryData | null {
    const pending = sessionStorage.getItem('pending_cam_geometry')
    if (!pending) return null

    try {
      const data = JSON.parse(pending)
      sessionStorage.removeItem('pending_cam_geometry') // Clear after retrieval
      return data.geometry
    } catch (error) {
      console.error('Failed to retrieve pending CAM geometry:', error)
      return null
    }
  }

  // ===========================================================================
  // STORE EXPORTS
  // ===========================================================================

  return {
    // State
    currentGeometry,
    geometryHistory,
    camTargets,
    
    // Computed
    hasGeometry,
    geometrySource,
    geometryUnits,
    pathCount,
    boundingBox,
    geometrySummary,
    
    // Actions
    setGeometry,
    clearGeometry,
    loadFromHistory,
    exportToJSON,
    importFromJSON,
    copyToClipboard,
    pasteFromClipboard,
    sendToCAM,
    receivePendingCAMGeometry
  }
})
