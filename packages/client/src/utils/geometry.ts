export type Units = 'mm' | 'inch'

export interface CanonicalSegment {
  type: 'line' | 'arc'
  x1?: number
  y1?: number
  x2?: number
  y2?: number
  cx?: number
  cy?: number
  r?: number
  start?: number
  end?: number
}

export interface CanonicalPath {
  segments: CanonicalSegment[]
  meta?: Record<string, unknown>
}

export interface CanonicalGeometry {
  units: Units
  paths: CanonicalPath[]
  source?: string
}

function clone<T>(value: T): T {
  return value ? JSON.parse(JSON.stringify(value)) : value
}

function toLoopPoints(loop: any): number[][] {
  if (!loop) {
    return []
  }
  if (Array.isArray(loop)) {
    return loop
  }
  if (Array.isArray(loop?.pts)) {
    return loop.pts
  }
  return []
}

export function loopsToGeometry(loops: any[], units: Units = 'mm'): CanonicalGeometry {
  const canonicalLoops = Array.isArray(loops) ? loops : []
  const paths: CanonicalPath[] = canonicalLoops.map((loop) => {
    const pts = toLoopPoints(loop)
    const segments: CanonicalSegment[] = []
    if (pts.length >= 2) {
      for (let i = 0; i < pts.length; i += 1) {
        const current = pts[i]
        const next = pts[(i + 1) % pts.length]
        if (!current || !next) {
          continue
        }
        segments.push({
          type: 'line',
          x1: Number(current[0]) || 0,
          y1: Number(current[1]) || 0,
          x2: Number(next[0]) || 0,
          y2: Number(next[1]) || 0,
        })
      }
    }
    return { segments }
  })

  return {
    units,
    paths,
  }
}

export function normalizeGeometryPayload(payload: any, defaultUnits: Units = 'mm'): CanonicalGeometry | null {
  if (!payload) {
    return null
  }
  if (payload.paths) {
    return {
      units: (payload.units as Units) || defaultUnits,
      paths: clone(payload.paths),
      source: payload.source,
    }
  }
  if (payload.loops) {
    return loopsToGeometry(payload.loops, (payload.units as Units) || defaultUnits)
  }
  if (Array.isArray(payload)) {
    return loopsToGeometry(payload, defaultUnits)
  }
  return null
}
*** End of File