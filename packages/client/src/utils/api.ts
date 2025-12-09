/**
 * API Client for Luthier's Tool Box
 * 
 * Provides typed SDK for all backend endpoints.
 */

import type {
  RosetteParams,
  RosetteResult,
  BracingParams,
  BracingResult,
  HardwareParams,
  HardwareResult,
  ExportItem,
  HealthCheck,
  APIError
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE || '/api'

class APIClient {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE}${endpoint}`
    
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })

    if (!response.ok) {
      const error: APIError = await response.json()
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  private async download(endpoint: string, filename: string): Promise<void> {
    const url = `${API_BASE}${endpoint}`
    const response = await fetch(url)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const blob = await response.blob()
    const objectUrl = URL.createObjectURL(blob)
    
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    a.click()
    
    URL.revokeObjectURL(objectUrl)
  }

  // ==================== Health ====================

  async healthCheck(): Promise<HealthCheck> {
    return this.request<HealthCheck>('/health')
  }

  // ==================== Rosette Pipeline ====================

  async calculateRosette(params: RosetteParams): Promise<RosetteResult> {
    return this.request<RosetteResult>('/pipelines/rosette/calculate', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  async exportRosetteDXF(params: RosetteParams): Promise<void> {
    const response = await fetch(`${API_BASE}/pipelines/rosette/export-dxf`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rosette.dxf'
    a.click()
    URL.revokeObjectURL(url)
  }

  async exportRosetteGCode(
    params: RosetteParams,
    options?: {
      tool_mm?: number
      feed?: number
      rpm?: number
      stepdown?: number
      radstep?: number
    }
  ): Promise<void> {
    const queryParams = new URLSearchParams()
    if (options?.tool_mm) queryParams.set('tool_mm', options.tool_mm.toString())
    if (options?.feed) queryParams.set('feed', options.feed.toString())
    if (options?.rpm) queryParams.set('rpm', options.rpm.toString())
    if (options?.stepdown) queryParams.set('stepdown', options.stepdown.toString())
    if (options?.radstep) queryParams.set('radstep', options.radstep.toString())

    const response = await fetch(
      `${API_BASE}/pipelines/rosette/export-gcode?${queryParams}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'rosette.ngc'
    a.click()
    URL.revokeObjectURL(url)
  }

  // ==================== Bracing Pipeline ====================

  async calculateBracing(params: BracingParams): Promise<BracingResult> {
    return this.request<BracingResult>('/pipelines/bracing/calculate', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  // ==================== Hardware Pipeline ====================

  async generateHardwareLayout(params: HardwareParams): Promise<HardwareResult> {
    return this.request<HardwareResult>('/pipelines/hardware/generate', {
      method: 'POST',
      body: JSON.stringify(params),
    })
  }

  // ==================== G-code Explainer Pipeline ====================

  async explainGCode(file: File): Promise<{ filename: string; explanation: string; download_url: string }> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${API_BASE}/pipelines/gcode/explain`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    return response.json()
  }

  // ==================== DXF Cleaner Pipeline ====================

  async cleanDXF(file: File, tolerance: number = 0.12): Promise<void> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(
      `${API_BASE}/pipelines/dxf/clean?tolerance=${tolerance}`,
      {
        method: 'POST',
        body: formData,
      }
    )

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const blob = await response.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cleaned_${file.name}`
    a.click()
    URL.revokeObjectURL(url)
  }

  // ==================== Export Queue ====================

  async listExports(): Promise<ExportItem[]> {
    return this.request<ExportItem[]>('/exports/list')
  }

  async markDownloaded(exportId: string): Promise<{ status: string; export_id: string }> {
    return this.request(`/exports/${exportId}/downloaded`, {
      method: 'POST',
    })
  }

  async downloadFile(exportId: string, filename: string): Promise<void> {
    await this.download(`/files/${exportId}`, filename)
  }
}

export const api = new APIClient()
