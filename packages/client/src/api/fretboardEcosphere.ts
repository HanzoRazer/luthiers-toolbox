/**
 * Typed client for /api/v1/fretboard/* endpoints.
 *
 * Backend: services/api/app/api_v1/fretboard.py
 *
 * Endpoints:
 *   POST /fretboard/compute  - Build ecosphere (free)
 *   POST /fretboard/dxf      - Export DXF (R12 free, R2000 pro)
 *   POST /fretboard/scala    - Export Scala temperament (free)
 *   GET  /fretboard/presets  - List presets (free)
 *   GET  /fretboard/presets/{name} - Get preset (free)
 *
 * Types use camelCase (Vue/TS convention); serialization converts
 * to/from snake_case for the wire format.
 */

// =============================================================================
// Types - camelCase frontend convention
// =============================================================================

export type DxfVersion = "R12" | "R2000"

export type ScaleType = "standard" | "multiscale"

export type TemperamentType =
  | "equal_12"
  | "equal_19"
  | "equal_24"
  | "equal_31"
  | "pythagorean"
  | "just_major"
  | "meantone_quarter"

export interface RadiusSpec {
  nutRadiusMm?: number
  heelRadiusMm?: number
}

export interface FretboardInput {
  scaleType?: ScaleType
  scaleLengthMm: number
  bassScaleLengthMm?: number
  stringCount: number
  fretCount: number
  perpendicularFret?: number
  temperament: TemperamentType
  nutWidthMm?: number
  heelWidthMm?: number
  edgeOffsetMm?: number
  radius?: RadiusSpec
  extensionMm?: number
  slotWidthMm?: number
  intonationOffsetsMm?: Record<number, number>
}

export interface FretPoint {
  fretNumber: number
  stringIndex: number
  xMm: number
  yMm: number
}

export interface FretLine {
  fretNumber: number
  points: FretPoint[]
  angleRad: number
  isPerpendicular: boolean
}

export interface StringPath {
  stringIndex: number
  scaleLengthMm: number
  nutPosition: [number, number]
  bridgePosition: [number, number]
  fretIntersections: [number, number][]
  intonationOffsetMm: number
}

export interface FretboardEcosphere {
  inputParams: FretboardInput
  fretLines: FretLine[]
  stringPaths: StringPath[]
  outlinePoints: [number, number][]
  totalLengthMm: number
  maxWidthMm: number
  maxFretAngleDeg: number
  version: string
}

// =============================================================================
// Serialization helpers - camelCase <-> snake_case
// =============================================================================

function toApiPayload(input: FretboardInput): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    scale_length_mm: input.scaleLengthMm,
    fret_count: input.fretCount,
    temperament: input.temperament,
    string_count: input.stringCount,
  }

  if (input.scaleType !== undefined) payload.scale_type = input.scaleType
  if (input.bassScaleLengthMm !== undefined) payload.bass_scale_length_mm = input.bassScaleLengthMm
  if (input.perpendicularFret !== undefined) payload.perpendicular_fret = input.perpendicularFret
  if (input.nutWidthMm !== undefined) payload.nut_width_mm = input.nutWidthMm
  if (input.heelWidthMm !== undefined) payload.heel_width_mm = input.heelWidthMm
  if (input.edgeOffsetMm !== undefined) payload.edge_offset_mm = input.edgeOffsetMm
  if (input.extensionMm !== undefined) payload.extension_mm = input.extensionMm
  if (input.slotWidthMm !== undefined) payload.slot_width_mm = input.slotWidthMm
  if (input.intonationOffsetsMm !== undefined) payload.intonation_offsets_mm = input.intonationOffsetsMm

  if (input.radius) {
    payload.radius = {
      nut_radius_mm: input.radius.nutRadiusMm,
      heel_radius_mm: input.radius.heelRadiusMm,
    }
  }

  return payload
}

function fromFretPoint(data: Record<string, unknown>): FretPoint {
  return {
    fretNumber: data.fret_number as number,
    stringIndex: data.string_index as number,
    xMm: data.x_mm as number,
    yMm: data.y_mm as number,
  }
}

function fromFretLine(data: Record<string, unknown>): FretLine {
  return {
    fretNumber: data.fret_number as number,
    points: ((data.points as unknown[]) ?? []).map((p) => fromFretPoint(p as Record<string, unknown>)),
    angleRad: (data.angle_rad as number) ?? 0,
    isPerpendicular: (data.is_perpendicular as boolean) ?? true,
  }
}

