/**
 * Shared G-code export utilities for CAM Essentials operations.
 */

/**
 * Download content as a file.
 */
export function downloadFile(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/**
 * Handle export errors consistently.
 */
export function handleExportError(operation: string, err: unknown): void {
  console.error(`${operation} export failed:`, err)
  alert('Export failed. Check console for details.')
}
