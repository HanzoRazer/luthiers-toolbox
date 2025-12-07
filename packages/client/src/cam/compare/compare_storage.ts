import type { CompareBaseline, CompareCandidate } from "./compare_types"

const LS_BASELINE_LAST = "compare_last_baseline"
const LS_CANDIDATE_LAST = "compare_last_candidate"
const LS_TOLERANCE_LAST = "compare_last_tolerance"

export function saveLastBaseline(b: CompareBaseline) {
  try { localStorage.setItem(LS_BASELINE_LAST, JSON.stringify(b)) } catch {}
}
export function saveLastCandidate(c: CompareCandidate) {
  try { localStorage.setItem(LS_CANDIDATE_LAST, JSON.stringify(c)) } catch {}
}
export function loadLastBaseline(): CompareBaseline | null {
  try {
    const raw = localStorage.getItem(LS_BASELINE_LAST)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}
export function loadLastCandidate(): CompareCandidate | null {
  try {
    const raw = localStorage.getItem(LS_CANDIDATE_LAST)
    return raw ? JSON.parse(raw) : null
  } catch { return null }
}
export function saveLastTolerance(tol: number) {
  try { localStorage.setItem(LS_TOLERANCE_LAST, tol.toString()) } catch {}
}
export function loadLastTolerance(): number | null {
  try {
    const raw = localStorage.getItem(LS_TOLERANCE_LAST)
    return raw ? parseFloat(raw) : null
  } catch { return null }
}
