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
 * Read G-code from a successful export response.
 *
 * Throws on non-OK status so callers cannot download a JSON error body
 * (for example 409 SAFETY_BLOCKED) as a .nc file.
 */
export async function readGcodeOrThrow(
  response: Response,
  operation: string
): Promise<string> {
  if (!response.ok) {
    let message = `${operation} export failed (${response.status})`
    try {
      const payload = await response.json() as {
        detail?: { error?: string; message?: string } | string
      }
      const detail = payload?.detail
      if (detail && typeof detail === 'object') {
        if (detail.error === 'SAFETY_BLOCKED') {
          message = detail.message || 'Blocked by server-side safety policy.'
        } else if (detail.message) {
          message = detail.message
        }
      } else if (typeof detail === 'string' && detail) {
        message = detail
      }
    } catch {
      // Body was not JSON; keep the status-based message.
    }
    throw new Error(message)
  }
  return response.text()
}

/**
 * Handle export errors consistently.
 */
export function handleExportError(operation: string, err: unknown): void {
  const detail = err instanceof Error ? err.message : String(err)
  console.error(`${operation} export failed:`, err)
  alert(`${operation} export failed: ${detail}`)
}
