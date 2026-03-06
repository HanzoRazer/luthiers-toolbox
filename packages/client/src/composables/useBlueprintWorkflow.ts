/**
 * useBlueprintWorkflow - Composable for Blueprint Lab 4-phase workflow
 *
 * Phase 1: AI Analysis (Claude Sonnet 4)
 * Phase 1.5: Calibration (PPI detection)
 * Phase 2: Geometry Vectorization (OpenCV)
 * Phase 3: CAM Integration (GRBL)
 */

import { ref, computed, onUnmounted } from 'vue'
import { api } from '@/services/apiBase'

// Types
export interface Dimension {
  label: string
  value: string
  type: string
  confidence: string
}

export interface AnalysisResult {
  scale?: string
  scale_confidence?: string
  blueprint_type?: string
  detected_model?: string
  dimensions?: Dimension[]
}

export interface CalibrationResult {
  calibration_id: string
  method: string
  ppi: number
  ppmm: number
  confidence: number
  reference_name?: string
  reference_value_inches?: number
  reference_pixels?: number
  notes: string[]
}

export interface CalibrationOptions {
  knownScaleLength?: number
  paperSize?: string
  preferMethod?: string
}

export interface ManualCalibrationPoints {
  point1: { x: number; y: number }
  point2: { x: number; y: number }
  realDimension: number
  dimensionName: string
}

export interface VectorParams {
  scaleFactor: number
  lowThreshold: number
  highThreshold: number
  minArea: number
  instrumentType?: 'electric' | 'acoustic'
  darkThreshold?: number | 'auto'
  gapCloseSize?: number
}

export interface VectorizedGeometry {
  contours_detected: number
  lines_detected: number
  processing_time_ms: number
  svg_path: string
  dxf_path: string
}

export interface CamParams {
  tool_d: number
  stepover: number
  stepdown: number
  z_rough: number
  feed_xy: number
  feed_z: number
  rapid: number
  safe_z: number
  strategy: string
  layer_name: string
  climb: boolean
  smoothing: number
  margin: number
}

export interface RmosResult {
  run_id?: string
  rmos_persisted?: boolean
  rmos_error?: string
  decision?: {
    risk_level?: string
    warnings?: string[]
  }
  gcode?: {
    inline?: boolean
    text?: string
  }
}

export interface BlueprintWorkflowOptions {
  onError?: (error: string) => void
}

