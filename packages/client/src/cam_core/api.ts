import type { CamCoreTool, SawLabRunSummary } from './types'

const CAM_CORE_BASE = '/api/cam-core'

export async function fetchSawLabRuns(): Promise<SawLabRunSummary[]> {
  await Promise.resolve()
  return []
}

export async function fetchCamCoreTools(): Promise<CamCoreTool[]> {
  await Promise.resolve()
  return []
}
