/**
 * WorkspaceView.vue — CAM spec integration patch
 *
 * These are the additions to the existing WorkspaceView.vue.
 * Apply them in the sections marked below.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 1 — imports (add to <script setup>)
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { useCamSpec }       from '@/composables/useCamSpec'
import { drawCamOverlay }   from '@/composables/drawCamOverlay'
import CamSpecPanel         from '@/components/CamSpecPanel.vue'
import WoodGrainPanel       from '@/components/WoodGrainPanel.vue'
import { useWoodGrain }     from '@/composables/useWoodGrain'
import { useExportDxf }     from '@/composables/useExportDxf'
import { MM }               from '@/assets/data/headstockData'

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 2 — composable instances (add in setup(), after canvas is ready)
 * ─────────────────────────────────────────────────────────────────────────────
 */

// Derive nut width from the active headstock model (reactively)
const nutWidthMm = computed(() => (currentHS().nw ?? 70) * MM)

const camSpec = useCamSpec(nutWidthMm.value, 175)
const grain   = useWoodGrain()
const exporter = useExportDxf()

// Keep cam nut width in sync when model changes
watch(currentModelKey, () => {
  // useCamSpec takes nutWidthMm as init param — recreate or expose a setter
  // For now: the gates and derived dimensions auto-update via the spec's
  // own nutWidthMm prop. Pass updated value when creating:
  //   camSpec = useCamSpec(nutWidthMm.value, 175)
  // Or add a setNutWidth() helper to useCamSpec if you want live sync.
})

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 3 — Konva layer (add after hsLayer, inLayer, guLayer)
 * ─────────────────────────────────────────────────────────────────────────────
 */

let camLayer: Konva.Layer   // declared at module scope with the others

// In onMounted(), after adding existing layers:
camLayer = canvas.addLayer()

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 4 — redrawHS() additions
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Replace the plain path fill in drawHeadstock() call with the grain path,
 * then draw the cam overlay on top.
 */

function redrawHS() {
  hsLayer.destroyChildren()
  const hs = currentHS()

  // 1. Grain-textured headstock path (replaces flat fill)
  const grainPath = grain.createGrainPath(
    hs.path,
    canvas.OX.value, canvas.OY.value, canvas.SC.value,
    hsLayer,
  )
  hsLayer.add(grainPath)

  // 2. Edge shading + tuner holes + guides (existing logic from useHeadstock)
  drawHeadstock(hsLayer, guideLayer, canvas, hs, showCL.value, showNut.value)

  // 3. CAM overlay — tuner holes, rod channel, pitch annotation
  drawCamOverlay(
    camLayer, canvas,
    camSpec.tunerHoles.value,
    camSpec.rodChannel.value,
    camSpec.spec,
    showCamOverlay.value,
  )
}

// Toggle state for the cam overlay
const showCamOverlay = ref(true)

// Called from CamSpecPanel @change
function onCamChange() {
  drawCamOverlay(
    camLayer, canvas,
    camSpec.tunerHoles.value,
    camSpec.rodChannel.value,
    camSpec.spec,
    showCamOverlay.value,
  )
}

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 5 — Export button wiring
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Replace the existing exportSVG() with a full DXF export that merges the
 * cam spec payload into the ExportRequest.
 */

async function exportDxf() {
  const hs = currentHS()

  // Merge cam spec into the export options
  const camPayload = camSpec.exportPayload.value
  exporter.exportOptions.label = `${currentModelKey.value} — ${camSpec.spec.tunerPattern}`

  // The useExportDxf composable's buildPayload() already handles
  // tuner_holes and inlay_pockets. We extend it here with rod + pitch:
  await exporter.exportDxf(hs, inlays.value, canvas, {
    extraLayers: camPayload,  // passed through to POST body
  })
}

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 6 — Template additions
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * In the right panel (ws-right), add after the layer list:
 */

/*
<template>

  <!-- existing: model list, inlay grid, canvas toggles, element props, layer list -->

  <!-- ADD: Wood grain -->
  <div class="pcat-lbl" style="padding:8px 12px 4px">Wood</div>
  <WoodGrainPanel :grain="grain" @change="redrawHS" />

  <!-- ADD: CAM spec -->
  <div class="pcat-lbl" style="padding:8px 12px 4px">
    CAM spec
    <span
      class="sbtn" style="float:right;padding:2px 5px;font-size:8px"
      @click="showCamOverlay = !showCamOverlay; onCamChange()"
    >{{ showCamOverlay ? 'hide' : 'show' }}</span>
  </div>
  <CamSpecPanel :cam="camSpec" @change="onCamChange" />

  <!-- ADD: status bar export button change -->
  <!-- replace ↓ Export SVG with: -->
  <button class="sbtn go" @click="exportDxf">↓ Export DXF</button>

</template>
*/

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * SECTION 7 — dxf_export.py additions
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * The cam payload merges cleanly into the existing ExportRequest model.
 * Add these fields to ExportRequest in dxf_export.py:
 *
 *   class TrussRod(BaseModel):
 *     access:      str = 'heel'    # 'heel' | 'head'
 *     type:        str = 'single'
 *     width_mm:    float = 6.0
 *     depth_mm:    float = 11.0
 *     length_mm:   float = 445.0
 *     end_mill_mm: float = 6.0
 *     cx_u:        float = 100.0   # canvas units
 *     start_y_u:   float = 298.0
 *     end_y_u:     float = 190.0
 *
 *   class PitchSpec(BaseModel):
 *     style:        str = 'angled'
 *     angle_deg:    float = 13.0
 *     fixture_note: str = ''
 *
 *   class ExportRequest(BaseModel):
 *     ...existing fields...
 *     truss_rod:    Optional[TrussRod]   = None
 *     pitch:        Optional[PitchSpec]  = None
 *     screw_holes:  list[TunerHole]      = []
 *
 * Then in build_dxf():
 *
 *   if req.truss_rod:
 *     rod = req.truss_rod
 *     scale = req.scale_override or MM_PER_UNIT
 *     cx_mm  = rod.cx_u * scale
 *     sy_mm  = rod.start_y_u * scale
 *     ey_mm  = rod.end_y_u * scale
 *     w_mm   = rod.width_mm
 *     d_mm   = rod.depth_mm
 *     em_r   = rod.end_mill_mm / 2
 *
 *     layer_name = 'HS_ROD_SLOT' if rod.access == 'head' else 'HS_ROD_CHANNEL'
 *     msp.add_lwpolyline([
 *       (cx_mm - w_mm/2, sy_mm),
 *       (cx_mm + w_mm/2, sy_mm),
 *       (cx_mm + w_mm/2, ey_mm),
 *       (cx_mm - w_mm/2, ey_mm),
 *     ], close=True, dxfattribs={'layer': layer_name})
 *
 *     # End-mill radius arc at open end
 *     msp.add_arc(
 *       center=(cx_mm, ey_mm + em_r),
 *       radius=em_r,
 *       start_angle=180, end_angle=0,
 *       dxfattribs={'layer': layer_name},
 *     )
 *
 *   if req.screw_holes:
 *     for sh in req.screw_holes:
 *       msp.add_circle(
 *         center=(sh.x * scale, sh.y * scale),
 *         radius=sh.radius * scale,
 *         dxfattribs={'layer': 'HS_TUNER_SCREWS'},
 *       )
 *
 *   if req.pitch and req.pitch.angle_deg > 0:
 *     msp.add_text(
 *       req.pitch.fixture_note,
 *       dxfattribs={'layer': LAYER_ANNOTATION, 'height': 2.0}
 *     ).set_placement((10, -15), align=TextEntityAlignment.LEFT)
 */