export function useBlueprintWorkflow(options: BlueprintWorkflowOptions = {}) {
  // File state
  const uploadedFile = ref<File | null>(null)
  const error = ref<string | null>(null)

  // Phase 1: Analysis
  const isAnalyzing = ref(false)
  const analysis = ref<AnalysisResult | null>(null)
  const analysisProgress = ref(0)
  let analysisInterval: ReturnType<typeof setInterval> | null = null

  // Phase 1.5: Calibration
  const isCalibrating = ref(false)
  const calibration = ref<CalibrationResult | null>(null)
  const calibrationAccepted = ref(false)

  // Phase 2: Vectorization
  const isVectorizing = ref(false)
  const vectorizedGeometry = ref<VectorizedGeometry | null>(null)
  const vectorParams = ref<VectorParams>({
    scaleFactor: 1.0,
    lowThreshold: 50,
    highThreshold: 150,
    minArea: 100,
    instrumentType: 'electric',
    darkThreshold: 'auto',
    gapCloseSize: 0,
  })

  // Phase 3: CAM
  const isSendingToCAM = ref(false)
  const rmosResult = ref<RmosResult | null>(null)
  const camParams = ref<CamParams>({
    tool_d: 6.0,
    stepover: 0.45,
    stepdown: 1.5,
    z_rough: -3.0,
    feed_xy: 1200,
    feed_z: 300,
    rapid: 3000,
    safe_z: 5.0,
    strategy: 'Spiral',
    layer_name: 'GEOMETRY',
    climb: true,
    smoothing: 0.1,
    margin: 0.0,
  })

  // Export state
  const isExporting = ref(false)

  // Computed
  const gcodeReady = computed<boolean>(
    () => !!(rmosResult.value?.gcode?.inline && rmosResult.value?.gcode?.text)
  )

  const currentPhase = computed(() => {
    if (!uploadedFile.value) return 0
    if (!analysis.value) return 1
    if (!calibrationAccepted.value) return 1.5 // Calibration phase
    if (!vectorizedGeometry.value) return 2
    return 3
  })

  // Error helper
  const setError = (msg: string) => {
    error.value = msg
    options.onError?.(msg)
  }

  // File validation
  const validateAndSetFile = (file: File): boolean => {
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      setError(`Unsupported file type: ${file.type}. Use PDF, PNG, or JPG.`)
      return false
    }

    if (file.size > 20 * 1024 * 1024) {
      setError('File too large. Maximum size: 20MB')
      return false
    }

    uploadedFile.value = file
    error.value = null
    return true
  }

  // Phase 1: AI Analysis
  const analyzeBlueprint = async (): Promise<boolean> => {
    if (!uploadedFile.value) return false

    try {
      isAnalyzing.value = true
      error.value = null
      analysisProgress.value = 0

      // Start progress timer
      analysisInterval = setInterval(() => {
        analysisProgress.value++
      }, 1000)

      const formData = new FormData()
      formData.append('file', uploadedFile.value)

      const response = await api('/api/blueprint/analyze', {
        method: 'POST',
        body: formData,
      })

      if (analysisInterval) clearInterval(analysisInterval)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()

      if (!result.success) {
        setError(result.message || 'Analysis failed')
        return false
      }

      analysis.value = result.analysis
      return true
    } catch (err: any) {
      console.error('Analysis error:', err)
      setError(err.message || 'Failed to analyze blueprint')
      return false
    } finally {
      isAnalyzing.value = false
      if (analysisInterval) clearInterval(analysisInterval)
    }
  }

  // Phase 1.5: Calibration
  const calibrateBlueprint = async (opts: CalibrationOptions = {}): Promise<boolean> => {
    if (!uploadedFile.value) return false

    try {
      isCalibrating.value = true
      error.value = null

      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      if (opts.knownScaleLength) {
        formData.append('known_scale_length', opts.knownScaleLength.toString())
      }
      formData.append('paper_size', opts.paperSize || 'letter')
      formData.append('prefer_method', opts.preferMethod || 'auto')

      const response = await api('/api/blueprint/calibrate', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Calibration failed')
      }

      calibration.value = await response.json()
      return true
    } catch (err: any) {
      console.error('Calibration error:', err)
      setError(err.message || 'Failed to calibrate blueprint')
      return false
    } finally {
      isCalibrating.value = false
    }
  }

  const manualCalibrate = async (points: ManualCalibrationPoints): Promise<boolean> => {
    if (!uploadedFile.value) return false

    try {
      isCalibrating.value = true
      error.value = null

      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      formData.append('point1_x', points.point1.x.toString())
      formData.append('point1_y', points.point1.y.toString())
      formData.append('point2_x', points.point2.x.toString())
      formData.append('point2_y', points.point2.y.toString())
      formData.append('real_dimension', points.realDimension.toString())
      formData.append('dimension_name', points.dimensionName)

      const response = await api('/api/blueprint/calibrate/manual', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Manual calibration failed')
      }

      calibration.value = await response.json()
      calibrationAccepted.value = true // Manual calibration is authoritative
      return true
    } catch (err: any) {
      console.error('Manual calibration error:', err)
      setError(err.message || 'Failed to perform manual calibration')
      return false
    } finally {
      isCalibrating.value = false
    }
  }

  const acceptCalibration = () => {
    if (calibration.value) {
      calibrationAccepted.value = true
    }
  }

  const resetCalibration = () => {
    calibration.value = null
    calibrationAccepted.value = false
  }

  // Phase 2: Vectorization
  const vectorizeGeometry = async (): Promise<boolean> => {
    if (!uploadedFile.value || !analysis.value) return false

    try {
      isVectorizing.value = true
      error.value = null

      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      formData.append('analysis_data', JSON.stringify(analysis.value))
      formData.append('scale_factor', vectorParams.value.scaleFactor.toString())

      // Use calibration if available
      if (calibration.value?.calibration_id) {
        formData.append('calibration_id', calibration.value.calibration_id)
      }

      // Use new endpoint parameters
      formData.append('instrument_type', vectorParams.value.instrumentType || 'electric')
      formData.append('dark_threshold', vectorParams.value.darkThreshold?.toString() || 'auto')
      formData.append('gap_close_size', (vectorParams.value.gapCloseSize || 0).toString())

      const response = await api('/api/blueprint/vectorize-geometry', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Vectorization failed')
      }

      const result = await response.json()
      vectorizedGeometry.value = result
      return true
    } catch (err: any) {
      console.error('Vectorization error:', err)
      setError(err.message || 'Failed to vectorize geometry')
      return false
    } finally {
      isVectorizing.value = false
    }
  }

  // Phase 3: Send to CAM
  const sendToCAM = async (): Promise<boolean> => {
    if (!vectorizedGeometry.value?.dxf_path) return false

    try {
      isSendingToCAM.value = true
      error.value = null
      rmosResult.value = null

      // Fetch the DXF file from server
      const dxfFilename = vectorizedGeometry.value.dxf_path.split('/').pop()
      const dxfResponse = await api(`/api/blueprint/static/${dxfFilename}`)
      if (!dxfResponse.ok) throw new Error('Failed to fetch DXF file')
      const dxfBlob = await dxfResponse.blob()

      // Build form data for MVP wrapper
      const fd = new FormData()
      fd.append('file', dxfBlob, 'blueprint.dxf')

      // Add all CAM parameters
      for (const [k, v] of Object.entries(camParams.value)) {
        if (typeof v === 'boolean') {
          fd.append(k, v ? 'true' : 'false')
        } else {
          fd.append(k, String(v))
        }
      }

      // Call MVP wrapper endpoint
      const response = await api('/api/rmos/wrap/mvp/dxf-to-grbl', {
        method: 'POST',
        body: fd,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `HTTP ${response.status}`)
      }

      rmosResult.value = await response.json()
      return true
    } catch (err: any) {
      console.error('CAM error:', err)
      setError(err.message || 'Failed to generate G-code')
      return false
    } finally {
      isSendingToCAM.value = false
    }
  }

  // Export: SVG (basic dimensions)
  const exportSVGBasic = async (): Promise<Blob | null> => {
    if (!analysis.value) return null

    try {
      isExporting.value = true
      error.value = null

      const response = await api('/api/blueprint/to-svg', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          analysis_data: analysis.value,
          format: 'svg',
          scale_correction: 1.0,
          width_mm: 300,
          height_mm: 200,
        }),
      })

      if (!response.ok) throw new Error('SVG export failed')
      return await response.blob()
    } catch (err: any) {
      console.error('Export error:', err)
      setError(err.message || 'Failed to export SVG')
      return null
    } finally {
      isExporting.value = false
    }
  }

  // Export: Vectorized SVG
  const downloadVectorizedSVG = async (): Promise<Blob | null> => {
    if (!vectorizedGeometry.value?.svg_path) return null

    try {
      const response = await fetch(
        `/api/blueprint/static/${vectorizedGeometry.value.svg_path.split('/').pop()}`
      )
      return await response.blob()
    } catch (err: any) {
      setError('Failed to download SVG: ' + err.message)
      return null
    }
  }

  // Export: Vectorized DXF
  const downloadVectorizedDXF = async (): Promise<Blob | null> => {
    if (!vectorizedGeometry.value?.dxf_path) return null

    try {
      const response = await fetch(
        `/api/blueprint/static/${vectorizedGeometry.value.dxf_path.split('/').pop()}`
      )
      return await response.blob()
    } catch (err: any) {
      setError('Failed to download DXF: ' + err.message)
      return null
    }
  }

  // Get G-code text (for download)
  const getGcodeText = (): string | null => {
    if (!rmosResult.value?.gcode?.inline || !rmosResult.value?.gcode?.text) {
      return null
    }
    return rmosResult.value.gcode.text
  }

  // Reset workflow
  const resetWorkflow = () => {
    uploadedFile.value = null
    analysis.value = null
    calibration.value = null
    calibrationAccepted.value = false
    vectorizedGeometry.value = null
    rmosResult.value = null
    error.value = null
    analysisProgress.value = 0
  }

  // Re-vectorize (clear vectorization result only)
  const resetVectorization = () => {
    vectorizedGeometry.value = null
    rmosResult.value = null
  }

  // Clear error
  const clearError = () => {
    error.value = null
  }

  // Cleanup
  onUnmounted(() => {
    if (analysisInterval) clearInterval(analysisInterval)
  })

  return {
    // State
    uploadedFile,
    error,

    // Phase 1
    isAnalyzing,
    analysis,
    analysisProgress,

    // Phase 1.5: Calibration
    isCalibrating,
    calibration,
    calibrationAccepted,

    // Phase 2
    isVectorizing,
    vectorizedGeometry,
    vectorParams,

    // Phase 3
    isSendingToCAM,
    rmosResult,
    camParams,

    // Export
    isExporting,

    // Computed
    gcodeReady,
    currentPhase,

    // Actions
    validateAndSetFile,
    analyzeBlueprint,
    calibrateBlueprint,
    manualCalibrate,
    acceptCalibration,
    resetCalibration,
    vectorizeGeometry,
    sendToCAM,
    exportSVGBasic,
    downloadVectorizedSVG,
    downloadVectorizedDXF,
    getGcodeText,
    resetWorkflow,
    resetVectorization,
    clearError,
  }
}
