/**
 * Minimal composable for DXF/SVG file import (e.g. headstock outline).
 * Used by InlayWorkspaceShell Stage 0 to load custom headstock files.
 */
import { ref } from 'vue'

export interface ImportedFile {
  name: string
  size: number
  type: string
  content?: string
}

export function useDxfImport() {
  const importedFile = ref<ImportedFile | null>(null)
  const error = ref<string | null>(null)

  async function loadFile(file: File): Promise<void> {
    error.value = null
    const validTypes = [
      'application/dxf',
      'image/vnd.dxf',
      'application/dxf+xml',
      'image/svg+xml',
      'text/plain',
    ]
    const isAccepted =
      validTypes.includes(file.type) ||
      file.name.toLowerCase().endsWith('.dxf') ||
      file.name.toLowerCase().endsWith('.svg')
    if (!isAccepted) {
      error.value = 'Please select a DXF or SVG file.'
      return
    }
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => {
        importedFile.value = {
          name: file.name,
          size: file.size,
          type: file.type,
          content: reader.result as string,
        }
        resolve()
      }
      reader.onerror = () => {
        error.value = 'Failed to read file.'
        reject(reader.error)
      }
      reader.readAsText(file)
    })
  }

  function clearFile() {
    importedFile.value = null
    error.value = null
  }

  return {
    importedFile,
    error,
    loadFile,
    clearFile,
  }
}
