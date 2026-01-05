<script setup lang="ts">
import { computed, onMounted, ref, watch, onBeforeUnmount } from "vue";
import CandidateDecisionHistoryPopover from "@/components/rmos/CandidateDecisionHistoryPopover.vue";
import {
  decideManufacturingCandidate,
  downloadManufacturingCandidateZip,
  listManufacturingCandidates,
  type ManufacturingCandidate,
  type RiskLevel,
} from "@/sdk/rmos/runs";

const props = defineProps<{
  runId: string;
}>();

type CandidateRow = ManufacturingCandidate & {
  candidate_id: string;
};

const loading = ref(false);
const error = ref<string | null>(null);
const requestId = ref<string>("");

const candidates = ref<CandidateRow[]>([]);

// -------------------------
// Filters (product-only)
// -------------------------
type DecisionFilter = "ALL" | "UNDECIDED" | "GREEN" | "YELLOW" | "RED";
type StatusFilter = "ALL" | "PROPOSED" | "ACCEPTED" | "REJECTED";

const decisionFilter = ref<DecisionFilter>("ALL");
const statusFilter = ref<StatusFilter>("ALL");
const showSelectedOnly = ref(false);
const searchText = ref("");

// micro-follow: decided-by filter (product-only)
const filterDecidedBy = ref<string>("ALL");
const decidedByOptions = computed(() => {
  const set = new Set<string>();
  for (const c of candidates.value) {
    const v = (c.decided_by ?? "").trim();
    if (v) set.add(v);
  }
  return Array.from(set).sort((a, b) => a.localeCompare(b));
});

// micro-follow: density toggle (compact mode) for long runs
const compact = ref<boolean>(false);

// micro-follow: persist view prefs (filters + density) to localStorage (product-only)
const PREF_KEY = computed(() => `rmos:candidates:prefs:${props.runId || "unknown"}`);
type PrefsV1 = {
  decisionFilter: string;
  statusFilter: string;
  searchText: string;
  showSelectedOnly: boolean;
  compact: boolean;
  sortKey: string;
};
function _readPrefs(): PrefsV1 | null {
  try {
    const raw = localStorage.getItem(PREF_KEY.value);
    if (!raw) return null;
    const obj = JSON.parse(raw) as Partial<PrefsV1>;
    if (!obj) return null;
    return {
      decisionFilter: obj.decisionFilter ?? "ALL",
      statusFilter: obj.statusFilter ?? "ALL",
      searchText: obj.searchText ?? "",
      showSelectedOnly: obj.showSelectedOnly ?? false,
      compact: obj.compact ?? false,
      sortKey: obj.sortKey ?? "id",
    };
  } catch {
    return null;
  }
}
function _writePrefs(p: PrefsV1) {
  try { localStorage.setItem(PREF_KEY.value, JSON.stringify(p)); } catch { /* ignore */ }
}

let _prefsTimer: number | null = null;
function schedulePrefsSave() {
  if (_prefsTimer) window.clearTimeout(_prefsTimer);
  _prefsTimer = window.setTimeout(() => {
    _writePrefs({
      decisionFilter: decisionFilter.value,
      statusFilter: statusFilter.value,
      searchText: searchText.value,
      showSelectedOnly: showSelectedOnly.value,
      compact: compact.value,
      sortKey: sortKey.value,
    });
  }, 250);
}

function resetViewPrefs() {
  decisionFilter.value = "ALL";
  statusFilter.value = "ALL";
  searchText.value = "";
  showSelectedOnly.value = false;
  compact.value = false;
  sortKey.value = "id";
  schedulePrefsSave();
  showToast("View reset");
}

// Copy-to-clipboard toast
const toast = ref<string | null>(null);
let _toastTimer: number | null = null;
function showToast(msg: string) {
  toast.value = msg;
  if (_toastTimer) window.clearTimeout(_toastTimer);
  _toastTimer = window.setTimeout(() => { toast.value = null; }, 2000);
}

type SortKey = "id" | "id_desc" | "created" | "created_desc" | "status" | "decision";
const sortKey = ref<SortKey>("id");

// Save / decision state
const saving = ref(false);
const saveError = ref<string | null>(null);

// history popover (product-only)
const openHistoryFor = ref<string | null>(null);

// Inline note editor state
const editingId = ref<string | null>(null);
const editValue = ref<string>("");

// micro-follow: keyboard shortcuts (product-only)
// - g/y/r: bulk set decision GREEN/YELLOW/RED for selected
// - u: clear decision (NEEDS_DECISION) for selected
// - e: export GREEN-only zips (requires all decided)
// - a: select all shown (post-filter)
// - c: clear shown (post-filter)
// - esc: clear selection
function _isTypingContext(): boolean {
  const el = document.activeElement as HTMLElement | null;
  if (!el) return false;
  const tag = (el.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  if ((el as any).isContentEditable) return true;
  return false;
}

function _clearSelection() {
  selectedIds.value = new Set();
}

function _hotkeyHelp(): string {
  return [
    "Hotkeys:",
    "g/y/r = Bulk decision GREEN/YELLOW/RED",
    "u = Clear decision (NEEDS_DECISION)",
    "b = Bulk clear decision (selected)",
    "e = Export GREEN-only (all must be decided)",
    "a = Select shown (post-filter)",
    "c = Clear shown (post-filter)",
    "i = Invert selection (shown rows)",
    "x = Clear all selection",
    "h = Toggle bulk history panel",
    "esc = Clear selection",
  ].join("\n");
}

function _onKeydown(ev: KeyboardEvent) {
  if (ev.defaultPrevented) return;
  if (_isTypingContext()) return;

  const k = (ev.key || "").toLowerCase();
  if (k === "escape") {
    ev.preventDefault();
    _clearSelection();
    return;
  }
  if (k === "a") {
    ev.preventDefault();
    selectAllFiltered();
    return;
  }
  if (k === "c") {
    ev.preventDefault();
    clearAllFiltered();
    return;
  }
  if (k === "i") {
    ev.preventDefault();
    invertSelectionFiltered();
    return;
  }
  if (k === "x") {
    ev.preventDefault();
    _clearSelection();
    return;
  }
  if (k === "h") {
    ev.preventDefault();
    showBulkHistory.value = !showBulkHistory.value;
    return;
  }
  if (k === "b") {
    if (selectedIds.value.size > 0) {
      ev.preventDefault();
      void clearBulkDecision();
    }
    return;
  }
  if (selectedIds.value.size === 0) return; // decision hotkeys require selection
  if (k === "g") { ev.preventDefault(); bulkSetDecision("GREEN"); return; }
  if (k === "y") { ev.preventDefault(); bulkSetDecision("YELLOW"); return; }
  if (k === "r") { ev.preventDefault(); bulkSetDecision("RED"); return; }
  if (k === "u") { ev.preventDefault(); bulkClearDecision(); return; }
  if (k === "e") { ev.preventDefault(); exportGreenOnlyZips(); return; }
}

// Copy-to-clipboard helper
async function copyText(label: string, value: string) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value);
    } else {
      // fallback for older browsers
      const ta = document.createElement("textarea");
      ta.value = value;
      ta.style.position = "fixed";
      ta.style.left = "-9999px";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    showToast(`Copied ${label}`);
  } catch {
    showToast("Copy failed");
  }
}

