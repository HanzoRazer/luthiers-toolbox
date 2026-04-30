/**
 * Tests for fretboardEcosphere API client
 *
 * Covers:
 *   - Request serialization (camelCase → snake_case)
 *   - Response deserialization (snake_case → camelCase)
 *   - DXF version parameter passthrough
 *   - Error handling
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  computeEcosphere,
  exportEcosphereDxf,
  type FretboardInput,
} from '../fretboardEcosphere'

const sampleInput: FretboardInput = {
  scaleLengthMm: 647.7,
  fretCount: 22,
  temperament: 'equal_12',
  stringCount: 6,
  slotWidthMm: 0.58,
  nutWidthMm: 42.0,
}

const mockApiResponse = {
  input_params: {
    scale_type: 'standard',
    scale_length_mm: 647.7,
    fret_count: 22,
    temperament: 'equal_12',
    string_count: 6,
    slot_width_mm: 0.58,
    nut_width_mm: 42.0,
  },
  fret_lines: [
    {
      fret_number: 1,
      points: [
        { fret_number: 1, string_index: 0, x_mm: 36.34, y_mm: -21.0 },
        { fret_number: 1, string_index: 5, x_mm: 36.34, y_mm: 21.0 },
      ],
      angle_rad: 0,
      is_perpendicular: true,
    },
  ],
  string_paths: [
    {
      string_index: 0,
      scale_length_mm: 647.7,
      nut_position: [0, -21],
      bridge_position: [647.7, -21],
      fret_intersections: [[36.34, -21]],
      intonation_offset_mm: 0,
    },
  ],
  outline_points: [[0, -21], [0, 21], [400, 28], [400, -28]],
  total_length_mm: 400,
  max_width_mm: 56,
  max_fret_angle_deg: 0,
  version: '1.0.0',
}

describe('fretboardEcosphere API client', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  describe('computeEcosphere', () => {
    it('serializes camelCase input to snake_case for API', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApiResponse,
      } as Response)

      await computeEcosphere(sampleInput)

      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/fretboard/compute',
        expect.objectContaining({ method: 'POST' })
      )

      const callBody = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
      expect(callBody.scale_length_mm).toBe(647.7)
      expect(callBody.fret_count).toBe(22)
      expect(callBody.temperament).toBe('equal_12')
      expect(callBody.string_count).toBe(6)
      expect(callBody.slot_width_mm).toBe(0.58)
      expect(callBody.nut_width_mm).toBe(42.0)
    })

    it('deserializes snake_case response to camelCase', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApiResponse,
      } as Response)

      const result = await computeEcosphere(sampleInput)

      expect(result.inputParams.scaleLengthMm).toBe(647.7)
      expect(result.inputParams.fretCount).toBe(22)
      expect(result.fretLines).toHaveLength(1)
      expect(result.fretLines[0].fretNumber).toBe(1)
      expect(result.fretLines[0].points[0].xMm).toBe(36.34)
      expect(result.stringPaths).toHaveLength(1)
      expect(result.stringPaths[0].stringIndex).toBe(0)
      expect(result.stringPaths[0].nutPosition).toEqual([0, -21])
      expect(result.totalLengthMm).toBe(400)
      expect(result.maxWidthMm).toBe(56)
      expect(result.version).toBe('1.0.0')
    })

    it('throws on non-2xx response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 422,
        text: async () => 'Validation failed: scale_length_mm must be positive',
      } as Response)

      await expect(computeEcosphere(sampleInput)).rejects.toThrow(/422/)
    })
  })

  describe('exportEcosphereDxf', () => {
    it('passes dxf_version when specified', async () => {
      const fakeBlob = new Blob([new Uint8Array([0])], { type: 'application/dxf' })
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => fakeBlob,
      } as Response)

      await exportEcosphereDxf(sampleInput, 'R2000')

      const callBody = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
      expect(callBody.dxf_version).toBe('R2000')
    })

    it('omits dxf_version when not specified', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => new Blob(),
      } as Response)

      await exportEcosphereDxf(sampleInput)

      const callBody = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
      expect(callBody.dxf_version).toBeUndefined()
    })

    it('returns blob on success', async () => {
      const fakeBlob = new Blob(['DXF content'], { type: 'application/dxf' })
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        blob: async () => fakeBlob,
      } as Response)

      const result = await exportEcosphereDxf(sampleInput, 'R12')

      expect(result).toBeInstanceOf(Blob)
    })

    it('throws on export failure', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        text: async () => 'Internal server error',
      } as Response)

      await expect(exportEcosphereDxf(sampleInput)).rejects.toThrow(/DXF export failed.*500/)
    })
  })

  describe('optional fields', () => {
    it('includes optional fields when provided', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApiResponse,
      } as Response)

      const inputWithOptionals: FretboardInput = {
        ...sampleInput,
        scaleType: 'multiscale',
        bassScaleLengthMm: 686.0,
        perpendicularFret: 8,
        radius: { nutRadiusMm: 241.3, heelRadiusMm: 406.4 },
      }

      await computeEcosphere(inputWithOptionals)

      const callBody = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
      expect(callBody.scale_type).toBe('multiscale')
      expect(callBody.bass_scale_length_mm).toBe(686.0)
      expect(callBody.perpendicular_fret).toBe(8)
      expect(callBody.radius.nut_radius_mm).toBe(241.3)
      expect(callBody.radius.heel_radius_mm).toBe(406.4)
    })

    it('omits undefined optional fields', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: async () => mockApiResponse,
      } as Response)

      const minimalInput: FretboardInput = {
        scaleLengthMm: 648,
        fretCount: 22,
        temperament: 'equal_12',
        stringCount: 6,
      }

      await computeEcosphere(minimalInput)

      const callBody = JSON.parse((fetch as ReturnType<typeof vi.fn>).mock.calls[0][1].body)
      expect(callBody.scale_type).toBeUndefined()
      expect(callBody.bass_scale_length_mm).toBeUndefined()
      expect(callBody.radius).toBeUndefined()
    })
  })
})
