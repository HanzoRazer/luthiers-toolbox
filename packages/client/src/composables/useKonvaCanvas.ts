/**
 * useKonvaCanvas — creates a Konva Stage in the container ref and exposes one layer + dimensions.
 * Used by NeckView and other canvas views.
 */
import { ref, onMounted } from 'vue'
import Konva from 'konva'

export function useKonvaCanvas(containerRef: { value: HTMLElement | null }) {
  const W = ref(800)
  const H = ref(600)
  let stage: Konva.Stage | null = null
  let layer: Konva.Layer | null = null

  function addLayer(): Konva.Layer {
    if (layer) return layer
    const el = containerRef.value
    if (!el) {
      layer = new Konva.Layer()
      return layer
    }
    const width = el.offsetWidth || 800
    const height = el.offsetHeight || 600
    W.value = width
    H.value = height
    stage = new Konva.Stage({ container: el, width, height })
    layer = new Konva.Layer()
    stage.add(layer)
    const ro = new ResizeObserver(() => {
      if (!el || !stage) return
      W.value = el.offsetWidth || 800
      H.value = el.offsetHeight || 600
      stage.size({ width: W.value, height: H.value })
      stage.draw()
    })
    ro.observe(el)
    return layer
  }

  return { addLayer, W, H }
}
