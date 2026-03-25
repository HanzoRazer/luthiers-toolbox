/**
 * useWoodGrain
 *
 * Generates a procedural wood grain texture on an offscreen Canvas,
 * then applies it as a Konva pattern fill to the headstock path shape.
 *
 * Algorithm:
 *   - fBm (fractal Brownian motion) over smooth noise to warp sine-wave
 *     grain lines — producing the wandering long-grain character of real wood.
 *   - Curl figure: a second sine applied to the grain-line phase, simulating
 *     flame/quilted maple.
 *   - Ray fleck: high-frequency fBm spot amplification for quartersawn figure.
 *   - Open pore: threshold the fBm to darken pore channels (rosewood, mahogany).
 *   - Gloss: a radial Canvas gradient composited on top.
 *
 * Usage:
 *   const grain = useWoodGrain()
 *   grain.setSpecies('Mahogany')
 *   const konvaPath = new Konva.Path({ ... })
 *   grain.applyToPath(konvaPath, layer)
 *
 * In WorkspaceView, call applyToPath() whenever the headstock model changes.
 */

import { reactive, readonly } from 'vue'
import Konva from 'konva'

// ─── Species presets ──────────────────────────────────────────────────────────

export interface WoodSpecies {
  name:   string
  base:   [number, number, number]   // mid-tone RGB
  dark:   [number, number, number]   // dark ring RGB
  light:  [number, number, number]   // light ring RGB
  freq:   number   // grain line frequency (lines across width)
  wave:   number   // warp amplitude 0-60
  con:    number   // contrast 0-100
  curl:   number   // flame/curl figure 0-100
  ray:    number   // ray fleck 0-100
  ang:    number   // grain angle degrees off-vertical
}

export const WOOD_SPECIES: Record<string, WoodSpecies> = {
  Mahogany: { name:'Mahogany', base:[130,68,30],  dark:[88,40,14],   light:[168,100,54], freq:14, wave:22, con:55, curl:0,  ray:0,  ang:2  },
  Maple:    { name:'Maple',    base:[210,175,120], dark:[175,138,82], light:[238,210,165],freq:28, wave:8,  con:35, curl:40, ray:30, ang:0  },
  Rosewood: { name:'Rosewood', base:[90,45,28],   dark:[55,22,10],   light:[130,72,48],  freq:10, wave:35, con:80, curl:0,  ray:0,  ang:4  },
  Walnut:   { name:'Walnut',   base:[100,72,42],  dark:[62,40,20],   light:[145,108,68], freq:18, wave:28, con:65, curl:0,  ray:10, ang:1  },
  Ebony:    { name:'Ebony',    base:[38,28,22],   dark:[20,14,10],   light:[65,48,35],   freq:22, wave:12, con:85, curl:0,  ray:0,  ang:0  },
  Koa:      { name:'Koa',      base:[155,88,42],  dark:[110,55,22],  light:[195,130,72], freq:16, wave:40, con:70, curl:55, ray:20, ang:5  },
}

// ─── Grain parameters (user-adjustable) ───────────────────────────────────────

export interface GrainParams {
  freq:   number   // 1-40
  wave:   number   // 0-60
  con:    number   // 0-100
  ang:    number   // -30 to +30 degrees
  curl:   number   // 0-100 flame figure
  ray:    number   // 0-100 ray fleck
  gloss:  number   // 0-100 finish gloss
  pore:   number   // 0-100 pore fill (100=filled, 0=open)
  seed:   number   // randomisation seed 0-999
}

const DEFAULT_PARAMS: GrainParams = {
  freq: 14, wave: 22, con: 55, ang: 0,
  curl: 0,  ray: 0,  gloss: 70, pore: 80, seed: 42,
}

// ─── Noise primitives ─────────────────────────────────────────────────────────

function hash(x: number, y: number, seed: number): number {
  const h = Math.sin(x * 127.1 + y * 311.7 + seed * 74.3) * 43758.5453
  return h - Math.floor(h)
}

function smoothNoise(x: number, y: number, seed: number): number {
  const fx = Math.floor(x), fy = Math.floor(y)
  const tx = x - fx, ty = y - fy
  const s = tx * tx * (3 - 2 * tx)
  const t = ty * ty * (3 - 2 * ty)
  return (
    hash(fx,   fy,   seed) * (1-s) * (1-t) +
    hash(fx+1, fy,   seed) *   s   * (1-t) +
    hash(fx,   fy+1, seed) * (1-s) *   t   +
    hash(fx+1, fy+1, seed) *   s   *   t
  )
}

