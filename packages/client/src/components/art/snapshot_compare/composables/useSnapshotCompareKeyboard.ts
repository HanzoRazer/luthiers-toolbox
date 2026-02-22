/**
 * SnapshotComparePanel keyboard composable.
 */
import { onMounted, onBeforeUnmount, type Ref } from 'vue'

export interface SnapshotCompareKeyboardReturn {
  // Keyboard handling is done internally
}

/**
 * Check if event target is a typing element.
 */
function isTypingTarget(el: EventTarget | null): boolean {
  const node = el as HTMLElement | null
  if (!node) return false
  const tag = (node.tagName || '').toLowerCase()
  return tag === 'input' || tag === 'textarea' || tag === 'select' || node.isContentEditable
}

export function useSnapshotCompareKeyboard(
  isOpen: Ref<boolean>,
  stepLeft: (delta: number) => void,
  stepRight: (delta: number) => void
): SnapshotCompareKeyboardReturn {
  function onKeyDown(e: KeyboardEvent): void {
    if (!isOpen.value) return
    if (isTypingTarget(e.target)) return

    // Shift+[ / Shift+] steps Left; plain [ / ] steps Right
    if (e.key === '[') {
      e.preventDefault()
      if (e.shiftKey) {
        stepLeft(-1)
      } else {
        stepRight(-1)
      }
    } else if (e.key === ']') {
      e.preventDefault()
      if (e.shiftKey) {
        stepLeft(1)
      } else {
        stepRight(1)
      }
    }
  }

  onMounted(() => {
    window.addEventListener('keydown', onKeyDown)
  })

  onBeforeUnmount(() => {
    window.removeEventListener('keydown', onKeyDown)
  })

  return {}
}
