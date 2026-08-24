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
 *
 * The generic alert is deliberately unchanged for the five CAM operations that
 * have always used it. Pass `showDetail` only where the server message is
 * actionable to the operator — a governed SAFETY_BLOCKED rejection says *why*
 * the lane is closed, and "check the console" wastes that. Widening the detail
 * text to every operation is a UX change unrelated to retract convergence.
 */
export function handleExportError(
  operation: string,
  err: unknown,
  opts: { showDetail?: boolean } = {}
): void {
  console.error(`${operation} export failed:`, err)
  if (!opts.showDetail) {
    alert('Export failed. Check console for details.')
    return
  }
  const detail = err instanceof Error ? err.message : String(err)
  alert(`${operation} export failed: ${detail}`)
}