function fbm(x: number, y: number, seed: number, octaves = 4): number {
  let v = 0, a = 0.5
  for (let i = 0; i < octaves; i++) {
    v += a * smoothNoise(x, y, seed + i * 17.3)
    a *= 0.5; x *= 2.1; y *= 2.1
  }
  return v
}

// ─── Texture generator ────────────────────────────────────────────────────────

export function generateGrainTexture(
  species: WoodSpecies,
  params: GrainParams,
  texW = 400,
  texH = 640,
): HTMLCanvasElement {
  const tc = document.createElement('canvas')
  tc.width = texW; tc.height = texH
  const ctx = tc.getContext('2d')!

  const { base, dark, light } = species
  const { freq, wave, con, ang, curl, ray, gloss, pore, seed } = params

  const conN  = con  / 100
  const curlN = curl / 100
  const rayN  = ray  / 100
  const poreN = 1 - pore / 100
  const angR  = ang  * Math.PI / 180
  const cosA  = Math.cos(angR)
  const sinA  = Math.sin(angR)

  const id   = ctx.createImageData(texW, texH)
  const data = id.data

  for (let y = 0; y < texH; y++) {
    for (let x = 0; x < texW; x++) {
      const nx = x / texW, ny = y / texH

      // Rotate sample coordinates by grain angle
      const rx =  nx * cosA - ny * sinA
      const ry =  nx * sinA + ny * cosA

      // Warp the grain-line axis with fBm
      const warpX = fbm(nx * 3.2 + 0.1, ny * 3.2 + 0.4, seed,     4) * (wave / 40)
      const warpY = fbm(nx * 3.2 + 5.3, ny * 3.2 + 2.8, seed + 3, 4) * (wave / 40)
      const linePos = (ry + warpX + warpY) * freq

      // Primary grain sine
      let grain = (Math.sin(linePos * 2 * Math.PI) + 1) * 0.5

      // Curl / flame figure
      if (curlN > 0) {
        const curlShift = Math.sin((nx * 8 + fbm(nx * 2, ny * 2, seed + 7) * 4) * Math.PI) * curlN * 0.5
        grain = (Math.sin((linePos + curlShift) * 2 * Math.PI) + 1) * 0.5
      }

      // Ray fleck (quartersawn)
      if (rayN > 0) {
        const fleckVal = fbm(nx * 12, ny * 1.5, seed + 11)
        if (fleckVal > 0.65) grain = Math.min(1, grain + (fleckVal - 0.65) * rayN * 2.5)
      }

      // Open pore channels
      if (poreN > 0) {
        const poreVal = fbm(nx * 30, ny * 60, seed + 23)
        if (poreVal < poreN * 0.15) grain *= 0.55
      }

      // Map grain → colour
      const t = grain * conN + (1 - conN) * 0.5
      const r = dark[0] + (light[0] - dark[0]) * t
      const g = dark[1] + (light[1] - dark[1]) * t
      const b = dark[2] + (light[2] - dark[2]) * t

      // Micro-variance (pore/fibre scatter)
      const mv = (fbm(nx * 80, ny * 80, seed + 31) - 0.5) * 10

      const idx = (y * texW + x) * 4
      data[idx]   = Math.max(0, Math.min(255, r + mv))
      data[idx+1] = Math.max(0, Math.min(255, g + mv))
      data[idx+2] = Math.max(0, Math.min(255, b + mv))
      data[idx+3] = 255
    }
  }
  ctx.putImageData(id, 0, 0)

  // Gloss highlight: radial gradient top-centre
  const glossAlpha = (gloss / 100) * 0.25
  const grd = ctx.createRadialGradient(texW * 0.45, texH * 0.1, 0, texW * 0.45, texH * 0.3, texW * 0.65)
  grd.addColorStop(0, `rgba(255,255,255,${glossAlpha})`)
  grd.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = grd
  ctx.fillRect(0, 0, texW, texH)

  return tc
}

// ─── Edge-shading overlay (depth, bevel) ──────────────────────────────────────