function fromStringPath(data: Record<string, unknown>): StringPath {
  return {
    stringIndex: data.string_index as number,
    scaleLengthMm: data.scale_length_mm as number,
    nutPosition: data.nut_position as [number, number],
    bridgePosition: data.bridge_position as [number, number],
    fretIntersections: (data.fret_intersections as [number, number][]) ?? [],
    intonationOffsetMm: (data.intonation_offset_mm as number) ?? 0,
  }
}

function fromRadiusSpec(data: Record<string, unknown> | undefined): RadiusSpec | undefined {
  if (!data) return undefined
  return {
    nutRadiusMm: data.nut_radius_mm as number | undefined,
    heelRadiusMm: data.heel_radius_mm as number | undefined,
  }
}

function fromInputParams(data: Record<string, unknown>): FretboardInput {
  return {
    scaleType: data.scale_type as ScaleType | undefined,
    scaleLengthMm: data.scale_length_mm as number,
    bassScaleLengthMm: data.bass_scale_length_mm as number | undefined,
    stringCount: data.string_count as number,
    fretCount: data.fret_count as number,
    perpendicularFret: data.perpendicular_fret as number | undefined,
    temperament: data.temperament as TemperamentType,
    nutWidthMm: data.nut_width_mm as number | undefined,
    heelWidthMm: data.heel_width_mm as number | undefined,
    edgeOffsetMm: data.edge_offset_mm as number | undefined,
    radius: fromRadiusSpec(data.radius as Record<string, unknown> | undefined),
    extensionMm: data.extension_mm as number | undefined,
    slotWidthMm: data.slot_width_mm as number | undefined,
    intonationOffsetsMm: data.intonation_offsets_mm as Record<number, number> | undefined,
  }
}

function fromApiResponse(data: Record<string, unknown>): FretboardEcosphere {
  return {
    inputParams: fromInputParams(data.input_params as Record<string, unknown>),
    fretLines: ((data.fret_lines as unknown[]) ?? []).map((fl) => fromFretLine(fl as Record<string, unknown>)),
    stringPaths: ((data.string_paths as unknown[]) ?? []).map((sp) => fromStringPath(sp as Record<string, unknown>)),
    outlinePoints: (data.outline_points as [number, number][]) ?? [],
    totalLengthMm: (data.total_length_mm as number) ?? 0,
    maxWidthMm: (data.max_width_mm as number) ?? 0,
    maxFretAngleDeg: (data.max_fret_angle_deg as number) ?? 0,
    version: (data.version as string) ?? "1.0.0",
  }
}

// =============================================================================
// API functions
// =============================================================================

const API_BASE = "/api/v1/fretboard"

async function fetchJson<T>(
  url: string,
  init?: RequestInit,
  transform?: (data: Record<string, unknown>) => T
): Promise<T> {
  const resp = await fetch(url, init)
  if (!resp.ok) {
    const detail = await resp.text()
    throw new Error(`API ${resp.status}: ${detail}`)
  }
  const data = await resp.json()
  return transform ? transform(data) : data
}

export async function computeEcosphere(req: FretboardInput): Promise<FretboardEcosphere> {
  return fetchJson(
    `${API_BASE}/compute`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(toApiPayload(req)),
    },
    fromApiResponse
  )
}

export async function exportEcosphereDxf(req: FretboardInput, version?: DxfVersion): Promise<Blob> {
  const payload = toApiPayload(req)
  if (version) {
    payload.dxf_version = version
  }

  const resp = await fetch(`${API_BASE}/dxf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  })

  if (!resp.ok) {
    const detail = await resp.text()
    throw new Error(`DXF export failed: ${resp.status} ${detail}`)
  }

  return resp.blob()
}

export async function exportEcosphereScala(req: FretboardInput): Promise<string> {
  const resp = await fetch(`${API_BASE}/scala`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/plain",
    },
    body: JSON.stringify(toApiPayload(req)),
  })

  if (!resp.ok) {
    const detail = await resp.text()
    throw new Error(`Scala export failed: ${resp.status} ${detail}`)
  }

  return resp.text()
}

export interface PresetListItem {
  name: string
  description?: string
}

export async function listPresets(): Promise<PresetListItem[]> {
  return fetchJson(`${API_BASE}/presets`)
}

export async function getPreset(name: string): Promise<FretboardInput> {
  return fetchJson(
    `${API_BASE}/presets/${encodeURIComponent(name)}`,
    undefined,
    fromInputParams
  )
}
