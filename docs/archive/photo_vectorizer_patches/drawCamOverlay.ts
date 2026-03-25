/**
 * drawCamOverlay
 *
 * Draws the CAM spec (truss rod channel, tuner holes, pitch annotation)
 * on top of the headstock in WorkspaceView.
 *
 * Call from drawHeadstock() after the wood-grain path is added:
 *
 *   import { drawCamOverlay } from '@/composables/drawCamOverlay'
 *   drawCamOverlay(camLayer, canvas, camSpec.tunerHoles, camSpec.rodChannel, camSpec.spec)
 *
 * Uses a dedicated Konva layer (camLayer) so it can be toggled independently
 * from the headstock shape and inlay layers.
 */

import Konva from 'konva'
import type { KonvaCanvas } from './useKonvaCanvas'
import type { TunerHoleSpec, RodChannelSpec, CamSpec } from './useCamSpec'

export function drawCamOverlay(
  layer:      Konva.Layer,
  canvas:     KonvaCanvas,
  tuners:     TunerHoleSpec[],
  rod:        RodChannelSpec,
  spec:       CamSpec,
  visible =   true,
) {
  layer.destroyChildren()
  if (!visible) { layer.draw(); return }

  const { p2cx, p2cy, SC } = canvas

  // ── Truss rod channel ──────────────────────────────────────────────────────
  const rodCX  = p2cx(rod.cx)
  const rodW   = rod.widthU * SC.value
  const rodX   = rodCX - rodW / 2
  const rodStartY = p2cy(rod.startY)
  const rodEndY   = p2cy(rod.endY)
  const rodH      = Math.abs(rodEndY - rodStartY)
  const topY      = Math.min(rodStartY, rodEndY)

  // Channel fill
  layer.add(new Konva.Rect({
    x: rodX, y: topY, width: rodW, height: rodH,
    fill:        'rgba(200,112,48,.18)',
    stroke:      '#c87030',
    strokeWidth: 0.8,
    dash:        [4, 3],
    listening:   false,
  }))

  // End-mill radius indicator at open end
  const emR = rod.emRadiusU * SC.value
  layer.add(new Konva.Arc({
    x:           rodCX,
    y:           topY + emR,
    innerRadius: 0,
    outerRadius: emR,
    angle:       180,
    rotation:    0,
    fill:        'rgba(200,112,48,.25)',
    stroke:      '#c87030',
    strokeWidth: 0.6,
    listening:   false,
  }))

  // Label
  layer.add(new Konva.Text({
    x:          rodX + rodW + 4,
    y:          topY + rodH / 2 - 8,
    text:       `TR ${spec.rodWidthMm}×${spec.rodDepthMm}mm\n${spec.rodAccess === 'head' ? 'head access' : 'heel access'}`,
    fontSize:   7.5,
    fontFamily: 'Courier New',
    fill:       '#c87030',
    opacity:    0.85,
    listening:  false,
  }))

  // ── Tuner post holes ───────────────────────────────────────────────────────
  tuners.forEach((t, i) => {
    const tx = p2cx(t.x)
    const ty = p2cy(t.y)
    const pr = t.postR * SC.value
    const sr = t.screwR * SC.value

    // Post bore circle — green (drill layer)
    layer.add(new Konva.Circle({
      x: tx, y: ty, radius: pr,
      fill:        'rgba(90,184,106,.12)',
      stroke:      '#5ab86a',
      strokeWidth: 1,
      dash:        [3, 2],
      listening:   false,
    }))

    // Bushing ring
    layer.add(new Konva.Circle({
      x: tx, y: ty, radius: pr * 1.45,
      fill:        'none',
      stroke:      'rgba(90,184,106,.25)',
      strokeWidth: 0.5,
      listening:   false,
    }))

    // Mounting screws (2 per tuner, offset along post axis perp)
    const offU = pr * 2.2
    ;[-1, 1].forEach(sign => {
      layer.add(new Konva.Circle({
        x: tx + sign * offU,
        y: ty,
        radius: sr,
        fill:        'rgba(90,184,106,.1)',
        stroke:      'rgba(90,184,106,.4)',
        strokeWidth: 0.6,
        listening:   false,
      }))
    })

    // Cross-hair for drill registration
    ;[[-pr*0.6, 0, pr*0.6, 0], [0, -pr*0.6, 0, pr*0.6]].forEach(pts => {
      layer.add(new Konva.Line({
        points:      [tx+pts[0], ty+pts[1], tx+pts[2], ty+pts[3]],
        stroke:      'rgba(90,184,106,.5)',
        strokeWidth: 0.5,
        listening:   false,
      }))
    })

    // Index label (T1, T2…)
    if (i === 0 || i === tuners.length / 2) {
      layer.add(new Konva.Text({
        x:          tx + pr + 3,
        y:          ty - 4,
        text:       `T${i + 1}  Ø${spec.postDiamMm}`,
        fontSize:   7,
        fontFamily: 'Courier New',
        fill:       'rgba(90,184,106,.7)',
        listening:  false,
      }))
    }
  })

  // ── Pitch annotation (side-view indicator on face) ─────────────────────────
  if (spec.pitchStyle === 'angled') {
    const nutY2 = p2cy(298)
    const nutX1 = p2cx(65)

    // Small angle arc at nut corner
    const arcR = 18 * SC.value
    layer.add(new Konva.Arc({
      x:           nutX1,
      y:           nutY2,
      innerRadius: 0,
      outerRadius: arcR,
      angle:       spec.angle,
      rotation:    -(90 + spec.angle),
      fill:        'rgba(91,143,168,.15)',
      stroke:      '#5b8fa8',
      strokeWidth: 0.7,
      listening:   false,
    }))

    layer.add(new Konva.Text({
      x:          nutX1 + 5,
      y:          nutY2 - 20,
      text:       `${spec.angle}°`,
      fontSize:   8,
      fontFamily: 'Courier New',
      fill:       '#5b8fa8',
      opacity:    0.8,
      listening:  false,
    }))

    // Fixture warning badge
    layer.add(new Konva.Label({
      x: p2cx(140),
      y: p2cy(270),
      opacity: 0.85,
    }).add(
      new Konva.Tag({ fill:'rgba(91,143,168,.12)', stroke:'#3a6a8a', strokeWidth:0.6, cornerRadius:2 }),
      new Konva.Text({ text: `${spec.angle}° fixture req'd`, fontSize:7.5, fontFamily:'Courier New', fill:'#5b8fa8', padding:4 }),
    ))
  }

  layer.draw()
}
