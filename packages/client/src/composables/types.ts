/**
 * Shared types for composable extraction pattern.
 *
 * Standard interface pattern:
 *   - Config: Static dependencies (refs passed from parent)
 *   - Deps: Dynamic dependencies (functions, other composable outputs)
 *   - State: What the composable provides (refs, computed, methods)
 *
 * Example:
 *   interface MyConfig extends BaseConfig {
 *     toolD: Ref<number>
 *   }
 *
 *   interface MyDeps extends BaseDeps {
 *     plan: () => Promise<void>
 *   }
 *
 *   interface MyState extends BaseState {
 *     result: Ref<Result>
 *     execute: () => Promise<void>
 *   }
 *
 *   function useMyComposable(config: MyConfig, deps: MyDeps): MyState
 */

import type { Ref, ComputedRef } from 'vue'

// =============================================================================
// Base Interfaces
// =============================================================================

/**
 * Base configuration interface.
 * Extend this for composable-specific config.
 */
export interface BaseConfig {
  /**
   * Whether to persist state to localStorage
   */
  persist?: boolean

  /**
   * localStorage key prefix for persistence
   */
  storageKey?: string

  /**
   * Enable debug logging
   */
  debug?: boolean
}

/**
 * Base dependencies interface.
 * Extend this for composable-specific deps.
 */
export interface BaseDeps {
  // Marker interface - extend with specific dependencies
}

/**
 * Base state interface.
 * Extend this for composable-specific state.
 */
export interface BaseState {
  // Marker interface - extend with specific state
}

// =============================================================================
// Common Ref Types
// =============================================================================

/**
 * A ref that may be null during initialization
 */
export type NullableRef<T> = Ref<T | null>

/**
 * A ref that may be undefined
 */
export type OptionalRef<T> = Ref<T | undefined>

/**
 * Read-only ref (from computed or external source)
 */
export type ReadonlyRef<T> = Readonly<Ref<T>>

// =============================================================================
// Common State Patterns
// =============================================================================

/**
 * Loading state pattern
 */
export interface LoadingState {
  loading: Ref<boolean>
  error: Ref<string | null>
}

/**
 * Async operation state
 */
export interface AsyncState<T> extends LoadingState {
  data: Ref<T | null>
  execute: () => Promise<void>
  reset: () => void
}

/**
 * List with filters pattern
 */
export interface FilteredListState<T, F> {
  items: Ref<T[]>
  filters: Ref<F>
  filteredItems: ComputedRef<T[]>
  setFilter: <K extends keyof F>(key: K, value: F[K]) => void
  clearFilters: () => void
}

/**
 * Selection state pattern
 */
export interface SelectionState<T> {
  selected: Ref<T | null>
  selectedId: Ref<string | null>
  select: (item: T) => void
  clear: () => void
  isSelected: (item: T) => boolean
}

/**
 * Pagination state pattern
 */
export interface PaginationState {
  page: Ref<number>
  pageSize: Ref<number>
  total: Ref<number>
  totalPages: ComputedRef<number>
  hasNext: ComputedRef<boolean>
  hasPrev: ComputedRef<boolean>
  next: () => void
  prev: () => void
  goTo: (page: number) => void
}

/**
 * Form state pattern
 */
export interface FormState<T> {
  values: Ref<T>
  errors: Ref<Partial<Record<keyof T, string>>>
  touched: Ref<Partial<Record<keyof T, boolean>>>
  isDirty: ComputedRef<boolean>
  isValid: ComputedRef<boolean>
  validate: () => boolean
  reset: () => void
  setField: <K extends keyof T>(field: K, value: T[K]) => void
}

/**
 * Modal/dialog state pattern
 */
export interface ModalState<T = void> {
  isOpen: Ref<boolean>
  data: Ref<T | null>
  open: (data?: T) => void
  close: () => void
  toggle: () => void
}

// =============================================================================
// Domain-Specific Types
// =============================================================================

/**
 * CAM/toolpath move
 */
export interface Move {
  code: 'G0' | 'G1' | 'G2' | 'G3'
  x: number
  y: number
  z?: number
  f?: number
  meta?: {
    limit?: string
    slowdown?: number
    trochoid?: boolean
    radius_mm?: number
  }
  _len_mm?: number
}

/**
 * Machine profile
 */
export interface MachineProfile {
  id: string
  name: string
  type: 'router' | 'mill' | 'laser' | 'saw'
  workEnvelope?: {
    x: number
    y: number
    z: number
  }
  maxFeedXY?: number
  maxFeedZ?: number
  maxRPM?: number
  accel?: number
  jerk?: number
}

/**
 * Material definition
 */
export interface Material {
  id: string
  name: string
  category: 'hardwood' | 'softwood' | 'plywood' | 'mdf' | 'acrylic' | 'aluminum' | 'other'
  density?: number
  hardness?: 'soft' | 'medium' | 'hard' | 'very-hard'
  feedMultiplier?: number
}

/**
 * Tool definition
 */
export interface Tool {
  id: string
  name: string
  type: 'endmill' | 'ballnose' | 'vbit' | 'drill' | 'saw'
  diameter: number
  fluteCount?: number
  fluteLength?: number
  stickout?: number
  maxDOC?: number
  maxStepover?: number
}

/**
 * Risk level for RMOS decisions
 */
export type RiskLevel = 'GREEN' | 'YELLOW' | 'RED'

/**
 * RMOS feasibility result
 */
export interface FeasibilityResult {
  decision: RiskLevel
  rules_triggered: Array<{
    id: string
    level: RiskLevel
    message: string
    hint?: string
  }>
  export_allowed: boolean
  block_reason?: string
}

// =============================================================================
// Utility Types
// =============================================================================

/**
 * Extract the return type of a composable function
 */
export type ComposableReturn<T extends (...args: any[]) => any> = ReturnType<T>

/**
 * Make all refs in an object writable
 */
export type WritableRefs<T> = {
  [K in keyof T]: T[K] extends Readonly<Ref<infer U>> ? Ref<U> : T[K]
}

/**
 * Extract ref value types from a state interface
 */
export type UnwrapRefs<T> = {
  [K in keyof T]: T[K] extends Ref<infer U> ? U : T[K] extends ComputedRef<infer U> ? U : T[K]
}