// Bulk export state
const exporting = ref(false);
const exportError = ref<string | null>(null);

// Selection state (bulk decision)
const selectedIds = ref<Set<string>>(new Set());
const lastClickedId = ref<string | null>(null);
const selectingAll = computed(() => candidates.value.length > 0 && selectedIds.value.size === candidates.value.length);

// Undo stack for bulk decisions (client-side)
type UndoItem = {
  ts_utc: string;
  run_id: string;
  label: string;
  applied_decision: RiskLevel;
  candidate_ids: string[];
  // snapshot needed to restore
  prev: Record<
    string,
    {
      decision: RiskLevel | null;
      decision_note: string | null;
    }
  >;
};
const undoStack = ref<UndoItem[]>([]);
const undoBusy = ref(false);
const undoError = ref<string | null>(null);

// -----------------------------------------------------------------------------
// micro-follow: bulk set decision v2 (dropdown + shared note + history panel)
// + undo history display (product-only, still wired to runs.ts)
// -----------------------------------------------------------------------------
type RiskDecision = "GREEN" | "YELLOW" | "RED";
type BulkUndoItem = {
  candidate_id: string;
  prev_decision: RiskDecision | null;
  prev_note: string | null;
  next_decision: RiskDecision | null;
  next_note: string | null;
};
type BulkActionRecord = {
  id: string;
  at_utc: string;
  decision: RiskDecision | null;
  note: string | null;
  selected_count: number;
  applied_count: number;
  failed_count: number;
  items: BulkUndoItem[];
};

const bulkDecision = ref<RiskDecision | null>(null);
const bulkNote = ref<string>("");
const bulkApplying = ref(false);
const bulkProgress = ref<{ total: number; done: number; fail: number } | null>(null);
const bulkHistory = ref<BulkActionRecord[]>([]);
const showBulkHistory = ref(false);

const bulkClearNoteToo = ref<boolean>(false);

