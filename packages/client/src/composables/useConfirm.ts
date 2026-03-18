/**
 * Composable for confirmation dialogs.
 * Shim over window.confirm — same behavior, but injectable and replaceable
 * with a proper modal later. See CRITICAL_SYSTEMS_REVIEW_2026-03-18.md (Usability).
 */
export function useConfirm() {
  function confirm(message: string): Promise<boolean> {
    return Promise.resolve(window.confirm(message))
  }
  return { confirm }
}
