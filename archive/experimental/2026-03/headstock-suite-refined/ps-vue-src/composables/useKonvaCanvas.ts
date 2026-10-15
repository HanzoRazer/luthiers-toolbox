import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue'
import Konva from 'konva'

/**
 * Manages Konva Stage + a set of named layers tied to a container ref.
 * Cleans up on unmount. Exposes a resize handler for use with ResizeObserver.
 */
export function useKonvaCanvas(
  containerRef: Ref<HTMLElement | null>,
  layerNames: string[],
) {
  const stage  = ref<Konva.Stage | null>(null)
  const layers = ref<Record<string, Konva.Layer>>({})
  let ro: ResizeObserver | null = null

  function init() {
    const el = containerRef.value
    if (!el || stage.value) return

    const s = new Konva.Stage({ container: el, width: el.clientWidth, height: el.clientHeight })
    const ls: Record<string, Konva.Layer> = {}
    layerNames.forEach(name => {
      const l = new Konva.Layer()
      s.add(l)
      ls[name] = l
    })
    stage.value  = s
    layers.value = ls

    ro = new ResizeObserver(() => {
      if (!el || !stage.value) return
      stage.value.width(el.clientWidth)
      stage.value.height(el.clientHeight)
    })
    ro.observe(el)
  }

  function destroy() {
    ro?.disconnect()
    stage.value?.destroy()
    stage.value  = null
    layers.value = {}
  }

  function getLayer(name: string): Konva.Layer | null {
    return layers.value[name] ?? null
  }

  /** Redraw a specific layer (or all if no name given) */
  function draw(name?: string) {
    if (name) {
      layers.value[name]?.draw()
    } else {
      Object.values(layers.value).forEach(l => l.draw())
    }
  }

  onMounted(init)
  onBeforeUnmount(destroy)

  return { stage, layers, getLayer, draw, init, destroy }
}

// ─── Canvas coordinate helpers ────────────────────────────────────────────────

/** Standard path space: 200 × 320 units, nut at y=298 */
export const PATH_W = 200
export const PATH_H = 320

export function makeCoordHelpers(
  getStage: () => Konva.Stage | null,
  scale: () => number,
  offsetX: () => number,
  offsetY: () => number,
) {
  const p2cx = (p: number) => offsetX() + p * scale()
  const p2cy = (p: number) => offsetY() + p * scale()
  const c2px = (c: number) => (c - offsetX()) / scale()
  const c2py = (c: number) => (c - offsetY()) / scale()

  /** Fit 200×320 path space into the current canvas, centered with padding */
  function fitScale(padding = 28): { sc: number; ox: number; oy: number } {
    const s = getStage()
    if (!s) return { sc: 1.42, ox: 0, oy: 0 }
    const sc = Math.min((s.width() - padding * 2) / PATH_W, (s.height() - padding * 2) / PATH_H)
    const ox = (s.width()  - PATH_W * sc) / 2
    const oy = (s.height() - PATH_H * sc) / 2 + 6
    return { sc, ox, oy }
  }

  return { p2cx, p2cy, c2px, c2py, fitScale }
}