function _utcNowIso(): string {
  return new Date().toISOString();
}
function _mkId(prefix = "bulk"): string {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now()}`;
}
function _selectedCandidates(): CandidateRow[] {
  const ids = selectedIds.value;
  return candidates.value.filter((c) => ids.has(c.candidate_id));
}
function _findCandidate(id: string): CandidateRow | null {
  return candidates.value.find((c) => c.candidate_id === id) ?? null;
}
function _updateCandidateFromDecisionResponse(id: string, res: any) {
  const idx = candidates.value.findIndex((x) => x.candidate_id === id);
  if (idx === -1) return;
  candidates.value[idx] = {
    ...candidates.value[idx],
    decision: (res.decision ?? null) as any,
    status: (res.status ?? candidates.value[idx].status) as any,
    decision_note: (res.decision_note ?? null) as any,
    decided_at_utc: (res.decided_at_utc ?? null) as any,
    decided_by: (res.decided_by ?? null) as any,
    decision_history: (res.decision_history ?? candidates.value[idx].decision_history ?? null) as any,
  };
}

// -----------------------------------------------------------------------------
// micro-follow: bulk CLEAR decision (set decision=null) for selected candidates
// (keeps UI + backend perfectly aligned to "needs explicit operator decision")
// -----------------------------------------------------------------------------
async function clearBulkDecision() {
  if (bulkApplying.value) return;
  const sel = _selectedCandidates();
  if (!sel.length) {
    showToast("No candidates selected", "err");
    return;
  }

  bulkApplying.value = true;
  bulkProgress.value = { total: sel.length, done: 0, fail: 0 };

  const record: BulkActionRecord = {
    id: _mkId("bulk_clear"),
    at_utc: _utcNowIso(),
    decision: null,
    note: bulkClearNoteToo.value ? null : null,
    selected_count: sel.length,
    applied_count: 0,
    failed_count: 0,
    items: [],
  };

  try {
    for (const c of sel) {
      const prev_decision = (c.decision ?? null) as any;
      const prev_note = (c.decision_note ?? null) as any;
      const next_decision = null;
      const next_note = bulkClearNoteToo.value ? null : prev_note;

      record.items.push({
        candidate_id: c.candidate_id,
        prev_decision,
        prev_note,
        next_decision: (next_decision as any),
        next_note,
      });

      try {
        const res = await decideManufacturingCandidate(runId.value, c.candidate_id, {
          decision: next_decision,
          note: next_note,
        } as any);
        _updateCandidateFromDecisionResponse(c.candidate_id, res);
        record.applied_count += 1;
      } catch (e) {
        record.failed_count += 1;
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done,
          fail: bulkProgress.value!.fail + 1,
        };
      } finally {
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done + 1,
          fail: bulkProgress.value!.fail,
        };
      }
    }

    bulkHistory.value = [record, ...bulkHistory.value].slice(0, 10);
    showToast(
      record.failed_count
        ? `Bulk clear done (${record.applied_count} ok, ${record.failed_count} failed)`
        : "Cleared decision for selected candidates",
      record.failed_count ? "err" : "ok"
    );
  } finally {
    bulkApplying.value = false;
    window.setTimeout(() => (bulkProgress.value = null), 900);
  }
}

function decisionBadge(decision: RiskLevel | null | undefined) {
  if (decision == null) return "NEEDS_DECISION";
  return decision;
}

function normalize(s: unknown) {
  return String(s ?? "").trim().toLowerCase();
}

function matchesSearch(c: CandidateRow, q: string) {
  if (!q) return true;
  const hay = [
    c.candidate_id,
    c.advisory_id ?? "",
    c.decision_note ?? "",
    c.decided_by ?? "",
    c.created_by ?? "",
  ].map(normalize).join(" | ");
  return hay.includes(q);
}

function statusText(c: CandidateRow) {
  if (c.decision == null) return "Needs decision";
  if (c.decision === "GREEN") return "Accepted";
  if (c.decision === "YELLOW") return "Caution";
  if (c.decision === "RED") return "Rejected";
  return "—";
}

function notePreview(note?: string | null) {
  const n = note ?? "";
  if (!n) return "—";
  return n.length > 120 ? n.slice(0, 120) + "…" : n;
}

function _fmtAuditLine(h: { decision?: string | null; decided_by?: string | null; decided_at_utc?: string | null; note?: string | null }) {
  const d = h.decision ?? "—";
  const who = h.decided_by ?? "—";
  const when = h.decided_at_utc ?? "—";
  const note = h.note ? ` "${h.note.slice(0, 40)}${h.note.length > 40 ? '…' : ''}"` : "";
  return `${d} · ${who} · ${when}${note}`;
}

function auditHover(c: CandidateRow) {
  const who = c.decided_by ?? "—";
  const when = c.decided_at_utc ?? "—";
  const note = c.decision_note ?? "";
  const preview = note ? (note.length > 80 ? note.slice(0, 80) + "…" : note) : "—";

  const lines = [
    `Decision: ${decisionBadge(c.decision)}`,
    `By: ${who}`,
    `At: ${when}`,
    `Note: ${preview}`,
  ];

  if (c.decision_history && c.decision_history.length > 0) {
    lines.push("History:");
    for (const h of c.decision_history.slice(-5)) {
      lines.push(`  ${_fmtAuditLine(h)}`);
    }
  }

  return lines.join("\n");
}

function openDecisionHistory(id: string) {
  openHistoryFor.value = openHistoryFor.value === id ? null : id;
}

async function load() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  exportError.value = null;
  undoError.value = null;
  try {
    const res = await listManufacturingCandidates(props.runId);
    candidates.value = (res.items ?? []) as CandidateRow[];
    requestId.value = res.requestId ?? "";
    // prune selection set to only existing candidates
    const existing = new Set(candidates.value.map((c) => c.candidate_id));
    const next = new Set<string>();
    for (const id of selectedIds.value) if (existing.has(id)) next.add(id);
    selectedIds.value = next;
    // If you were in "selected only" mode and selection got emptied, auto-disable it.
    if (showSelectedOnly.value && selectedIds.value.size === 0) showSelectedOnly.value = false;
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  // restore prefs first (so first render matches user intent)
  const p = _readPrefs();
  if (p) {
    decisionFilter.value = p.decisionFilter as DecisionFilter;
    statusFilter.value = p.statusFilter as StatusFilter;
    searchText.value = p.searchText;
    showSelectedOnly.value = p.showSelectedOnly;
    compact.value = p.compact;
    sortKey.value = (p.sortKey as SortKey) || "id";
  }

  load();
  window.addEventListener("keydown", _onKeydown, { capture: true });
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", _onKeydown, { capture: true } as any);
  if (_toastTimer) window.clearTimeout(_toastTimer);
  if (_prefsTimer) window.clearTimeout(_prefsTimer);
});

watch(() => props.runId, load);

watch([decisionFilter, statusFilter, searchText, showSelectedOnly, compact, sortKey], () => {
  schedulePrefsSave();
});

function startEdit(c: CandidateRow) {
  // Spine-locked: don't allow note editing until a decision exists
  if (c.decision == null) return;
  editingId.value = c.candidate_id;
  editValue.value = c.decision_note ?? "";
  saveError.value = null;
}

function cancelEdit() {
  editingId.value = null;
  editValue.value = "";
  saveError.value = null;
}

async function saveEdit(c: CandidateRow) {
  if (!props.runId) return;
  if (c.decision == null) return;
  saving.value = true;
  saveError.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision: c.decision, // keep decision stable; update note only
      note: editValue.value,
      decided_by: null,
    });
    requestId.value = res.requestId ?? requestId.value;

    const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
    if (idx >= 0) {
      candidates.value[idx] = {
        ...candidates.value[idx],
        decision: (res.decision ?? candidates.value[idx].decision ?? null) as any,
        status: (res.status ?? candidates.value[idx].status ?? null) as any,
        decision_note: res.decision_note ?? editValue.value,
        decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
        decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
        decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
      };
    }
    cancelEdit();
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function decide(c: CandidateRow, decision: RiskLevel) {
  if (!props.runId) return;
  saving.value = true;
  saveError.value = null;
  try {
    const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
      decision,
      note: c.decision_note ?? null,
      decided_by: null,
    });
    requestId.value = res.requestId ?? requestId.value;

    const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
    if (idx >= 0) {
      candidates.value[idx] = {
        ...candidates.value[idx],
        decision: (res.decision ?? decision) as any,
        status: (res.status ?? candidates.value[idx].status ?? null) as any,
        decision_note: res.decision_note ?? candidates.value[idx].decision_note ?? null,
        decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
        decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
        decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
      };
    }
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

// -------------------------
// Bulk decision (GREEN/YELLOW/RED) with undo
// -------------------------
const selectedRows = computed(() => {
  const s = selectedIds.value;
  return candidates.value.filter((c) => s.has(c.candidate_id));
});

// micro-follow: bulk clear decision (set to null) for selected
// This aligns with migration: decision=null == NEEDS_DECISION
// Clears decision_note as well (note is tied to decision record).
// Uses decideManufacturingCandidate() only (runs.ts lockpoint).

function canBulkClearDecision(): { ok: boolean; reason?: string } {
  const sel = selectedRows.value;
  if (sel.length === 0) return { ok: false, reason: "Select candidates to clear decision." };
  // allow clearing any decided candidate; no-op if already undecided
  const anyDecided = sel.some((c) => c.decision !== null);
  if (!anyDecided) return { ok: false, reason: "All selected candidates are already undecided." };
  return { ok: true };
}

function bulkClearBlockedHover(): string {
  const chk = canBulkClearDecision();
  return chk.ok ? "Clear decision → NEEDS_DECISION (decision=null). Note cleared too." : (chk.reason ?? "Blocked");
}

// micro-follow: summary chips (counts) + one-click filters (product-only)
function _decisionKey(c: CandidateRow): "NEEDS_DECISION" | "GREEN" | "YELLOW" | "RED" | "OTHER" {
  const d = (c.decision ?? null) as any;
  if (d === null) return "NEEDS_DECISION";
  if (d === "GREEN" || d === "YELLOW" || d === "RED") return d;
  return "OTHER";
}
function _statusKey(c: CandidateRow): "PROPOSED" | "ACCEPTED" | "REJECTED" | "OTHER" {
  const s = (c.status ?? null) as any;
  if (s === "PROPOSED" || s === "ACCEPTED" || s === "REJECTED") return s;
  return "OTHER";
}

const summary = computed(() => {
  const decisionCounts: Record<string, number> = {
    NEEDS_DECISION: 0,
    GREEN: 0,
    YELLOW: 0,
    RED: 0,
    OTHER: 0,
  };
  const statusCounts: Record<string, number> = {
    PROPOSED: 0,
    ACCEPTED: 0,
    REJECTED: 0,
    OTHER: 0,
  };
  for (const c of candidates.value) {
    decisionCounts[_decisionKey(c)] = (decisionCounts[_decisionKey(c)] || 0) + 1;
    statusCounts[_statusKey(c)] = (statusCounts[_statusKey(c)] || 0) + 1;
  }
  return { decisionCounts, statusCounts, total: candidates.value.length };
});

function setDecisionFilter(v: string) {
  decisionFilter.value = v as DecisionFilter;
  schedulePrefsSave();
}
function setStatusFilter(v: string) {
  statusFilter.value = v as StatusFilter;
  schedulePrefsSave();
}

function chipClass(active: boolean, kind: "neutral" | "good" | "warn" | "bad" | "muted" = "neutral") {
  return {
    chip: true,
    active,
    neutral: kind === "neutral",
    good: kind === "good",
    warn: kind === "warn",
    bad: kind === "bad",
    muted: kind === "muted",
  };
}

// -------------------------
// Filtered view (product-only)
// -------------------------
const filteredCandidates = computed(() => {
  const df = decisionFilter.value;
  const sf = statusFilter.value;
  const onlySel = showSelectedOnly.value;
  const sel = selectedIds.value;
  const q = normalize(searchText.value);

  let arr = candidates.value.filter((c) => {
    if (onlySel && !sel.has(c.candidate_id)) return false;

    // decision filter
    if (df === "UNDECIDED") {
      if (c.decision != null) return false;
    } else if (df === "GREEN" || df === "YELLOW" || df === "RED") {
      if (c.decision !== df) return false;
    }

    // status filter
    if (sf !== "ALL") {
      if ((c.status ?? null) !== sf) return false;
    }

    // decided-by filter
    if (filterDecidedBy.value !== "ALL") {
      if ((c.decided_by ?? "") !== filterDecidedBy.value) return false;
    }

    // search
    if (!matchesSearch(c, q)) return false;
    return true;
  });

  // sort
  const sk = sortKey.value;
  arr = [...arr].sort((a, b) => {
    if (sk === "id") return a.candidate_id.localeCompare(b.candidate_id);
    if (sk === "id_desc") return b.candidate_id.localeCompare(a.candidate_id);
    if (sk === "created") return (a.created_at_utc ?? "").localeCompare(b.created_at_utc ?? "");
    if (sk === "created_desc") return (b.created_at_utc ?? "").localeCompare(a.created_at_utc ?? "");
    if (sk === "status") return (a.status ?? "").localeCompare(b.status ?? "");
    if (sk === "decision") return (a.decision ?? "ZZZ").localeCompare(b.decision ?? "ZZZ");
    return 0;
  });

  return arr;
});

const filteredCount = computed(() => filteredCandidates.value.length);

const filteredIds = computed(() => new Set(filteredCandidates.value.map((c) => c.candidate_id)));
const allFilteredSelected = computed(() => {
  const f = filteredIds.value;
  if (f.size === 0) return false;
  for (const id of f) if (!selectedIds.value.has(id)) return false;
  return true;
});

// Selection helpers
function idxById(id: string): number {
  return filteredCandidates.value.findIndex((c) => c.candidate_id === id);
}
function setSelected(id: string, on: boolean) {
  const next = new Set(selectedIds.value);
  if (on) next.add(id);
  else next.delete(id);
  selectedIds.value = next;
}
function toggleSelected(id: string) {
  setSelected(id, !selectedIds.value.has(id));
}
function selectRange(fromId: string, toId: string) {
  const a = idxById(fromId);
  const b = idxById(toId);
  if (a < 0 || b < 0) return;
  const lo = Math.min(a, b);
  const hi = Math.max(a, b);
  const next = new Set(selectedIds.value);
  for (let i = lo; i <= hi; i++) next.add(filteredCandidates.value[i].candidate_id);
  selectedIds.value = next;
}
function selectAllFiltered() {
  const next = new Set(selectedIds.value);
  for (const id of filteredIds.value) next.add(id);
  selectedIds.value = next;
}
function clearAllFiltered() {
  const f = filteredIds.value;
  const next = new Set(selectedIds.value);
  for (const id of f) next.delete(id);
  selectedIds.value = next;
}
function invertSelectionFiltered() {
  const f = filteredIds.value;
  const next = new Set(selectedIds.value);
  for (const id of f) {
    if (next.has(id)) next.delete(id);
    else next.add(id);
  }
  selectedIds.value = next;
}

function quickUndecided() {
  decisionFilter.value = "UNDECIDED";
}

function clearFilters() {
  decisionFilter.value = "ALL";
  statusFilter.value = "ALL";
  showSelectedOnly.value = false;
  searchText.value = "";
}

// -----------------------------------------------------------------------------
// micro-follow: bulk decision v2 - apply + undo (with progress + history panel)
// -----------------------------------------------------------------------------
async function applyBulkDecision() {
  if (bulkApplying.value) return;
  const sel = _selectedCandidates();
  if (!sel.length) {
    showToast("No candidates selected", "err");
    return;
  }
  if (bulkDecision.value == null) {
    showToast("Choose GREEN/YELLOW/RED", "err");
    return;
  }

  bulkApplying.value = true;
  bulkProgress.value = { total: sel.length, done: 0, fail: 0 };

  const record: BulkActionRecord = {
    id: _mkId("bulk_decision"),
    at_utc: _utcNowIso(),
    decision: bulkDecision.value,
    note: bulkNote.value.trim() ? bulkNote.value.trim() : null,
    selected_count: sel.length,
    applied_count: 0,
    failed_count: 0,
    items: [],
  };

  try {
    for (const c of sel) {
      const prev_decision = (c.decision ?? null) as RiskDecision | null;
      const prev_note = (c.decision_note ?? null) as string | null;
      const next_decision = bulkDecision.value;
      const next_note = record.note;

      // store undo snapshot *before* mutating
      record.items.push({
        candidate_id: c.candidate_id,
        prev_decision,
        prev_note,
        next_decision,
        next_note,
      });

      try {
        const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
          decision: next_decision,
          note: next_note,
        } as any);
        _updateCandidateFromDecisionResponse(c.candidate_id, res);
        record.applied_count += 1;
      } catch (e) {
        record.failed_count += 1;
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done,
          fail: bulkProgress.value!.fail + 1,
        };
      } finally {
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done + 1,
          fail: bulkProgress.value!.fail,
        };
      }
    }

    // push record to history (cap to 10)
    bulkHistory.value = [record, ...bulkHistory.value].slice(0, 10);
    showToast(
      record.failed_count
        ? `Bulk set done (${record.applied_count} ok, ${record.failed_count} failed)`
        : `Bulk set decision: ${record.decision}`,
      record.failed_count ? "err" : "ok"
    );
  } finally {
    bulkApplying.value = false;
    // keep progress visible briefly; user can also open history
    window.setTimeout(() => (bulkProgress.value = null), 900);
  }
}

async function undoLastBulkAction() {
  if (bulkApplying.value) return;
  const rec = bulkHistory.value[0];
  if (!rec) {
    showToast("No bulk history to undo", "err");
    return;
  }

  bulkApplying.value = true;
  bulkProgress.value = { total: rec.items.length, done: 0, fail: 0 };

  try {
    for (const it of rec.items) {
      try {
        const res = await decideManufacturingCandidate(props.runId, it.candidate_id, {
          decision: it.prev_decision,
          note: it.prev_note,
        } as any);
        _updateCandidateFromDecisionResponse(it.candidate_id, res);
      } catch (e) {
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done,
          fail: bulkProgress.value!.fail + 1,
        };
      } finally {
        bulkProgress.value = {
          total: bulkProgress.value!.total,
          done: bulkProgress.value!.done + 1,
          fail: bulkProgress.value!.fail,
        };
      }
    }

    // remove the record we just undid
    bulkHistory.value = bulkHistory.value.slice(1);
    showToast("Undid last bulk decision");
  } finally {
    bulkApplying.value = false;
    window.setTimeout(() => (bulkProgress.value = null), 900);
  }
}

function toggleOne(id: string, ev?: MouseEvent) {
  if (ev?.shiftKey && lastClickedId.value && lastClickedId.value !== id) {
    selectRange(lastClickedId.value, id);
  } else {
    toggleSelected(id);
  }
  lastClickedId.value = id;
}

function toggleAllFiltered() {
  if (allFilteredSelected.value) clearAllFiltered();
  else selectAllFiltered();
}

function utcNowIso() {
  return new Date().toISOString();
}

async function bulkSetDecision(decision: RiskLevel) {
  if (!props.runId) return;
  undoError.value = null;
  saveError.value = null;

  const rows = selectedRows.value;
  if (rows.length === 0) {
    undoError.value = "Select at least one candidate first.";
    return;
  }

  // Snapshot previous states (for undo)
  const prev: UndoItem["prev"] = {};
  for (const r of rows) {
    prev[r.candidate_id] = {
      decision: (r.decision ?? null) as any,
      decision_note: (r.decision_note ?? null) as any,
    };
  }

  saving.value = true;
  try {
    // Sequential, deterministic updates (keeps audit clean and avoids request bursts)
    for (const r of rows) {
      const res = await decideManufacturingCandidate(props.runId, r.candidate_id, {
        decision,
        note: r.decision_note ?? null,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      const idx = candidates.value.findIndex((x) => x.candidate_id === r.candidate_id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? decision) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? candidates.value[idx].decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
          decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }

    // push undo record
    undoStack.value.unshift({
      ts_utc: utcNowIso(),
      run_id: props.runId,
      label: `Bulk set ${rows.length} → ${decision}`,
      applied_decision: decision,
      candidate_ids: rows.map((x) => x.candidate_id),
      prev,
    });
    // keep stack small/high-signal
    if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20);
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function bulkClearDecision() {
  const chk = canBulkClearDecision();
  if (!chk.ok) return;

  saving.value = true;
  saveError.value = null;

  const sel = selectedRows.value;
  const nowIso = utcNowIso();

  // Snapshot "before" for undo per candidate that is changing
  const changed = sel.filter((c) => c.decision !== null);
  const prev: UndoItem["prev"] = {};
  for (const c of changed) {
    prev[c.candidate_id] = {
      decision: (c.decision ?? null) as any,
      decision_note: (c.decision_note ?? null) as any,
    };
  }

  try {
    for (const c of changed) {
      const res = await decideManufacturingCandidate(props.runId, c.candidate_id, {
        decision: null,
        note: null,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      // optimistic local update
      const idx = candidates.value.findIndex((x) => x.candidate_id === c.candidate_id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? null) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? null,
          decided_by: res.decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }

    // push undo record
    undoStack.value.unshift({
      ts_utc: nowIso,
      run_id: props.runId,
      label: `Bulk clear ${changed.length} → NEEDS_DECISION`,
      applied_decision: null as any,
      candidate_ids: changed.map((x) => x.candidate_id),
      prev,
    });
    if (undoStack.value.length > 20) undoStack.value = undoStack.value.slice(0, 20);
  } catch (e: any) {
    saveError.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

async function undoLast() {
  if (!props.runId) return;
  if (undoStack.value.length === 0) return;
  undoBusy.value = true;
  undoError.value = null;

  const item = undoStack.value[0];
  try {
    for (const id of item.candidate_ids) {
      const snap = item.prev[id];
      if (!snap) continue;
      const res = await decideManufacturingCandidate(props.runId, id, {
        decision: snap.decision, // may be null (back to NEEDS_DECISION)
        note: snap.decision_note,
        decided_by: null,
      });
      requestId.value = res.requestId ?? requestId.value;

      const idx = candidates.value.findIndex((x) => x.candidate_id === id);
      if (idx >= 0) {
        candidates.value[idx] = {
          ...candidates.value[idx],
          decision: (res.decision ?? snap.decision ?? null) as any,
          status: (res.status ?? candidates.value[idx].status ?? null) as any,
          decision_note: res.decision_note ?? snap.decision_note ?? null,
          decided_at_utc: res.decided_at_utc ?? candidates.value[idx].decided_at_utc ?? null,
          decided_by: res.decided_by ?? candidates.value[idx].decided_by ?? null,
          decision_history: res.decision_history ?? candidates.value[idx].decision_history ?? null,
        };
      }
      await new Promise((rr) => setTimeout(rr, 40));
    }
    // pop after successful undo
    undoStack.value.shift();
  } catch (e: any) {
    undoError.value = e?.message ?? String(e);
  } finally {
    undoBusy.value = false;
  }
}

function undoStackHover(item: UndoItem) {
  const ids = item.candidate_ids.slice(0, 6).join(", ");
  const more = item.candidate_ids.length > 6 ? ` …(+${item.candidate_ids.length - 6})` : "";
  return [
    `When: ${item.ts_utc}`,
    `Run: ${item.run_id}`,
    `Action: ${item.label}`,
    `Candidates: ${ids}${more}`,
    `Undo applies previous decision + note (including null).`,
  ].join("\n");
}

// -------------------------
// Bulk export (GREEN-only)
// -------------------------
const undecidedCount = computed(() => candidates.value.filter((c) => c.decision == null).length);
const greenCandidates = computed(() => candidates.value.filter((c) => c.decision === "GREEN"));

const exportBlockedReason = computed(() => {
  if (candidates.value.length === 0) return "No candidates to export.";
  if (undecidedCount.value > 0) {
    return `Export blocked: ${undecidedCount.value} candidate(s) still NEED DECISION. Decide all candidates before exporting.`;
  }
  if (greenCandidates.value.length === 0) {
    return "Export blocked: there are no GREEN candidates to export.";
  }
  return null;
});

const canExportGreenOnly = computed(() => exportBlockedReason.value == null && !exporting.value);

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  // give the browser a beat before revoking
  setTimeout(() => URL.revokeObjectURL(url), 2500);
}

async function exportGreenOnlyZips() {
  if (!props.runId) return;
  exportError.value = null;

  const reason = exportBlockedReason.value;
  if (reason) {
    exportError.value = reason;
    return;
  }

  exporting.value = true;
  try {
    // Download each GREEN candidate zip. (Product-only: no server-side bundling.)
    for (const c of greenCandidates.value) {
      const res = await downloadManufacturingCandidateZip(props.runId, c.candidate_id);
      requestId.value = res.requestId ?? requestId.value;
      const fname = `rmos_${props.runId}_candidate_${c.candidate_id}_GREEN.zip`;
      downloadBlob(res.blob, fname);
      // small delay to avoid browser throttling
      await new Promise((r) => setTimeout(r, 250));
    }
  } catch (e: any) {
    exportError.value = e?.message ?? String(e);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <section class="rmos-candidates">
    <div class="header">
      <div class="title">
        <h3>Manufacturing Candidates</h3>
        <div class="subtitle muted">
          Decision is <span class="mono">null</span> until operator decides (spine-locked).
        </div>
      </div>
      <div class="meta">
        <span v-if="requestId" class="reqid" title="X-Request-Id">req: {{ requestId }}</span>
        <button class="btn" @click="load" :disabled="loading || exporting">Refresh</button>

        <!-- Bulk export (GREEN-only), blocked if any undecided -->
        <button
          class="btn"
          @click="exportGreenOnlyZips"
          :disabled="!canExportGreenOnly"
          :title="exportBlockedReason ?? 'Download zips for GREEN candidates only'"
        >
          {{ exporting ? "Exporting…" : "Export GREEN zips" }}
        </button>
      </div>
    </div>

    <p v-if="error" class="error">Error: {{ error }}</p>
    <p v-if="saveError" class="error">Save error: {{ saveError }}</p>
    <p v-if="exportError" class="error">Export: {{ exportError }}</p>
    <p v-if="undoError" class="error">Undo: {{ undoError }}</p>

    <p v-if="loading" class="muted">Loading candidates…</p>
    <p v-else-if="candidates.length === 0" class="muted">No candidates yet.</p>

    <div v-else class="table" :class="{ compact }">
      <!-- Filters -->
      <div class="filters">
        <div class="filters-left">
          <!-- micro-follow: quick chips -->
          <div class="chipsRow" v-if="summary.total > 0">
            <div class="chipsGroup">
              <div class="small muted">Decision:</div>
              <button
                type="button"
                :class="chipClass(decisionFilter === 'ALL', 'neutral')"
                @click="setDecisionFilter('ALL')"
                title="Show all decisions"
              >
                All <span class="count">{{ summary.total }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(decisionFilter === 'UNDECIDED', 'muted')"
                @click="setDecisionFilter('UNDECIDED')"
                title="Show candidates that still need an explicit decision"
              >
                Needs decision <span class="count">{{ summary.decisionCounts.NEEDS_DECISION }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(decisionFilter === 'GREEN', 'good')"
                @click="setDecisionFilter('GREEN')"
                title="Show GREEN-only"
              >
                GREEN <span class="count">{{ summary.decisionCounts.GREEN }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(decisionFilter === 'YELLOW', 'warn')"
                @click="setDecisionFilter('YELLOW')"
                title="Show YELLOW-only"
              >
                YELLOW <span class="count">{{ summary.decisionCounts.YELLOW }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(decisionFilter === 'RED', 'bad')"
                @click="setDecisionFilter('RED')"
                title="Show RED-only"
              >
                RED <span class="count">{{ summary.decisionCounts.RED }}</span>
              </button>
            </div>

            <div class="chipsGroup">
              <div class="small muted">Status:</div>
              <button
                type="button"
                :class="chipClass(statusFilter === 'ALL', 'neutral')"
                @click="setStatusFilter('ALL')"
                title="Show all statuses"
              >
                All <span class="count">{{ summary.total }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(statusFilter === 'PROPOSED', 'muted')"
                @click="setStatusFilter('PROPOSED')"
                title="Show PROPOSED-only"
              >
                PROPOSED <span class="count">{{ summary.statusCounts.PROPOSED }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(statusFilter === 'ACCEPTED', 'good')"
                @click="setStatusFilter('ACCEPTED')"
                title="Show ACCEPTED-only"
              >
                ACCEPTED <span class="count">{{ summary.statusCounts.ACCEPTED }}</span>
              </button>
              <button
                type="button"
                :class="chipClass(statusFilter === 'REJECTED', 'bad')"
                @click="setStatusFilter('REJECTED')"
                title="Show REJECTED-only"
              >
                REJECTED <span class="count">{{ summary.statusCounts.REJECTED }}</span>
              </button>
            </div>
          </div>

          <div class="field">
            <label class="muted">Decision</label>
            <select v-model="decisionFilter" :disabled="saving || exporting || undoBusy">
              <option value="ALL">All</option>
              <option value="UNDECIDED">Undecided</option>
              <option value="GREEN">GREEN</option>
              <option value="YELLOW">YELLOW</option>
              <option value="RED">RED</option>
            </select>
          </div>

          <div class="field">
            <label class="muted">Status</label>
            <select v-model="statusFilter" :disabled="saving || exporting || undoBusy">
              <option value="ALL">All</option>
              <option value="PROPOSED">PROPOSED</option>
              <option value="ACCEPTED">ACCEPTED</option>
              <option value="REJECTED">REJECTED</option>
            </select>
          </div>

          <div class="field">
            <label class="muted">Decided by</label>
            <select v-model="filterDecidedBy" :disabled="saving || exporting || undoBusy" title="Filter by operator identity">
              <option value="ALL">All</option>
              <option v-for="op in decidedByOptions" :key="op" :value="op">{{ op }}</option>
            </select>
          </div>

          <div class="field grow">
            <label class="muted">Search</label>
            <input
              v-model="searchText"
              type="text"
              placeholder="candidate id, advisory id, note, decided_by…"
              :disabled="saving || exporting || undoBusy"
            />
          </div>

          <div class="field">
            <label class="muted">Sort</label>
            <select v-model="sortKey" :disabled="saving || exporting || undoBusy">
              <option value="id">ID ↑</option>
              <option value="id_desc">ID ↓</option>
              <option value="created">Created ↑</option>
              <option value="created_desc">Created ↓</option>
              <option value="status">Status</option>
              <option value="decision">Decision</option>
            </select>
          </div>
        </div>

        <div class="filters-right">
          <button class="btn ghost" @click="selectAllFiltered" :disabled="saving || exporting || undoBusy || filteredCount === 0" title="Select all shown rows">
            Select shown
          </button>
          <button class="btn ghost" @click="clearAllFiltered" :disabled="saving || exporting || undoBusy || filteredCount === 0" title="Clear selection for shown rows">
            Clear shown
          </button>
          <button class="btn ghost" @click="invertSelectionFiltered" :disabled="saving || exporting || undoBusy || filteredCount === 0" title="Invert selection (shown rows)">
            Invert
          </button>

          <label class="check">
            <input type="checkbox" v-model="showSelectedOnly" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" />
            <span class="muted">Selected only</span>
          </label>

          <button class="btn ghost" @click="quickUndecided" :disabled="saving || exporting || undoBusy" title="Jump to undecided candidates">
            Undecided-only
          </button>
          <button class="btn ghost" @click="clearFilters" :disabled="saving || exporting || undoBusy" title="Clear all filters">
            Clear filters
          </button>

          <div class="muted small">
            Showing <strong>{{ filteredCount }}</strong> / {{ candidates.length }}
          </div>
          <label class="check" :title="compact ? 'Compact rows (more visible)' : 'Comfortable rows (more spacing)'">
            <input type="checkbox" v-model="compact" />
            <span class="muted">{{ compact ? 'Compact' : 'Comfortable' }}</span>
          </label>
          <div class="small muted" style="margin-top:4px;">
            <span class="kbdhint" :title="_hotkeyHelp()">
              Hotkeys: g/y/r · u · b · e · a · c · i · x · h · esc
            </span>
          </div>
          <div style="margin-top:8px;">
            <button class="btn small" @click="resetViewPrefs" title="Reset filters, density, and sort (persisted)">
              Reset view
            </button>
          </div>
        </div>
      </div>

      <div class="row head">
        <div class="sel">
          <input
            type="checkbox"
            :checked="allFilteredSelected"
            @change="toggleAllFiltered"
            :disabled="saving || exporting || undoBusy || filteredCount === 0"
            title="Toggle select all shown"
          />
        </div>
        <div>Candidate</div>
        <div>Advisory</div>
        <div>Decision</div>
        <div>History</div>
        <div>Status</div>
        <div class="note">Decision Note</div>
        <div class="copyCol">Copy</div>
        <div class="actions">Actions</div>
      </div>

      <!-- Bulk decision bar -->
      <div class="bulkbar" v-if="candidates.length > 0">
        <div class="bulk-left">
          <span class="muted">
            Selected: <strong>{{ selectedIds.size }}</strong>
          </span>
          <span class="muted" v-if="selectedIds.size === 0"> (select rows to bulk-set decision)</span>
        </div>
        <div class="bulk-actions">
          <button class="btn" @click="bulkSetDecision('GREEN')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to GREEN">
            Bulk GREEN
          </button>
          <button class="btn" @click="bulkSetDecision('YELLOW')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to YELLOW">
            Bulk YELLOW
          </button>
          <button class="btn danger" @click="bulkSetDecision('RED')" :disabled="saving || exporting || undoBusy || selectedIds.size === 0" title="Set selected to RED">
            Bulk RED
          </button>
          <button
            class="btn ghost"
            @click="bulkClearDecision"
            :disabled="saving || exporting || undoBusy || !canBulkClearDecision().ok"
            :title="bulkClearBlockedHover()"
          >
            Clear decision
          </button>
          <button
            class="btn ghost"
            @click="undoLast"
            :disabled="undoBusy || saving || exporting || undoStack.length === 0"
            :title="undoStack.length ? undoStackHover(undoStack[0]) : 'Nothing to undo'"
          >
            {{ undoBusy ? "Undoing…" : "Undo last" }}
          </button>
        </div>
      </div>

      <!-- Undo history display -->
      <div class="undolist" v-if="undoStack.length > 0">
        <div class="undotitle muted">Undo history (most recent first)</div>
        <div class="undoitem" v-for="(u, idx) in undoStack.slice(0, 5)" :key="u.ts_utc + ':' + idx" :title="undoStackHover(u)">
          <span class="mono">{{ u.ts_utc }}</span>
          <span>—</span>
          <span>{{ u.label }}</span>
        </div>
      </div>

      <!-- Bulk decision v2 controls -->
      <div class="bulkbar2" v-if="selectedIds.size > 0">
        <div class="bulk-row">
          <label class="muted">Bulk Decision:</label>
          <select v-model="bulkDecision" class="selectSmall" :disabled="bulkApplying || saving || exporting">
            <option value="">— pick —</option>
            <option value="GREEN">GREEN</option>
            <option value="YELLOW">YELLOW</option>
            <option value="RED">RED</option>
          </select>
          <input
            v-model="bulkNote"
            class="inputSmall"
            placeholder="Shared note (optional)"
            :disabled="bulkApplying || saving || exporting"
          />
          <button
            class="btn small"
            :disabled="bulkApplying || saving || exporting || !bulkDecision"
            @click="applyBulkDecision"
          >
            {{ bulkApplying ? `Applying… (${bulkProgress.done}/${bulkProgress.total})` : 'Apply' }}
          </button>
          <label class="inlineCheck" title="When clearing decisions, also clear decision notes">
            <input type="checkbox" v-model="bulkClearNoteToo" :disabled="bulkApplying" />
            clear note too
          </label>
          <button
            class="btn small"
            :disabled="bulkApplying || saving || exporting || selectedIds.size === 0"
            @click="clearBulkDecision"
            :title="selectedIds.size ? 'Clear decision (set to null) for selected candidates (hotkey: b)' : 'Select one or more candidates first'"
          >
            Clear decision
          </button>
          <button
            class="btn ghost small"
            :disabled="bulkApplying || saving || exporting || bulkHistory.length === 0"
            @click="undoLastBulkAction"
            title="Undo last bulk action"
          >
            Undo
          </button>
          <button
            class="btn ghost small"
            @click="showBulkHistory = !showBulkHistory"
            :title="showBulkHistory ? 'Hide bulk history' : 'Show bulk history (hotkey: h)'"
          >
            {{ showBulkHistory ? 'Hide history' : `History (${bulkHistory.length})` }}
          </button>
        </div>
      </div>

      <!-- Bulk history panel -->
      <div class="bulkHistory" v-if="showBulkHistory && bulkHistory.length > 0">
        <div class="bulkHistoryHeader muted">
          Bulk history (newest first)
        </div>
        <div class="bulkHistoryList">
          <div
            v-for="rec in bulkHistory"
            :key="rec.id"
            class="bulkHistoryRow"
          >
            <span class="mono small">{{ rec.ts_utc }}</span>
            <span class="badge" :class="'b' + rec.decision">{{ rec.decision }}</span>
            <span>{{ rec.count }} items</span>
            <span class="muted" v-if="rec.note">— {{ rec.note }}</span>
          </div>
        </div>
      </div>

      <div
        v-for="c in filteredCandidates"
        :key="c.candidate_id"
        class="row clickable"
        :title="auditHover(c)"
        @click="toggleOne(c.candidate_id, $event)"
      >
        <div class="sel">
          <input
            type="checkbox"
            :checked="selectedIds.has(c.candidate_id)"
            @click.stop="toggleOne(c.candidate_id, $event)"
            :disabled="saving || exporting || undoBusy"
            :title="selectedIds.has(c.candidate_id) ? 'Selected' : 'Select'"
          />
        </div>
        <div class="mono">{{ c.candidate_id }}</div>
        <div class="mono">{{ c.advisory_id ?? "—" }}</div>

        <div class="decision-cell">
          <span class="badge" :data-badge="decisionBadge(c.decision)">
            {{ decisionBadge(c.decision) }}
          </span>
          <span
            v-if="c.decision_history && c.decision_history.length > 0"
            class="history-count"
            :title="`${c.decision_history.length} history entries`"
            @click.stop="openDecisionHistory(c.candidate_id)"
          >
            ({{ c.decision_history.length }})
          </span>
        </div>

        <div class="history">
          <button class="btn ghost smallbtn" @click.stop="openDecisionHistory(c.candidate_id)" :disabled="saving || exporting || undoBusy">
            {{ openHistoryFor === c.candidate_id ? "Hide" : "View" }}
          </button>
          <div v-if="openHistoryFor === c.candidate_id" class="popover">
            <CandidateDecisionHistoryPopover
              :items="c.decision_history ?? null"
              :currentDecision="c.decision ?? null"
              :currentNote="c.decision_note ?? null"
              :currentBy="c.decided_by ?? null"
              :currentAt="c.decided_at_utc ?? null"
            />
          </div>
        </div>

        <div class="muted">{{ statusText(c) }}</div>

        <div class="note">
          <div v-if="editingId === c.candidate_id" class="editor">
            <textarea v-model="editValue" rows="2" />
            <div class="editor-actions">
              <button class="btn" @click="saveEdit(c)" :disabled="saving || exporting">Save</button>
              <button class="btn ghost" @click="cancelEdit" :disabled="saving || exporting">Cancel</button>
            </div>
          </div>
          <div v-else class="note-display">
            <span class="muted" v-if="!c.decision_note">—</span>
            <span v-else>{{ notePreview(c.decision_note) }}</span>
          </div>
        </div>

        <div class="copyCol">
          <button class="btn ghost smallbtn" @click="copyText('candidate_id', c.candidate_id)" title="Copy candidate_id">
            📋 candidate_id
          </button>
          <button class="btn ghost smallbtn" @click="copyText('advisory_id', c.advisory_id)" title="Copy advisory_id">
            📋 advisory_id
          </button>
        </div>

        <div class="actions">
          <button class="btn" @click="decide(c, 'GREEN')" :disabled="saving || exporting">GREEN</button>
          <button class="btn" @click="decide(c, 'YELLOW')" :disabled="saving || exporting">YELLOW</button>
          <button class="btn danger" @click="decide(c, 'RED')" :disabled="saving || exporting">RED</button>

          <button
            class="btn ghost"
            @click="startEdit(c)"
            :disabled="saving || exporting || c.decision == null"
            :title="c.decision == null ? 'Decide first to enable note editing' : 'Edit decision note'"
          >
            Edit Note
          </button>
        </div>
      </div>
    </div>

    <!-- Export policy explainers (visible, not just hover) -->
    <div class="policy muted" v-if="candidates.length > 0">
      <div><strong>Export policy:</strong></div>
      <ul>
        <li>Export is blocked while any candidate is <span class="mono">NEEDS_DECISION</span>.</li>
        <li>Export downloads zips for <strong>GREEN</strong> candidates only.</li>
        <li>Hover the export button to see the exact block reason.</li>
      </ul>
    </div>

    <!-- Copy toast -->
    <div class="toast" v-if="toast">{{ toast }}</div>
  </section>
</template>

<style scoped>
.rmos-candidates { display: flex; flex-direction: column; gap: 10px; }
.header { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.title { display: flex; flex-direction: column; gap: 4px; }
.subtitle { font-size: 12px; }
.meta { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.reqid { font-size: 12px; opacity: 0.75; }
.error { color: #b00020; }
.muted { opacity: 0.75; }
.small { font-size: 12px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }

.table { display: grid; gap: 6px; }
.row {
  display: grid;
  grid-template-columns: 34px 140px 1fr 140px 120px 140px 2fr 190px 360px;
  gap: 10px;
  align-items: start;
  padding: 8px;
  border: 1px solid rgba(0,0,0,0.12);
  border-radius: 10px;
  position: relative;
  background: white;
}
.row.head {
  font-weight: 600;
  background: rgba(0,0,0,0.04);
  position: sticky;
  top: 0;
  z-index: 3;
  border-radius: 10px;
  backdrop-filter: blur(6px);
}
.row.clickable { cursor: pointer; }

/* micro-follow: compact density */
.table.compact .row { padding: 6px; gap: 8px; }
.table.compact .mono { font-size: 11px; }
.table.compact .btn { padding: 4px 8px; }
.table.compact .copyCol { gap: 4px; }

/* copyCol layout */
.copyCol { display: flex; flex-direction: column; gap: 6px; }

.kbdhint {
  cursor: help;
  border: 1px solid rgba(0,0,0,0.15);
  padding: 2px 8px;
  border-radius: 999px;
  display: inline-block;
}
.sel { display: flex; align-items: center; justify-content: center; padding-top: 2px; }

.filters { display: flex; gap: 10px; align-items: end; justify-content: space-between; padding: 8px; border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; }
.filters-left { display: flex; gap: 10px; align-items: end; flex-wrap: wrap; flex: 1; }
.filters-right { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; justify-content: flex-end; }
.field { display: flex; flex-direction: column; gap: 4px; }
.field.grow { min-width: 280px; flex: 1; }
.field label { font-size: 12px; }
.field select, .field input { padding: 6px 10px; border: 1px solid rgba(0,0,0,0.16); border-radius: 10px; background: white; }
.check { display: inline-flex; gap: 6px; align-items: center; }

.actions { display: flex; flex-wrap: wrap; gap: 6px; }
.btn { padding: 6px 10px; border: 1px solid rgba(0,0,0,0.16); border-radius: 10px; background: white; cursor: pointer; }
.btn.ghost { background: transparent; }
.btn.danger { border-color: rgba(176,0,32,0.35); }
.smallbtn { padding: 4px 8px; font-size: 12px; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.badge { display: inline-flex; align-items: center; justify-content: center; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid rgba(0,0,0,0.14); }
.badge[data-badge="NEEDS_DECISION"] { opacity: 0.75; }

.note textarea { width: 100%; resize: vertical; padding: 6px; border-radius: 10px; border: 1px solid rgba(0,0,0,0.16); }
.editor-actions { display: flex; gap: 6px; margin-top: 6px; }

.bulkbar { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 8px; border: 1px dashed rgba(0,0,0,0.18); border-radius: 10px; }
.bulk-actions { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
.undolist { display: grid; gap: 4px; padding: 8px; border: 1px solid rgba(0,0,0,0.10); border-radius: 10px; }
.undotitle { font-size: 12px; }
.undoitem { display: flex; gap: 8px; align-items: center; font-size: 12px; }

.policy ul { margin: 6px 0 0 18px; }

.history { position: relative; }
.popover { position: absolute; z-index: 50; top: 30px; left: 0; }

/* toast (copy feedback) */
.toast {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: #323232;
  color: #fff;
  padding: 10px 20px;
  border-radius: 10px;
  z-index: 100;
  font-size: 14px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.25);
}

.chipsRow { display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px; }
.chipsGroup { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.chip {
  border: 1px solid rgba(0,0,0,0.14);
  background: white;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.chip .count {
  font-variant-numeric: tabular-nums;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.10);
  background: rgba(0,0,0,0.03);
}
.chip.active { border-color: rgba(0,0,0,0.28); box-shadow: 0 6px 14px rgba(0,0,0,0.06); }
.chip.good.active { border-color: #22c55e; }
.chip.warn.active { border-color: #eab308; }
.chip.bad.active { border-color: #ef4444; }
.chip.muted.active { border-color: #6b7280; }
.chip:hover { border-color: rgba(0,0,0,0.22); }

/* Decision cell with history count badge */
.decision-cell { display: flex; align-items: center; gap: 6px; }
.history-count {
  font-size: 11px;
  color: #6b7280;
  cursor: pointer;
}
.history-count:hover { color: #374151; text-decoration: underline; }

/* Bulk decision v2 */
.bulkbar2 { padding: 10px 14px; background: #f0f7ff; border-radius: 8px; margin-bottom: 10px; }
.bulk-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.selectSmall { padding: 4px 8px; font-size: 13px; border-radius: 4px; border: 1px solid #ccc; }
.inputSmall { padding: 4px 8px; font-size: 13px; border-radius: 4px; border: 1px solid #ccc; min-width: 180px; }
.inlineCheck {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: rgba(0,0,0,0.66);
  user-select: none;
}

/* Bulk history panel */
.bulkHistory { background: #fafafa; border: 1px solid #e5e5e5; border-radius: 8px; padding: 10px 14px; margin-bottom: 12px; }
.bulkHistoryHeader { font-weight: 600; margin-bottom: 8px; }
.bulkHistoryList { display: flex; flex-direction: column; gap: 6px; max-height: 200px; overflow-y: auto; }
.bulkHistoryRow { display: flex; align-items: center; gap: 10px; font-size: 13px; }
.badge.bGREEN { background: #dcfce7; color: #166534; }
.badge.bYELLOW { background: #fef9c3; color: #854d0e; }
.badge.bRED { background: #fee2e2; color: #991b1b; }
</style>
