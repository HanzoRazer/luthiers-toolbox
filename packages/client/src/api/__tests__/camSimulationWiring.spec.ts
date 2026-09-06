/**
 * S1 regression guard — the simulator URL the frontend actually posts to.
 *
 * Investigation 035 found five call sites posting to `/api/cam/simulate_gcode`,
 * which is not mounted: the simulator lives under the `/api/cam/sim` prefix.
 * Every one of them 404'd in production.
 *
 * This defect is invisible to the backend test suite. The API routes were fine
 * the whole time — nothing on the server side was wrong, so no pytest could
 * fail on it. It is only observable by looking at what the client asks for, so
 * the guard has to live here.
 *
 * The two callers do NOT share a contract, which is why a single alias would
 * have been the wrong fix:
 *   - four sites POST JSON `{ gcode }`      -> /api/cam/sim/gcode
 *   - one site POSTs multipart `{ file }`   -> /api/cam/sim/upload
 * Pointing the multipart caller at the JSON handler would have turned a 404
 * into a 422.
 */
import { describe, expect, it } from 'vitest'
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, resolve } from 'node:path'

const SRC = resolve(__dirname, '../..')
const SOURCE_EXTENSIONS = ['.ts', '.vue', '.js']
const SKIP_DIRECTORIES = new Set(['node_modules', 'dist', '__tests__'])

function collectSourceFiles(dir: string, found: string[] = []): string[] {
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry)
    if (statSync(full).isDirectory()) {
      if (!SKIP_DIRECTORIES.has(entry)) collectSourceFiles(full, found)
      continue
    }
    if (SOURCE_EXTENSIONS.some((ext) => entry.endsWith(ext))) found.push(full)
  }
  return found
}

const sources = collectSourceFiles(SRC).map((path) => ({
  path: path.slice(SRC.length + 1).replace(/\\/g, '/'),
  text: readFileSync(path, 'utf8'),
}))

describe('CAM simulation endpoint wiring', () => {
  it('finds source files to scan', () => {
    // Guards the guard: a broken path glob would make every assertion vacuous.
    expect(sources.length).toBeGreaterThan(100)
  })

  it('no source posts to the unmounted /api/cam/simulate_gcode', () => {
    const offenders = sources
      .filter((f) => f.text.includes('/api/cam/simulate_gcode'))
      .map((f) => f.path)

    expect(
      offenders,
      'This path is not mounted and returns 404. JSON callers want ' +
        '/api/cam/sim/gcode; multipart callers want /api/cam/sim/upload.',
    ).toEqual([])
  })

  it('the multipart caller targets the upload endpoint, not the JSON one', () => {
    const composable = sources.find(
      (f) => f.path === 'views/bridge_lab/composables/useGcodeSimulation.ts',
    )
    expect(composable, 'useGcodeSimulation.ts not found').toBeDefined()
    expect(composable!.text).toContain('FormData')
    expect(composable!.text).toContain('/api/cam/sim/upload')
    expect(composable!.text).not.toContain('/api/cam/sim/gcode')
  })

  it('the JSON callers target the JSON endpoint', () => {
    const jsonCallers = [
      'components/GeometryOverlay.vue',
      'components/toolbox/SimLab.vue',
      'components/toolbox/SimLabWorker.vue',
    ]
    for (const path of jsonCallers) {
      const file = sources.find((f) => f.path === path)
      expect(file, `${path} not found`).toBeDefined()
      expect(file!.text, `${path} should call the JSON simulator`).toContain(
        '/api/cam/sim/gcode',
      )
    }
  })
})
