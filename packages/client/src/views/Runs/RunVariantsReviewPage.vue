<script setup lang="ts">
/**
 * RunVariantsReviewPage.vue
 *
 * Product surface for variant review workflow.
 * Uses /api/rmos/runs/{run_id}/advisory/variants endpoint.
 *
 * Features:
 * - Status badges (NEW/REVIEWED/PROMOTED/REJECTED) with risk dot
 * - Filter bar (status, needs-attention, sort)
 * - Variant list with selection
 * - Compare mode for SVG diffs
 * - Promotion + notes + lineage panels
 * - Bulk selection + bulk reject
 *
 * H8.3 Migration: Uses canonical SDK with requestId correlation.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import VariantStatusBadge from "@/components/rmos/VariantStatusBadge.vue";
import RejectVariantButton from "@/components/rmos/RejectVariantButton.vue";
import UndoRejectButton from "@/components/rmos/UndoRejectButton.vue";
import BulkRejectModal from "@/components/rmos/BulkRejectModal.vue";
import BulkPromoteModal from "@/components/rmos/BulkPromoteModal.vue";
import {
  listAdvisoryVariants,
  type AdvisoryVariantSummary,
  type VariantStatus,
  type RiskLevel,
} from "@/sdk/rmos/runs";

// Optional: keep your existing components if present
import VariantNotes from "@/components/rmos/VariantNotes.vue";
import PromoteToManufacturingButton from "@/components/rmos/PromoteToManufacturingButton.vue";
import PromptLineageViewer from "@/components/rmos/PromptLineageViewer.vue";
import SvgPathDiffViewer from "@/components/rmos/SvgPathDiffViewer.vue";
import ManufacturingCandidateList from "@/components/rmos/ManufacturingCandidateList.vue";

const route = useRoute();

const runId = computed(() => String(route.params.run_id ?? route.params.id ?? ""));

// -----------------------------------------------------------------------------
// Operator identity for "My decisions" filter (passed to ManufacturingCandidateList)
// Replace with actual auth/store identity when available, e.g.:
//   return useAuthStore().user?.id ?? null
// -----------------------------------------------------------------------------
const currentOperator = computed<string | null>(() => null);

// Filters
const statusFilter = ref<"ALL" | VariantStatus>("ALL");
const riskFilter = ref<"ALL" | "NEEDS_ATTENTION">("ALL");
const sortBy = ref<"CREATED_DESC" | "RATING_DESC" | "RISK_DESC">("CREATED_DESC");

// Data
const loading = ref(false);
const error = ref<string | null>(null);
const variants = ref<AdvisoryVariantSummary[]>([]);

const selected = ref<string | null>(null);
const compareLeft = ref<string | null>(null);
const compareRight = ref<string | null>(null);

// Bulk selection state
const selectedIds = ref<Set<string>>(new Set());
const bulkBusy = ref(false);
const bulkRejectOpen = ref(false);
const bulkPromoteOpen = ref(false);

function toggleSelected(id: string) {
  const s = new Set(selectedIds.value);
  if (s.has(id)) s.delete(id);
  else s.add(id);
  selectedIds.value = s;
}

function clearSelection() {
  selectedIds.value = new Set();
}

function selectAll() {
  selectedIds.value = new Set(filteredSorted.value.map((v) => v.advisory_id));
}

const selectedNonRejectedIds = computed(() => {
  const s = selectedIds.value;
  return filteredSorted.value
    .filter((v) => s.has(v.advisory_id) && deriveStatus(v) !== "REJECTED")
    .map((v) => v.advisory_id);
});

const selectedPromotableIds = computed(() => {
  const s = selectedIds.value;
  return filteredSorted.value
    .filter((v) => {
      const status = deriveStatus(v);
      return s.has(v.advisory_id) && status !== "REJECTED" && status !== "PROMOTED";
    })
    .map((v) => v.advisory_id);
});

// Risk level map for bulk promote modal
type Risk = "GREEN" | "YELLOW" | "RED" | "UNKNOWN" | "ERROR";
const riskById = computed<Record<string, Risk>>(() => {
  const out: Record<string, Risk> = {};
  for (const v of variants.value) {
    out[v.advisory_id] = ((v.risk_level ?? "UNKNOWN").toUpperCase() as Risk);
  }
  return out;
});

const apiBase = "/api";

function deriveStatus(v: AdvisoryVariantSummary): VariantStatus {
  // Prefer server-derived
  if (v.status) return v.status;

  // Derive from known fields if backend does not provide status yet
  if (v.promoted_candidate_id) return "PROMOTED";
  if (v.rejected) return "REJECTED";
  if ((v.rating ?? null) !== null || (v.notes ?? null)) return "REVIEWED";
  return "NEW";
}

function riskRank(r: RiskLevel | null | undefined): number {
  const x = (r ?? "UNKNOWN").toUpperCase() as RiskLevel;
  if (x === "RED") return 3;
  if (x === "YELLOW") return 2;
  if (x === "GREEN") return 1;
  return 0; // UNKNOWN/ERROR etc
}

function parseCreatedAt(v: AdvisoryVariantSummary): number {
  const s = v.created_at_utc ?? "";
  const t = Date.parse(s);
  return Number.isFinite(t) ? t : 0;
}

async function load() {
  if (!runId.value) return;
  loading.value = true;
  error.value = null;
  try {
    // H8.3 SDK returns { items, count, requestId }
    const { items } = await listAdvisoryVariants(runId.value);
    variants.value = items ?? [];

    if (!selected.value && variants.value.length) {
      selected.value = variants.value[0].advisory_id;
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
    variants.value = [];
    selected.value = null;
  } finally {
    loading.value = false;
  }
}

function pickCompare(id: string) {
  if (!compareLeft.value) {
    compareLeft.value = id;
    return;
  }
  if (!compareRight.value && compareLeft.value !== id) {
    compareRight.value = id;
    return;
  }
  if (compareLeft.value === id) compareLeft.value = null;
  if (compareRight.value === id) compareRight.value = null;
}

const compareReady = computed(() => !!compareLeft.value && !!compareRight.value);

const filteredSorted = computed(() => {
  let list = variants.value.slice();

  // Status filter
  if (statusFilter.value !== "ALL") {
    list = list.filter((v) => deriveStatus(v) === statusFilter.value);
  }

  // Risk filter
  if (riskFilter.value === "NEEDS_ATTENTION") {
    list = list.filter((v) => {
      const r = (v.risk_level ?? "UNKNOWN").toUpperCase() as RiskLevel;
      return r === "YELLOW" || r === "RED";
    });
  }

  // Sort
  if (sortBy.value === "RATING_DESC") {
    list.sort((a, b) => (b.rating ?? -1) - (a.rating ?? -1));
  } else if (sortBy.value === "RISK_DESC") {
    list.sort((a, b) => riskRank(b.risk_level as any) - riskRank(a.risk_level as any));
  } else {
    list.sort((a, b) => parseCreatedAt(b) - parseCreatedAt(a));
  }

  return list;
});

function variantHoverTitle(v: AdvisoryVariantSummary): string {
  const status = deriveStatus(v);
  if (status !== "REJECTED") return v.advisory_id;

  const parts: string[] = [];
  parts.push(`REJECTED: ${v.rejection_reason_code ?? "—"}`);
  if (v.rejection_reason_detail) parts.push(`Detail: ${v.rejection_reason_detail}`);
  if (v.rejection_operator_note) parts.push(`Note: ${v.rejection_operator_note}`);
  if (v.rejected_at_utc) parts.push(`At: ${v.rejected_at_utc}`);
  return parts.join("\n");
}

const selectedVariant = computed(() =>
  variants.value.find((v) => v.advisory_id === selected.value) ?? null
);

const selectedIsRejected = computed(() =>
  selectedVariant.value ? deriveStatus(selectedVariant.value) === "REJECTED" : false
);

onMounted(load);
watch(runId, () => {
  selected.value = null;
  compareLeft.value = null;
  compareRight.value = null;
  load();
});
</script>

<template>
  <div class="page">
    <div class="hdr">
      <div>
        <div class="title">Variants & Review</div>
        <div class="subtle">Run: <code>{{ runId }}</code></div>
      </div>

      <div class="toolbar">
        <label class="ctl">
          <span>Status</span>
          <select v-model="statusFilter">
            <option value="ALL">All</option>
            <option value="NEW">New</option>
            <option value="REVIEWED">Reviewed</option>
            <option value="PROMOTED">Promoted</option>
            <option value="REJECTED">Rejected</option>
          </select>
        </label>

        <label class="ctl">
          <span>Risk</span>
          <select v-model="riskFilter">
            <option value="ALL">All</option>
            <option value="NEEDS_ATTENTION">Needs Attention (YELLOW/RED)</option>
          </select>
        </label>

        <label class="ctl">
          <span>Sort</span>
          <select v-model="sortBy">
            <option value="CREATED_DESC">Newest</option>
            <option value="RATING_DESC">Rating (High→Low)</option>
            <option value="RISK_DESC">Risk (RED→GREEN)</option>
          </select>
        </label>

        <button class="btn tiny secondary" @click="load">Refresh</button>
      </div>
    </div>

    <div v-if="loading" class="subtle">Loading variants…</div>
    <div v-else-if="error" class="error">{{ error }}</div>

    <div v-else class="grid">
      <!-- LEFT: Variant list -->
      <div class="panel">
        <div class="panelTitle">Variants ({{ filteredSorted.length }})</div>

        <div v-if="!filteredSorted.length" class="empty">
          <div class="subtle">No variants match current filters.</div>
          <button class="btn tiny" @click="statusFilter = 'ALL'; riskFilter = 'ALL'; sortBy = 'CREATED_DESC'">
            Reset filters
          </button>
        </div>

        <div v-else class="list">
          <!-- Bulk action bar -->
          <div v-if="selectedIds.size > 0" class="bulkBar">
            <div class="bulkInfo">
              <strong>{{ selectedIds.size }}</strong> selected
              <button class="btn tiny secondary" @click="clearSelection">Clear</button>
            </div>
            <div class="bulkActions">
              <button
                class="btn tiny primary"
                :disabled="bulkBusy || !selectedPromotableIds.length"
                @click="bulkPromoteOpen = true"
                title="Promote selected variants to manufacturing candidates"
              >
                Promote Selected ({{ selectedPromotableIds.length }})
              </button>
              <button
                class="btn tiny danger"
                :disabled="bulkBusy || !selectedNonRejectedIds.length"
                @click="bulkRejectOpen = true"
                title="Rejects selected variants (applies one reason code to all)"
              >
                Reject Selected ({{ selectedNonRejectedIds.length }})
              </button>
            </div>
          </div>

          <!-- Select all toggle -->
          <div class="selectAllRow">
            <label class="checkLabel">
              <input
                type="checkbox"
                :checked="selectedIds.size === filteredSorted.length && filteredSorted.length > 0"
                :indeterminate="selectedIds.size > 0 && selectedIds.size < filteredSorted.length"
                @change="selectedIds.size === filteredSorted.length ? clearSelection() : selectAll()"
              />
              <span class="small subtle">Select all ({{ filteredSorted.length }})</span>
            </label>
          </div>

          <button
            v-for="v in filteredSorted"
            :key="v.advisory_id"
            class="row"
            :class="{ on: selected === v.advisory_id, checked: selectedIds.has(v.advisory_id) }"
            :title="variantHoverTitle(v)"
            @click="selected = v.advisory_id"
          >
            <div class="rowCheck" @click.stop>
              <input
                type="checkbox"
                :checked="selectedIds.has(v.advisory_id)"
                @change="toggleSelected(v.advisory_id)"
              />
            </div>
            <div class="rowMain">
              <div class="rowTop">
                <div class="mono">{{ v.advisory_id.slice(0, 12) }}…</div>
                <VariantStatusBadge :status="deriveStatus(v)" :risk="(v.risk_level ?? 'UNKNOWN') as any" />
              </div>

              <div class="rowMeta">
                <span class="subtle small">Rating: {{ v.rating ?? "—" }}</span>
                <span class="sep">•</span>
                <span class="subtle small">Risk: {{ (v.risk_level ?? "UNKNOWN") }}</span>
                <span class="sep">•</span>
                <span class="subtle small">Preview: {{ v.has_preview === false ? "No" : "Yes" }}</span>
              </div>
            </div>

            <div class="rowActions">
              <button class="btn tiny secondary" @click.stop="pickCompare(v.advisory_id)">Pick</button>
            </div>
          </button>
        </div>

        <div class="compareHint subtle small">
          Compare picks:
          <span class="mono">{{ compareLeft ? compareLeft.slice(0, 8) + "…" : "—" }}</span>
          vs
          <span class="mono">{{ compareRight ? compareRight.slice(0, 8) + "…" : "—" }}</span>
        </div>
      </div>

      <!-- RIGHT: Selected variant actions -->
      <div class="panel" v-if="selected">
        <div class="panelTitle">Selected Variant</div>

        <div class="rowActionsInline">
          <PromoteToManufacturingButton :runId="runId" :advisoryId="selected" apiBase="/api/rmos" />
          <RejectVariantButton :runId="runId" :advisoryId="selected" @rejected="load" />
          <UndoRejectButton
            v-if="selectedIsRejected"
            :runId="runId"
            :advisoryId="selected"
            @cleared="load"
          />
        </div>

        <div class="spacer" />
        <VariantNotes :runId="runId" :advisoryId="selected" apiBase="/api/rmos" />

        <div class="spacer" />
        <PromptLineageViewer :runId="runId" :advisoryId="selected" apiBase="/api/rmos" />
      </div>

      <!-- Compare -->
      <div class="panel wide" v-if="compareReady">
        <SvgPathDiffViewer
          :runId="runId"
          :leftAdvisoryId="compareLeft!"
          :rightAdvisoryId="compareRight!"
          apiBase="/api/rmos"
        />
      </div>

      <!-- Manufacturing candidates -->
      <div class="panel wide">
        <ManufacturingCandidateList :runId="runId" :currentOperator="currentOperator" />
      </div>
    </div>

    <!-- Bulk Reject Modal -->
    <BulkRejectModal
      :open="bulkRejectOpen"
      :runId="runId"
      :advisoryIds="selectedNonRejectedIds"
      @close="bulkRejectOpen = false"
      @done="bulkRejectOpen = false; load(); clearSelection();"
    />

    <!-- Bulk Promote Modal -->
    <BulkPromoteModal
      :open="bulkPromoteOpen"
      :runId="runId"
      :advisoryIds="selectedPromotableIds"
      :riskById="riskById"
      :apiBase="apiBase"
      @close="bulkPromoteOpen = false"
      @done="bulkPromoteOpen = false; load(); clearSelection();"
    />
  </div>
</template>

<style scoped>
.page { padding: 12px; }
.hdr { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.title { font-weight: 800; font-size: 18px; }
.toolbar { display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap; }
.ctl { display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
.ctl select { border: 1px solid rgba(0, 0, 0, 0.18); border-radius: 10px; padding: 6px 8px; background: #fff; }

.grid { display: grid; grid-template-columns: 380px 1fr; gap: 12px; align-items: start; }
.panel { border: 1px solid rgba(0, 0, 0, 0.12); border-radius: 12px; padding: 10px; background: white; }
.panel.wide { grid-column: 1 / -1; }
.panelTitle { font-weight: 800; margin-bottom: 8px; }

.list { display: flex; flex-direction: column; gap: 8px; }
.row { display: flex; justify-content: space-between; gap: 8px; text-align: left; padding: 10px; border: 1px solid rgba(0, 0, 0, 0.10); border-radius: 12px; background: white; cursor: pointer; }
.row.on { border-color: rgba(0, 0, 0, 0.35); }
.rowMain { display: flex; flex-direction: column; gap: 6px; width: 100%; }
.rowTop { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
.rowMeta { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sep { opacity: 0.35; }

.rowActions { display: flex; gap: 6px; align-items: center; }
.btn { padding: 8px 10px; border: 1px solid rgba(0, 0, 0, 0.2); border-radius: 10px; background: white; cursor: pointer; }
.btn.tiny { padding: 4px 8px; font-size: 0.9em; }
.btn.secondary { opacity: 0.85; }
.btn.danger { border-color: rgba(176,0,32,0.35); background: rgba(176,0,32,0.06); }

/* Bulk selection */
.bulkBar { display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 10px; background: rgba(0,0,0,0.03); border-radius: 10px; margin-bottom: 8px; }
.bulkInfo { display: flex; align-items: center; gap: 8px; }
.bulkActions { display: flex; gap: 8px; }
.selectAllRow { margin-bottom: 8px; }
.checkLabel { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.rowCheck { display: flex; align-items: center; padding-right: 8px; }
.row.checked { background: rgba(0,0,0,0.03); }

.mono, code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.subtle { opacity: 0.75; }
.small { font-size: 12px; }
.error { color: #b00020; }
.empty { display: flex; flex-direction: column; gap: 8px; padding: 8px; border: 1px dashed rgba(0, 0, 0, 0.18); border-radius: 12px; }
.spacer { height: 10px; }
.compareHint { margin-top: 10px; }
.rowActionsInline { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

@media (max-width: 1100px) {
  .grid { grid-template-columns: 1fr; }
  .panel.wide { grid-column: auto; }
}
</style>
