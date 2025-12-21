export interface CamCoreTool {
  id: string
  name: string
  diameterMm: number
  lengthMm: number
  kind: 'router' | 'saw' | 'drill'
  vendor?: string
}

export interface SawLabRunSummary {
  id: string
  createdAt: string
  cutCount: number
  status: string
}
