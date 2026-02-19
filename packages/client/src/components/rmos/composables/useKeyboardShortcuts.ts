/**
 * Composable for keyboard shortcut handling in candidate list.
 * Handles g/y/r (bulk decisions), u (clear), e (export), a/c/i/x (selection), h (history), esc.
 */
import { onMounted, onBeforeUnmount, type Ref } from 'vue'
import type { RiskLevel } from '@/sdk/rmos/runs'

export interface KeyboardShortcutHandlers {
  clearSelection: () => void
  selectAllFiltered: () => void
  clearAllFiltered: () => void
  invertSelectionFiltered: () => void
  bulkSetDecision: (decision: RiskLevel) => void
  bulkClearDecision: () => void
  exportGreenOnlyZips: () => void
  toggleBulkHistory: () => void
  clearBulkDecisionV2: () => Promise<void>
}

export interface KeyboardShortcutsState {
  hotkeyHelp: () => string
}

function isTypingContext(): boolean {
  const el = document.activeElement as HTMLElement | null
  if (!el) return false
  const tag = (el.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || tag === 'select') return true
  if ((el as HTMLElement & { isContentEditable?: boolean }).isContentEditable) return true
  return false
}

export function useKeyboardShortcuts(
  selectedIds: Ref<Set<string>>,
  showBulkHistory: Ref<boolean>,
  handlers: KeyboardShortcutHandlers
): KeyboardShortcutsState {
  function hotkeyHelp(): string {
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

  function onKeydown(ev: KeyboardEvent) {
    if (ev.defaultPrevented) return
    if (isTypingContext()) return

    const k = (ev.key || '').toLowerCase()

    if (k === 'escape') {
      ev.preventDefault()
      handlers.clearSelection()
      return
    }
    if (k === 'a') {
      ev.preventDefault()
      handlers.selectAllFiltered()
      return
    }
    if (k === 'c') {
      ev.preventDefault()
      handlers.clearAllFiltered()
      return
    }
    if (k === 'i') {
      ev.preventDefault()
      handlers.invertSelectionFiltered()
      return
    }
    if (k === 'x') {
      ev.preventDefault()
      handlers.clearSelection()
      return
    }
    if (k === 'h') {
      ev.preventDefault()
      handlers.toggleBulkHistory()
      return
    }
    if (k === 'b') {
      if (selectedIds.value.size > 0) {
        ev.preventDefault()
        void handlers.clearBulkDecisionV2()
      }
      return
    }

    // Decision hotkeys require selection
    if (selectedIds.value.size === 0) return

    if (k === 'g') {
      ev.preventDefault()
      handlers.bulkSetDecision('GREEN')
      return
    }
    if (k === 'y') {
      ev.preventDefault()
      handlers.bulkSetDecision('YELLOW')
      return
    }
    if (k === 'r') {
      ev.preventDefault()
      handlers.bulkSetDecision('RED')
      return
    }
    if (k === 'u') {
      ev.preventDefault()
      handlers.bulkClearDecision()
      return
    }
    if (k === 'e') {
      ev.preventDefault()
      handlers.exportGreenOnlyZips()
      return
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeydown, { capture: true })
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeydown, { capture: true } as EventListenerOptions)
  })

  return {
    hotkeyHelp,
  }
}
