/**
 * stores/variants.ts
 *
 * Variant library — save / load / track parametric headstock and neck designs.
 *
 * Each variant captures a snapshot of the headstock Pinia store export payload
 * plus the neck store export payload, assigned a human name and ERP status.
 *
 * Status flow:  draft → approved → queued → cut → shipped
 *               (can also be: rejected, on_hold)
 *
 * Persisted to localStorage under key 'ps_variants_v1'.
 * Compatible with the Production Shop ERP quoting module.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// ─── Types ────────────────────────────────────────────────────────────────────

export type VariantStatus =
  | 'draft'
  | 'approved'
  | 'queued'
  | 'cut'
  | 'shipped'
  | 'rejected'
  | 'on_hold'

export interface Variant {
  id:          string       // uuid-lite: timestamp + random
  name:        string
  status:      VariantStatus
  createdAt:   string       // ISO
  updatedAt:   string       // ISO
  notes:       string

  // Snapshot payloads (from exportPayload computed on each store)
  headstock:   Record<string, any> | null
  neck:        Record<string, any> | null

  // ERP metadata
  orderId:     string       // linked order number (empty = unlinked)
  quantity:    number
  materialCostEst: number   // USD, 0 = not estimated
}

export const STATUS_LABELS: Record<VariantStatus, string> = {
  draft:    'Draft',
  approved: 'Approved',
  queued:   'Queued',
  cut:      'Cut',
  shipped:  'Shipped',
  rejected: 'Rejected',
  on_hold:  'On hold',
}

export const STATUS_ORDER: VariantStatus[] = [
  'draft', 'approved', 'queued', 'cut', 'shipped',
]

export const STATUS_COLORS: Record<VariantStatus, string> = {
  draft:    '#7a6448',
  approved: '#5ab86a',
  queued:   '#5b8fa8',
  cut:      '#b8962e',
  shipped:  '#9a60c8',
  rejected: '#c84030',
  on_hold:  '#c87030',
}

// ─── Storage ──────────────────────────────────────────────────────────────────

const STORAGE_KEY = 'ps_variants_v1'

function loadFromStorage(): Variant[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function saveToStorage(variants: Variant[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(variants))
  } catch { /* quota exceeded or SSR */ }
}

function makeId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useVariantStore = defineStore('variants', () => {

  const variants = ref<Variant[]>(loadFromStorage())
  const activeId  = ref<string | null>(null)

  // ── Derived ──────────────────────────────────────────────────────────────

  const byStatus = computed(() => {
    const groups: Record<VariantStatus, Variant[]> = {
      draft: [], approved: [], queued: [], cut: [], shipped: [],
      rejected: [], on_hold: [],
    }
    variants.value.forEach(v => { groups[v.status]?.push(v) })
    return groups
  })

  const active = computed(() =>
    variants.value.find(v => v.id === activeId.value) ?? null
  )

  const counts = computed(() =>
    Object.fromEntries(
      Object.entries(byStatus.value).map(([k, v]) => [k, v.length])
    ) as Record<VariantStatus, number>
  )

  // ── Actions ───────────────────────────────────────────────────────────────

  function save(persist = true) {
    if (persist) saveToStorage(variants.value)
  }

  function createVariant(
    name: string,
    headstockPayload: Record<string, any> | null = null,
    neckPayload:      Record<string, any> | null = null,
    notes = '',
  ): Variant {
    const now = new Date().toISOString()
    const v: Variant = {
      id:              makeId(),
      name:            name || `Variant ${variants.value.length + 1}`,
      status:          'draft',
      createdAt:       now,
      updatedAt:       now,
      notes,
      headstock:       headstockPayload,
      neck:            neckPayload,
      orderId:         '',
      quantity:        1,
      materialCostEst: 0,
    }
    variants.value.unshift(v)
    activeId.value = v.id
    save()
    return v
  }

  function updateVariant(id: string, patch: Partial<Omit<Variant, 'id' | 'createdAt'>>) {
    const idx = variants.value.findIndex(v => v.id === id)
    if (idx === -1) return
    variants.value[idx] = {
      ...variants.value[idx],
      ...patch,
      updatedAt: new Date().toISOString(),
    }
    save()
  }

  function advanceStatus(id: string) {
    const v = variants.value.find(x => x.id === id)
    if (!v) return
    const idx = STATUS_ORDER.indexOf(v.status)
    if (idx === -1 || idx >= STATUS_ORDER.length - 1) return
    updateVariant(id, { status: STATUS_ORDER[idx + 1] })
  }

  function setStatus(id: string, status: VariantStatus) {
    updateVariant(id, { status })
  }

  function deleteVariant(id: string) {
    variants.value = variants.value.filter(v => v.id !== id)
    if (activeId.value === id) activeId.value = variants.value[0]?.id ?? null
    save()
  }

  function duplicateVariant(id: string): Variant | null {
    const src = variants.value.find(v => v.id === id)
    if (!src) return null
    return createVariant(
      `${src.name} (copy)`,
      src.headstock ? { ...src.headstock } : null,
      src.neck      ? { ...src.neck }      : null,
      src.notes,
    )
  }

  /** Overwrite the active variant's snapshot with fresh payload data */
  function refreshSnapshot(
    id: string,
    headstockPayload: Record<string, any> | null,
    neckPayload:      Record<string, any> | null,
  ) {
    updateVariant(id, { headstock: headstockPayload, neck: neckPayload })
  }

  function clearAll() {
    variants.value = []
    activeId.value = null
    save()
  }

  function exportJSON(): string {
    return JSON.stringify(variants.value, null, 2)
  }

  function importJSON(raw: string): number {
    try {
      const data = JSON.parse(raw) as Variant[]
      if (!Array.isArray(data)) throw new Error('Expected array')
      // Merge — skip duplicates by id
      const existing = new Set(variants.value.map(v => v.id))
      const added = data.filter(v => !existing.has(v.id))
      variants.value.unshift(...added)
      save()
      return added.length
    } catch {
      return 0
    }
  }

  return {
    variants,
    activeId,
    active,
    byStatus,
    counts,
    createVariant,
    updateVariant,
    advanceStatus,
    setStatus,
    deleteVariant,
    duplicateVariant,
    refreshSnapshot,
    clearAll,
    exportJSON,
    importJSON,
  }
})
