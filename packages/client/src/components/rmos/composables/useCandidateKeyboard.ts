import { onMounted, onBeforeUnmount, type Ref } from 'vue'
import type { RiskLevel } from '@/sdk/rmos/runs'

export interface KeyboardActions {
  clearSelection: () => void
  selectAllFiltered: () => void
  clearAllFiltered: () => void
  invertSelectionFiltered: () => void
  toggleBulkHistory: () => void
  bulkSetDecision: (decision: RiskLevel) => void
  bulkClearDecision: () => void
  exportGreenOnlyZips: () => void
}

/**
 * Check if user is currently typing in an input field
 */
function isTypingContext(): boolean {
  const el = document.activeElement as HTMLElement | null
  if (!el) return false
  const tag = (el.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true
  if ((el as any).isContentEditable) return true
  return false
}

/**
 * Returns keyboard shortcut help text
 */
export function getHotkeyHelp(): string {
  return [
    'Hotkeys:',
    'g/y/r = Bulk decision GREEN/YELLOW/RED',
    'u = Clear decision (NEEDS_DECISION)',
    'b = Bulk clear decision (selected)',
    'e = Export GREEN-only (all must be decided)',
    'a = Select shown (post-filter)',
    'c = Clear shown (post-filter)',
    'i = Invert selection (shown rows)',
    'x = Clear all selection',
    'h = Toggle bulk history panel',
    'esc = Clear selection',
  ].join('\n')
}

/**
 * Composable for keyboard shortcuts in candidate list
 */
export function useCandidateKeyboard(
  selectedIds: Ref<Set<string>>,
  showBulkHistory: Ref<boolean>,
  actions: KeyboardActions
) {
  function handleKeydown(ev: KeyboardEvent) {
    if (ev.defaultPrevented) return
    if (isTypingContext()) return

    const k = (ev.key || '').toLowerCase()

    if (k === 'escape') {
      ev.preventDefault()
      actions.clearSelection()
      return
    }
    if (k === 'a') {
      ev.preventDefault()
      actions.selectAllFiltered()
      return
    }
    if (k === 'c') {
      ev.preventDefault()
      actions.clearAllFiltered()
      return
    }
    if (k === 'i') {
      ev.preventDefault()
      actions.invertSelectionFiltered()
      return
    }
    if (k === 'x') {
      ev.preventDefault()
      actions.clearSelection()
      return
    }
    if (k === 'h') {
      ev.preventDefault()
      actions.toggleBulkHistory()
      return
    }
    if (k === 'b') {
      if (selectedIds.value.size > 0) {
        ev.preventDefault()
        actions.bulkClearDecision()
      }
      return
    }

    // Decision hotkeys require selection
    if (selectedIds.value.size === 0) return

    if (k === 'g') {
      ev.preventDefault()
      actions.bulkSetDecision('GREEN')
      return
    }
    if (k === 'y') {
      ev.preventDefault()
      actions.bulkSetDecision('YELLOW')
      return
    }
    if (k === 'r') {
      ev.preventDefault()
      actions.bulkSetDecision('RED')
      return
    }
    if (k === 'u') {
      ev.preventDefault()
      actions.bulkClearDecision()
      return
    }
    if (k === 'e') {
      ev.preventDefault()
      actions.exportGreenOnlyZips()
      return
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeydown, { capture: true })
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', handleKeydown, { capture: true } as any)
  })

  return {
    getHotkeyHelp,
    isTypingContext,
  }
}
