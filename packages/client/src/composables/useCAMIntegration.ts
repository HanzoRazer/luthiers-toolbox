/**
 * Composable for Design → CAM Integration
 * 
 * CRITICAL SAFETY RULES:
 * 1. All geometry MUST be validated before sending to store
 * 2. Tool names MUST be explicitly typed (no loose strings)
 * 3. Event listeners MUST be properly cleaned up to prevent memory leaks
 * 4. Pending geometry MUST be cleared after retrieval to prevent stale data
 * 5. All metadata MUST include source and timestamp
 * 
 * This composable enables "Send to CAM" functionality in design tool components,
 * providing a standardized interface for geometry transfer between design tools
 * (Bridge Calculator, Rosette Designer) and CAM processors (Adaptive Pocketing, etc.).
 * 
 * Usage Example:
 * ```typescript
 * // In design tool component:
 * const { sendToCAMTool } = useCAMIntegration({ toolName: 'BridgeCalculator' })
 * sendToCAMTool(designGeometry, 'adaptive')
 * 
 * // In CAM tool component:
 * const { pendingGeometry } = useCAMIntegration({ autoReceive: true })
 * watch(pendingGeometry, (geo) => { if (geo) processGeometry(geo) })
 * ```
 */

import { ref, onMounted, onUnmounted } from 'vue'
import { useGeometryStore, type GeometryData } from '@/stores/geometry'

// =============================================================================
// TYPE DEFINITIONS
// =============================================================================

/**
 * CAM tool identifier (explicit type for routing).
 * 
 * Available Tools:
 * - helical: Helical hole drilling with ramping
 * - adaptive: Adaptive pocket clearing
 * - vcarve: V-bit engraving
 * - relief: 3D relief mapping
 * - svg-editor: SVG path editing
 */
export type CAMToolType = 'helical' | 'adaptive' | 'vcarve' | 'relief' | 'svg-editor'

/**
 * Configuration options for CAM integration composable.
 * 
 * Options:
 * - autoReceive: If true, automatically calls receivePendingGeometry() on mount
 * - toolName: Design tool name for metadata (e.g., 'BridgeCalculator')
 */
export interface CAMIntegrationOptions {
  autoReceive?: boolean      // Auto-load pending geometry on mount
  toolName?: string           // Name of the design tool (for metadata)
}

// =============================================================================
// COMPOSABLE IMPLEMENTATION
// =============================================================================

/**
 * Use CAM integration features in design or CAM tool components.
 * 
 * Features:
 * - Send geometry to store with automatic metadata enrichment
 * - Route geometry to specific CAM tools
 * - Receive pending geometry from other tools
 * - Listen for geometry update/clear events
 * - Automatic cleanup of event listeners on unmount
 * 
 * Args:
 *   options: Configuration with autoReceive and toolName
 * 
 * Returns:
 *   Reactive state and action functions
 * 
 * Example:
 *   const { sendToCAMTool, pendingGeometry } = useCAMIntegration({ 
 *     toolName: 'BridgeCalculator', 
 *     autoReceive: false 
 *   })
 */