export function addEdgeShading(
  layer: Konva.Layer,
  pathData: string,
  ox: number, oy: number, sc: number,
) {
  // Darken left and right edges to simulate rounded/bevelled sides
  const leftDark = new Konva.Path({
    data: pathData,
    x: ox, y: oy, scaleX: sc, scaleY: sc,
    fillLinearGradientStartPoint:   { x: 0,   y: 0 },
    fillLinearGradientEndPoint:     { x: 20,  y: 0 },
    fillLinearGradientColorStops:   [0, 'rgba(0,0,0,.45)', 1, 'rgba(0,0,0,0)'],
    stroke: 'none',
    listening: false,
  })
  const rightDark = new Konva.Path({
    data: pathData,
    x: ox, y: oy, scaleX: sc, scaleY: sc,
    fillLinearGradientStartPoint:   { x: 200,  y: 0 },
    fillLinearGradientEndPoint:     { x: 182,  y: 0 },
    fillLinearGradientColorStops:   [0, 'rgba(0,0,0,.45)', 1, 'rgba(0,0,0,0)'],
    stroke: 'none',
    listening: false,
  })
  layer.add(leftDark, rightDark)
}

// ─── Composable ────────────────────────────────────────────────────────────────

export function useWoodGrain() {
  const speciesKey = ref<string>('Mahogany')
  const params = reactive<GrainParams>({ ...DEFAULT_PARAMS })

  let _texture: HTMLCanvasElement | null = null
  let _grainNode: Konva.Path | null = null
  let _dirtyTexture = true

  function setSpecies(name: string) {
    const sp = WOOD_SPECIES[name]
    if (!sp) return
    speciesKey.value = name
    // Apply species defaults to params
    params.freq  = sp.freq
    params.wave  = sp.wave
    params.con   = sp.con
    params.curl  = sp.curl
    params.ray   = sp.ray
    params.ang   = sp.ang
    _dirtyTexture = true
  }

  function setParam<K extends keyof GrainParams>(key: K, value: GrainParams[K]) {
    params[key] = value
    _dirtyTexture = true
  }

  function randomiseSeed() {
    params.seed = Math.floor(Math.random() * 1000)
    _dirtyTexture = true
  }

  /**
   * Build or reuse the grain texture, then apply as a Konva pattern fill
   * to the given path node.  Call whenever species/params change.
   */
  function applyToPath(
    pathNode: Konva.Path,
    layer: Konva.Layer,
    canvasOX: number,
    canvasOY: number,
    canvasSC: number,
  ) {
    if (_dirtyTexture || !_texture) {
      _texture = generateGrainTexture(
        WOOD_SPECIES[speciesKey.value],
        params,
        400, 640,
      )
      _dirtyTexture = false
    }

    // Map 400×640 texture → canvas headstock bounds (200×320 path units × SC)
    const texScaleX = (200 * canvasSC) / 400
    const texScaleY = (320 * canvasSC) / 640

    pathNode.fillPatternImage(_texture)
    pathNode.fillPatternX(canvasOX)
    pathNode.fillPatternY(canvasOY)
    pathNode.fillPatternScaleX(texScaleX)
    pathNode.fillPatternScaleY(texScaleY)
    pathNode.fillPatternRepeat('no-repeat')
    pathNode.fill('')   // pattern overrides fill colour

    layer.draw()
  }

  /**
   * Convenience: create a fresh grain-textured Konva.Path for a headstock.
   * Returns the path node; caller adds it to the layer.
   */
  function createGrainPath(
    pathData: string,
    canvasOX: number,
    canvasOY: number,
    canvasSC: number,
    layer: Konva.Layer,
  ): Konva.Path {
    if (_dirtyTexture || !_texture) {
      _texture = generateGrainTexture(WOOD_SPECIES[speciesKey.value], params)
      _dirtyTexture = false
    }

    const texScaleX = (200 * canvasSC) / 400
    const texScaleY = (320 * canvasSC) / 640

    const node = new Konva.Path({
      data: pathData,
      x: canvasOX, y: canvasOY, scaleX: canvasSC, scaleY: canvasSC,
      fillPatternImage:  _texture,
      fillPatternX:      canvasOX,
      fillPatternY:      canvasOY,
      fillPatternScaleX: texScaleX,
      fillPatternScaleY: texScaleY,
      fillPatternRepeat: 'no-repeat',
      stroke:      'rgba(0,0,0,.65)',
      strokeWidth: 1.8,
      listening:   false,
    })

    _grainNode = node
    return node
  }

  function markDirty() { _dirtyTexture = true }

  return {
    speciesKey: readonly(speciesKey),
    params:     readonly(params),
    setSpecies, setParam, randomiseSeed,
    applyToPath, createGrainPath, markDirty,
    SPECIES: WOOD_SPECIES,
  }
}

// ref needs to be imported for the reactive composable
import { ref, readonly } from 'vue'
