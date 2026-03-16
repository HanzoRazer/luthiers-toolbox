// packages/client/src/instrument-workspace/shared-state/project-types.ts
/**
 * Project type utilities and stage definitions (HUB-002/004)
 *
 * Centralises:
 *   - Instrument Hub stage definitions (Body/Neck/Bridge/Bracing/Setup/CNC Prep)
 *   - Instrument category display labels and icons
 *   - Stage completion heuristics (derived from project state)
 *
 * Used by InstrumentHubShell.vue and InstrumentStageNavigator.vue.
 *
 * See docs/PLATFORM_ARCHITECTURE.md — Layer 2 / Workspaces.
 */

import type { InstrumentCategory, InstrumentProjectData } from '@/api/projects'

// ---------------------------------------------------------------------------
// Hub stage definitions (HUB-004)
// ---------------------------------------------------------------------------

export type HubStageId =
  | 'body'
  | 'neck'
  | 'bridge'
  | 'bracing'
  | 'setup'
  | 'cnc-prep'

export interface HubStage {
  id: HubStageId
  label: string
  icon: string
  description: string
  /** Route for direct-link access to this stage (future — Phase 5 cleanup) */
  route: string
  /** Instrument categories where this stage is relevant */
  applicableTo: InstrumentCategory[] | 'all'
}

export const HUB_STAGES: HubStage[] = [
  {
    id: 'body',
    label: 'Body',
    icon: '🎸',
    description: 'Body outline, dimensions, and material selection',
    route: '/design/body',
    applicableTo: 'all',
  },
  {
    id: 'neck',
    label: 'Neck',
    icon: '🎵',
    description: 'Scale length, fret count, neck angle, profile, and headstock',
    route: '/design/neck',
    applicableTo: 'all',
  },
  {
    id: 'bridge',
    label: 'Bridge',
    icon: '🌉',
    description: 'Saddle location, compensation, break angle, and string spacing',
    route: '/design/bridge',
    applicableTo: ['acoustic_guitar', 'electric_guitar', 'bass', 'classical', 'archtop', 'custom'],
  },
  {
    id: 'bracing',
    label: 'Bracing',
    icon: '🏗️',
    description: 'Top brace layout, dimensions, and structural design',
    route: '/design/bracing',
    applicableTo: ['acoustic_guitar', 'classical', 'archtop'],
  },
  {
    id: 'setup',
    label: 'Setup',
    icon: '🔧',
    description: 'Action, nut slots, intonation, and final adjustments',
    route: '/design/setup',
    applicableTo: 'all',
  },
  {
    id: 'cnc-prep',
    label: 'CNC Prep',
    icon: '⚙️',
    description: 'Review design, validate geometry, and approve for CNC',
    route: '/design/cnc-prep',
    applicableTo: 'all',
  },
]

/** Stages relevant to a given instrument category */
export function getApplicableStages(type: InstrumentCategory | null): HubStage[] {
  if (!type) return HUB_STAGES
  return HUB_STAGES.filter(
    (s) => s.applicableTo === 'all' || s.applicableTo.includes(type)
  )
}

// ---------------------------------------------------------------------------
// Stage completion heuristics
// These are lightweight derived checks, not engine math.
// ---------------------------------------------------------------------------

export function getStageCompletion(
  stageId: HubStageId,
  state: InstrumentProjectData | null,
): 'complete' | 'partial' | 'empty' {
  if (!state) return 'empty'

  switch (stageId) {
    case 'body':
      if (state.material_selection?.top || state.blueprint_geometry?.body_length_mm)
        return 'complete'
      if (state.instrument_type) return 'partial'
      return 'empty'

    case 'neck':
      if (state.spec?.scale_length_mm && state.spec?.fret_count && state.spec?.neck_angle_degrees !== undefined)
        return 'complete'
      if (state.spec?.scale_length_mm) return 'partial'
      return 'empty'

    case 'bridge':
      if (state.bridge_state?.saddle_line_from_nut_mm) return 'complete'
      if (state.bridge_state) return 'partial'
      return 'empty'

    case 'bracing':
      // No bracing state yet in schema — placeholder
      return 'empty'

    case 'setup':
      return state.spec ? 'partial' : 'empty'

    case 'cnc-prep':
      if (state.manufacturing_state?.status === 'cam_approved') return 'complete'
      if (state.manufacturing_state?.status === 'design_complete') return 'partial'
      return 'empty'

    default:
      return 'empty'
  }
}

// ---------------------------------------------------------------------------
// Instrument category display
// ---------------------------------------------------------------------------

export const INSTRUMENT_LABELS: Record<InstrumentCategory, { label: string; icon: string }> = {
  acoustic_guitar:  { label: 'Acoustic Guitar',  icon: '🎸' },
  electric_guitar:  { label: 'Electric Guitar',  icon: '⚡' },
  bass:             { label: 'Bass Guitar',       icon: '🎵' },
  classical:        { label: 'Classical Guitar',  icon: '🎼' },
  archtop:          { label: 'Archtop Guitar',    icon: '🎷' },
  violin:           { label: 'Violin / Viola',    icon: '🎻' },
  mandolin:         { label: 'Mandolin',          icon: '🪕' },
  ukulele:          { label: 'Ukulele',           icon: '🌺' },
  banjo:            { label: 'Banjo',             icon: '🥁' },
  custom:           { label: 'Custom Instrument', icon: '🔨' },
}

export function getInstrumentLabel(type: InstrumentCategory | null): string {
  if (!type) return 'No instrument selected'
  return INSTRUMENT_LABELS[type]?.label ?? type
}

export function getInstrumentIcon(type: InstrumentCategory | null): string {
  if (!type) return '🎸'
  return INSTRUMENT_LABELS[type]?.icon ?? '🎸'
}
