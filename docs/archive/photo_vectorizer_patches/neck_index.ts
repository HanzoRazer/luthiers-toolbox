/**
 * packages/client/src/design-utilities/lutherie/neck/index.ts
 *
 * Re-exports all neck composables for the luthiers-toolbox-main integration.
 *
 * Copy this folder to:
 *   packages/client/src/design-utilities/lutherie/neck/
 *
 * Files to copy:
 *   useFretboard.ts
 *   useNeckProfile.ts
 *   useNeckTaper.ts
 *   useHeadstockTransition.ts
 *   useCamSpec.ts
 *   drawCamOverlay.ts
 *   index.ts  (this file)
 */

export { useFretboard }          from './useFretboard'
export { useNeckProfile }        from './useNeckProfile'
export { useNeckTaper }          from './useNeckTaper'
export { useHeadstockTransition } from './useHeadstockTransition'
export { useCamSpec }            from './useCamSpec'
export { drawCamOverlay }        from './drawCamOverlay'

// Re-export pure geometry functions for use outside composables
export {
  fretPosition, boardWidthAtFret, radiusAtFret, sagittaHeight,
  stepoverMm, passCount,
} from './useFretboard'

export {
  shapeY, sampleProfile,
  COMPOUND_SHAPES,
} from './useNeckProfile'

export {
  neckWidthAtFret, edgeMarginAtFret, stringPositionsAtFret, bevelOffsetMm,
} from './useNeckTaper'

export {
  surfaceZ, voluteZ, headstockPlaneZ, blendZ, regionAt, thinPointMm,
  TRANSITION_PRESETS,
} from './useHeadstockTransition'