export function useCAMIntegration(options: CAMIntegrationOptions = {}) {
  const geometryStore = useGeometryStore()
  
  /** Pending geometry received from routing (null if none) */
  const pendingGeometry = ref<GeometryData | null>(null)

  // ===========================================================================
  // ACTIONS - GEOMETRY SENDING
  // ===========================================================================

  /**
   * Send design geometry to geometry store with metadata enrichment.
   * 
   * Process:
   * 1. Merge provided geometry with enriched metadata
   * 2. Add source (from arg or options.toolName)
   * 3. Add/update timestamp
   * 4. Call geometryStore.setGeometry() (triggers validation)
   * 
   * Args:
   *   geometry: Complete geometry data structure
   *   source: Optional source override (defaults to options.toolName)
   * 
   * Side Effects:
   * - Adds geometry to store history
   * - Emits 'geometry-updated' event
   * 
   * Example:
   *   sendToGeometryStore({
   *     units: 'mm',
   *     paths: [{type: 'line', x1: 0, y1: 0, x2: 100, y2: 0}]
   *   }, 'BridgeCalculator')
   */
  function sendToGeometryStore(geometry: GeometryData, source?: string): void {
    const enrichedGeometry: GeometryData = {
      ...geometry,
      metadata: {
        ...geometry.metadata,
        source: source || options.toolName || 'Unknown',
        timestamp: new Date().toISOString()
      }
    }
    
    geometryStore.setGeometry(enrichedGeometry)
  }

  /**
   * Send geometry to store and route to specific CAM tool.
   * 
   * Process:
   * 1. Call sendToGeometryStore() to store with metadata
   * 2. Call geometryStore.sendToCAM() to route to tool
   * 3. Target tool receives via receivePendingGeometry()
   * 
   * Args:
   *   geometry: Complete geometry data structure
   *   tool: Target CAM tool identifier (explicit type)
   *   source: Optional source override
   * 
   * Side Effects:
   * - Stores geometry in sessionStorage
   * - Emits 'send-to-cam' event with route information
   * - Target CAM tool can retrieve via receivePendingGeometry()
   * 
   * Example:
   *   sendToCAMTool(bridgeGeometry, 'adaptive', 'BridgeCalculator')
   *   // Routes to /lab/adaptive with geometry
   */
  function sendToCAMTool(
    geometry: GeometryData, 
    tool: CAMToolType,
    source?: string
  ): void {
    sendToGeometryStore(geometry, source)
    geometryStore.sendToCAM(tool)
  }

  // ===========================================================================
  // ACTIONS - GEOMETRY RECEIVING
  // ===========================================================================

  /**
   * Receive pending geometry from CAM routing.
   * 
   * Process:
   * 1. Call geometryStore.receivePendingCAMGeometry()
   * 2. If geometry exists, store in pendingGeometry ref
   * 3. Clear sessionStorage entry (one-time retrieval)
   * 
   * Returns:
   *   GeometryData if pending geometry exists, null otherwise
   * 
   * Side Effects:
   * - Updates pendingGeometry ref
   * - Clears sessionStorage 'pending_cam_geometry'
   * 
   * Notes:
   * - Should be called by CAM tools on mount or manually
   * - Returns null if already retrieved or no pending geometry
   * 
   * Example:
   *   onMounted(() => {
   *     const geo = receivePendingGeometry()
   *     if (geo) loadIntoEditor(geo)
   *   })
   */
  function receivePendingGeometry(): GeometryData | null {
    const geometry = geometryStore.receivePendingCAMGeometry()
    if (geometry) {
      pendingGeometry.value = geometry
      return geometry
    }
    return null
  }

  // ===========================================================================
  // EVENT HANDLING
  // ===========================================================================

  /**
   * Handle geometry update events from store.
   * 
   * Updates pendingGeometry ref when geometry changes in store.
   * Registered in onMounted(), cleaned up in onUnmounted().
   */
  const geometryUpdateHandler = (event: Event): void => {
    const customEvent = event as CustomEvent
    if (customEvent.detail?.geometry) {
      pendingGeometry.value = customEvent.detail.geometry
    }
  }

  /**
   * Handle geometry clear events from store.
   * 
   * Resets pendingGeometry ref to null when store is cleared.
   * Registered in onMounted(), cleaned up in onUnmounted().
   */
  const geometryClearedHandler = (): void => {
    pendingGeometry.value = null
  }

  // ===========================================================================
  // LIFECYCLE HOOKS
  // ===========================================================================

  onMounted(() => {
    // Auto-receive pending geometry if enabled
    if (options.autoReceive) {
      receivePendingGeometry()
    }

    // Listen for geometry updates (MUST be cleaned up to prevent leaks)
    window.addEventListener('geometry-updated', geometryUpdateHandler)
    window.addEventListener('geometry-cleared', geometryClearedHandler)
  })

  onUnmounted(() => {
    // CRITICAL: Remove event listeners to prevent memory leaks
    window.removeEventListener('geometry-updated', geometryUpdateHandler)
    window.removeEventListener('geometry-cleared', geometryClearedHandler)
  })

  return {
    // State
    pendingGeometry,
    
    // Store access
    geometryStore,
    
    // Actions
    sendToGeometryStore,
    sendToCAMTool,
    receivePendingGeometry
  }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Convert common design tool formats to standardized GeometryData.
 * 
 * Supported Input Formats:
 * 1. Array of points: [[x1,y1], [x2,y2], ...] → polyline
 * 2. Circle/Arc object: {type: 'circle', cx, cy, r, ...} → arc
 * 3. Line object: {type: 'line', x1, y1, x2, y2} → line
 * 4. GeometryPath (pass-through)
 * 
 * Args:
 *   paths: Array of path objects in various formats
 *   units: Output units ('mm' or 'inch', defaults to 'mm')
 *   source: Optional source tool name for metadata
 * 
 * Returns:
 *   GeometryData with standardized paths and metadata
 * 
 * Notes:
 * - Polylines are automatically marked as closed
 * - Arc angles default to full circle (0 to 360)
 * - Timestamp is automatically added
 * 
 * Example:
 *   const geometry = convertToGeometryData(
 *     [
 *       [[0,0], [100,0], [100,60], [0,60]],  // Rectangle as polyline
 *       {type: 'circle', cx: 50, cy: 30, r: 10}  // Hole
 *     ],
 *     'mm',
 *     'BridgeCalculator'
 *   )
 */
export function convertToGeometryData(
  paths: any[], 
  units: 'mm' | 'inch' = 'mm',
  source?: string
): GeometryData {
  return {
    units,
    paths: paths.map((path: any) => {
      // Handle different path formats
      if (Array.isArray(path)) {
        // Array of points [[x1,y1], [x2,y2], ...] → polyline
        return {
          type: 'polyline' as const,
          points: path,
          closed: true
        }
      } else if (path.type === 'circle' || path.type === 'arc') {
        // Arc/circle format → arc
        return {
          type: 'arc' as const,
          cx: path.cx || path.centerX,
          cy: path.cy || path.centerY,
          r: path.r || path.radius,
          startAngle: path.startAngle || 0,
          endAngle: path.endAngle || 360
        }
      } else if (path.type === 'line') {
        // Line format → line
        return {
          type: 'line' as const,
          x1: path.x1,
          y1: path.y1,
          x2: path.x2,
          y2: path.y2
        }
      } else {
        // Pass through if already in correct GeometryPath format
        return path
      }
    }),
    metadata: {
      source,
      timestamp: new Date().toISOString()
    }
  }
}
