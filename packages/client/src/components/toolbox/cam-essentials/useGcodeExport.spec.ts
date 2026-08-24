/**
 * Tests for CAM Essentials G-code export helpers.
 *
 * readGcodeOrThrow is the gate that stops a 409 SAFETY_BLOCKED JSON body
 * from being saved as a .nc file.
 */
import { describe, expect, it } from 'vitest'
import { readGcodeOrThrow } from './useGcodeExport'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' }
  })
}

function textResponse(status: number, body: string): Response {
  return new Response(body, {
    status,
    headers: { 'Content-Type': 'text/plain' }
  })
}

describe('readGcodeOrThrow', () => {
  it('returns the text body of a 200 response', async () => {
    const gcode = 'G21 G90\nG0 Z5.0000\nM30\n'
    await expect(
      readGcodeOrThrow(textResponse(200, gcode), 'Retract')
    ).resolves.toBe(gcode)
  })

  it('throws the server message for 409 SAFETY_BLOCKED JSON', async () => {
    const response = jsonResponse(409, {
      detail: {
        error: 'SAFETY_BLOCKED',
        message: 'Retract G-code generation blocked by server-side safety policy.'
      }
    })

    await expect(readGcodeOrThrow(response, 'Retract')).rejects.toThrow(
      'Retract G-code generation blocked by server-side safety policy.'
    )
  })

  it('falls back to a status message when the error body is not JSON', async () => {
    const response = textResponse(502, 'upstream exploded')

    await expect(readGcodeOrThrow(response, 'Retract')).rejects.toThrow(
      'Retract export failed (502)'
    )
  })
})
