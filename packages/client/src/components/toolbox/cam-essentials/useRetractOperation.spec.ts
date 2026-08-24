/**
 * Tests for the retract G-code exporter.
 *
 * The FastAPI /gcode route binds query params, not a JSON body. Sending JSON
 * was ignored and silently used defaults. exportGcode must put retract params
 * on the query string and must not download a non-OK body as a .nc file.
 */
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '@/services/apiBase'
import { downloadFile, handleExportError } from './useGcodeExport'
import { useRetractOperation } from './useRetractOperation'

vi.mock('@/services/apiBase', () => ({
  api: vi.fn()
}))

vi.mock('./useGcodeExport', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./useGcodeExport')>()
  return {
    ...actual,
    downloadFile: vi.fn(),
    handleExportError: vi.fn()
  }
})

const mockedApi = vi.mocked(api)
const mockedDownload = vi.mocked(downloadFile)
const mockedHandleError = vi.mocked(handleExportError)

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

describe('useRetractOperation.exportGcode', () => {
  beforeEach(() => {
    mockedApi.mockReset()
    mockedDownload.mockReset()
    mockedHandleError.mockReset()
  })

  it('POSTs retract params as a query string and does not send a JSON body', async () => {
    mockedApi.mockResolvedValue(textResponse(200, 'G21 G90\nM30\n'))

    const retract = useRetractOperation()
    retract.params.value.strategy = 'helical'
    retract.params.value.current_z = -20
    retract.params.value.safe_z = 12
    retract.params.value.ramp_feed = 800
    retract.params.value.helix_radius = 7.5
    retract.params.value.helix_pitch = 1.5

    await retract.exportGcode()

    expect(mockedApi).toHaveBeenCalledOnce()
    const [url, options] = mockedApi.mock.calls[0]
    expect(url).toMatch(/^\/api\/cam\/retract\/gcode\?/)
    expect(options).toEqual({ method: 'POST' })
    expect(options).not.toHaveProperty('body')

    const query = new URL(String(url), 'http://test.local').searchParams
    expect(query.get('strategy')).toBe('helical')
    expect(query.get('current_z')).toBe('-20')
    expect(query.get('safe_z')).toBe('12')
    expect(query.get('ramp_feed')).toBe('800')
    expect(query.get('helix_radius')).toBe('7.5')
    expect(query.get('helix_pitch')).toBe('1.5')

    expect(mockedDownload).toHaveBeenCalledOnce()
    expect(mockedDownload).toHaveBeenCalledWith(
      'G21 G90\nM30\n',
      'retract_helical.nc'
    )
    expect(mockedHandleError).not.toHaveBeenCalled()
  })

  it('does not call downloadFile when the server returns 409 SAFETY_BLOCKED', async () => {
    mockedApi.mockResolvedValue(
      jsonResponse(409, {
        detail: {
          error: 'SAFETY_BLOCKED',
          message: 'Retract G-code generation blocked by server-side safety policy.'
        }
      })
    )

    const retract = useRetractOperation()
    await retract.exportGcode()

    expect(mockedDownload).not.toHaveBeenCalled()
    expect(mockedHandleError).toHaveBeenCalledOnce()
    expect(mockedHandleError.mock.calls[0][0]).toBe('Retract')
    expect(mockedHandleError.mock.calls[0][1]).toBeInstanceOf(Error)
    expect(mockedHandleError.mock.calls[0][2]).toEqual({ showDetail: true })
  })
})
