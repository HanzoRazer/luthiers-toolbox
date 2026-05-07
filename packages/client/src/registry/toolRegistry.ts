/**
 * Tool Registry — simple typed array of registered workspace tools.
 */

export type ToolCategory = 'aperture' | 'neck' | 'setup' | 'rosette' | 'pattern' | 'calculator'

export type ToolStatus = 'stable' | 'beta' | 'experimental'

export interface ToolCapabilities {
  export?: string[]
  import?: string[]
}

export interface ToolMetadata {
  canonical?: boolean
  implementation?: string
  migrationState?: string
  mounts?: string[]
}

export interface ToolEntry {
  id: string
  label: string
  category: ToolCategory
  route: string
  status: ToolStatus
  capabilities?: ToolCapabilities
  metadata?: ToolMetadata
}

export const toolRegistry: ToolEntry[] = [
  {
    id: 'neck-setup',
    label: 'Neck Setup Diagnostics',
    category: 'setup',
    route: '/instrument-geometry/setup',
    status: 'stable',
    capabilities: {
      export: ['json'],
      import: ['preset'],
    },
  },
  {
    id: 'spiral-soundhole',
    label: 'Spiral Soundhole Designer',
    category: 'aperture',
    route: '/calculators/acoustics/spiral-soundhole',
    status: 'stable',
    capabilities: {
      export: ['dxf'],
      import: ['preset'],
    },
    metadata: {
      canonical: true,
      implementation: 'SpiralSoundholeDesigner.vue',
      migrationState: 'canonical-production-tool',
    },
  },
  {
    id: 'aperture-workspace',
    label: 'Aperture Workspace',
    category: 'aperture',
    route: '/art-studio/aperture',
    status: 'beta',
    capabilities: {
      export: ['dxf', 'svg', 'json'],
      import: ['preset'],
    },
    metadata: {
      canonical: false,
      migrationState: 'beta-consolidation-shell',
      mounts: ['SpiralSoundholeDesigner.vue'],
    },
  },
]

export function getToolById(id: string): ToolEntry | undefined {
  return toolRegistry.find((t) => t.id === id)
}

export function getToolsByCategory(category: ToolCategory): ToolEntry[] {
  return toolRegistry.filter((t) => t.category === category)
}

export function getToolsByStatus(status: ToolStatus): ToolEntry[] {
  return toolRegistry.filter((t) => t.status === status)
}
