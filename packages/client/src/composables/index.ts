/**
 * Generic composables barrel export.
 *
 * These are domain-agnostic utilities extracted and genericized from
 * component-level composables across the toolbox, RMOS, and adaptive
 * domains.  Import from here instead of reaching into component dirs.
 */
export { useListFilters } from './useListFilters'
export type { FilterableRow, FilterPrefs, UseListFiltersOptions } from './useListFilters'

export { useListSelection } from './useListSelection'
export type { SelectableItem } from './useListSelection'

export { useParametricSettings } from './useParametricSettings'
export type { FieldSpec, ValidationError, UseParametricSettingsOptions } from './useParametricSettings'

export { useDimensionEditor } from './useDimensionEditor'
export type { DimensionField, DimensionPreset, UseDimensionEditorOptions } from './useDimensionEditor'

export { useMaterialCalculator, calculateBoardFeet, calculateCost, calculateVolumeCm3, calculateWeight, calculateAngle, calculateComplementaryAngle } from './useMaterialCalculator'
export type { BoardFeetInput, VolumeInput, AngleInput, MaterialSpec } from './useMaterialCalculator'

export { useFormulaCalculator } from './useFormulaCalculator'
export type { FormulaParam, FormulaPreset, ThresholdRange, UseFormulaCalculatorOptions } from './useFormulaCalculator'

export { useUnitConverter, convert, UNITS, UNIT_CATEGORIES } from './useUnitConverter'
export type { UnitDef, UnitCategory } from './useUnitConverter'

export { useSavedViews } from './useSavedViews'
export type { SavedView, ViewSortMode, UseSavedViewsOptions } from './useSavedViews'

export { useBulkDecision } from './useBulkDecision'
export type {
  RiskDecision,
  BulkUndoItem,
  BulkActionRecord,
  BulkProgress,
  CandidateMinimal,
  UseBulkDecisionOptions,
} from './useBulkDecision'
