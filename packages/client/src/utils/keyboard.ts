/**
 * Shared keyboard utilities.
 *
 * Extracted from useCandidateKeyboard.ts and useKeyboardShortcuts.ts
 * which had an identical `isTypingContext()` function.
 */

/**
 * Returns true if the currently-focused element is a text input,
 * textarea, select, or contentEditable node — meaning keyboard
 * shortcuts should be suppressed.
 */
export function isTypingContext(): boolean {
  const el = document.activeElement as HTMLElement | null
  if (!el) return false
  const tag = (el.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true
  if ((el as HTMLElement & { isContentEditable?: boolean }).isContentEditable) return true
  return false
}
