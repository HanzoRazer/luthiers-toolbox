/**
 * DXF Preflight validation and auto-fix logic.
 */
import { api } from '@/services/apiBase'
import type { Ref } from 'vue'
import type { ValidationReport, FixOptions } from './types'

export interface DxfPreflightValidationDeps {
  selectedFile: Ref<File | null>
  validating: Ref<boolean>
  report: Ref<ValidationReport | null>
  error: Ref<string | null>
  fixes: Ref<FixOptions>
  fixedDxf: Ref<string | null>
  appliedFixes: Ref<string[]>
  autoFixing: Ref<boolean>
  hasSelectedFixes: Ref<boolean>
}

export function useDxfPreflightValidation(deps: DxfPreflightValidationDeps) {
  const {
    selectedFile,
    validating,
    report,
    error,
    fixes,
    fixedDxf,
    appliedFixes,
    autoFixing,
    hasSelectedFixes
  } = deps

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement
    if (target.files && target.files.length > 0) {
      selectedFile.value = target.files[0]
      report.value = null
      error.value = null
      fixedDxf.value = null
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  }

  async function validateFile() {
    if (!selectedFile.value) return

    validating.value = true
    error.value = null

    try {
      const formData = new FormData()
      formData.append('file', selectedFile.value)

      const response = await api('/api/dxf/preflight/validate', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(`Validation failed: ${errText}`)
      }

      report.value = await response.json()
    } catch (err: unknown) {
      error.value = (err as Error).message || 'Validation failed'
      console.error('Validation error:', err)
    } finally {
      validating.value = false
    }
  }

  async function applyAutoFix() {
    if (!selectedFile.value || !hasSelectedFixes.value) return

    autoFixing.value = true
    error.value = null

    try {
      // Read file as base64
      const reader = new FileReader()
      const fileBase64 = await new Promise<string>((resolve, reject) => {
        reader.onload = () => {
          const result = reader.result as string
          const base64 = result.split(',')[1] // Remove data:... prefix
          resolve(base64)
        }
        reader.onerror = reject
        reader.readAsDataURL(selectedFile.value!)
      })

      // Build fix list
      const fixList: string[] = []
      if (fixes.value.convert_to_r12) fixList.push('convert_to_r12')
      if (fixes.value.close_open_polylines) fixList.push('close_open_polylines')
      if (fixes.value.set_units_mm) fixList.push('set_units_mm')
      if (fixes.value.explode_splines) fixList.push('explode_splines')

      const response = await api('/api/dxf/preflight/auto_fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dxf_base64: fileBase64,
          filename: selectedFile.value.name,
          fixes: fixList
        })
      })

      if (!response.ok) {
        const errText = await response.text()
        throw new Error(`Auto-fix failed: ${errText}`)
      }

      const result = await response.json()
      fixedDxf.value = result.fixed_dxf_base64
      appliedFixes.value = result.fixes_applied
      report.value = result.validation_report
    } catch (err: unknown) {
      error.value = (err as Error).message || 'Auto-fix failed'
      console.error('Auto-fix error:', err)
    } finally {
      autoFixing.value = false
    }
  }

  function downloadFixedDxf() {
    if (!fixedDxf.value || !selectedFile.value) return

    const bytes = Uint8Array.from(atob(fixedDxf.value), c => c.charCodeAt(0))
    const blob = new Blob([bytes], { type: 'application/dxf' })
    const url = URL.createObjectURL(blob)

    const a = document.createElement('a')
    a.href = url
    a.download = selectedFile.value.name.replace('.dxf', '_fixed.dxf')
    a.click()

    URL.revokeObjectURL(url)
  }

  async function validateFixedDxf() {
    if (!fixedDxf.value || !selectedFile.value) return

    validating.value = true
    error.value = null

    try {
      const response = await api('/api/dxf/preflight/validate_base64', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dxf_base64: fixedDxf.value,
          filename: selectedFile.value.name.replace('.dxf', '_fixed.dxf')
        })
      })

      if (!response.ok) {
        throw new Error('Re-validation failed')
      }

      report.value = await response.json()
    } catch (err: unknown) {
      error.value = (err as Error).message
    } finally {
      validating.value = false
    }
  }

  return {
    handleFileSelect,
    formatFileSize,
    validateFile,
    applyAutoFix,
    downloadFixedDxf,
    validateFixedDxf
  }
}
