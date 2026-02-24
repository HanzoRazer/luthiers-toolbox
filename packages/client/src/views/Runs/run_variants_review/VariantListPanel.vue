<template>
  <div class="panel">
    <div class="panel-title">
      Variants ({{ variants.length }})
    </div>

    <div
      v-if="!variants.length"
      class="empty"
    >
      <div class="subtle">
        No variants match current filters.
      </div>
      <button
        class="btn tiny"
        @click="$emit('resetFilters')"
      >
        Reset filters
      </button>
    </div>

    <div
      v-else
      class="list"
    >
      <!-- Bulk action bar -->
      <div
        v-if="selectedIds.size > 0"
        class="bulk-bar"
      >
        <div class="bulk-info">
          <strong>{{ selectedIds.size }}</strong> selected
          <button
            class="btn tiny secondary"
            @click="$emit('clearSelection')"
          >
            Clear
          </button>
        </div>
        <div class="bulk-actions">
          <button
            class="btn tiny primary"
            :disabled="bulkBusy || !promotableCount"
            title="Promote selected variants to manufacturing candidates"
            @click="$emit('bulkPromote')"
          >
            Promote Selected ({{ promotableCount }})
          </button>
          <button
            class="btn tiny danger"
            :disabled="bulkBusy || !rejectableCount"
            title="Rejects selected variants (applies one reason code to all)"
            @click="$emit('bulkReject')"
          >
            Reject Selected ({{ rejectableCount }})
          </button>
        </div>
      </div>

      <!-- Select all toggle -->
      <div class="select-all-row">
        <label class="check-label">
          <input
            type="checkbox"
            :checked="selectedIds.size === variants.length && variants.length > 0"
            :indeterminate="selectedIds.size > 0 && selectedIds.size < variants.length"
            @change="selectedIds.size === variants.length ? $emit('clearSelection') : $emit('selectAll')"
          >
          <span class="small subtle">Select all ({{ variants.length }})</span>
        </label>
      </div>

      <button
        v-for="v in variants"
        :key="v.advisory_id"
        class="row"
        :class="{ on: selectedVariantId === v.advisory_id, checked: selectedIds.has(v.advisory_id) }"
        :title="getHoverTitle(v)"
        @click="$emit('select', v.advisory_id)"
      >
        <div
          class="row-check"
          @click.stop
        >
          <input
            type="checkbox"
            :checked="selectedIds.has(v.advisory_id)"
            @change="$emit('toggleSelected', v.advisory_id)"
          >
        </div>
        <div class="row-main">
          <div class="row-top">
            <div class="mono">
              {{ v.advisory_id.slice(0, 12) }}...
            </div>
            <VariantStatusBadge
              :status="deriveStatus(v)"
              :risk="(v.risk_level ?? 'UNKNOWN') as any"
            />
          </div>

          <div class="row-meta">
            <span class="subtle small">Rating: {{ v.rating ?? "—" }}</span>
            <span class="sep">*</span>
            <span class="subtle small">Risk: {{ (v.risk_level ?? "UNKNOWN") }}</span>
            <span class="sep">*</span>
            <span class="subtle small">Preview: {{ v.has_preview === false ? "No" : "Yes" }}</span>
          </div>
        </div>

        <div class="row-actions">
          <button
            class="btn tiny secondary"
            @click.stop="$emit('pickCompare', v.advisory_id)"
          >
            Pick
          </button>
        </div>
      </button>
    </div>

    <div class="compare-hint subtle small">
      Compare picks:
      <span class="mono">{{ compareLeft ? compareLeft.slice(0, 8) + "..." : "—" }}</span>
      vs
      <span class="mono">{{ compareRight ? compareRight.slice(0, 8) + "..." : "—" }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import VariantStatusBadge from "@/components/rmos/VariantStatusBadge.vue";
import type { AdvisoryVariantSummary, VariantStatus } from "@/sdk/rmos/runs";

defineProps<{
  variants: AdvisoryVariantSummary[]
  selectedVariantId: string | null
  selectedIds: Set<string>
  bulkBusy: boolean
  promotableCount: number
  rejectableCount: number
  compareLeft: string | null
  compareRight: string | null
}>()

defineEmits<{
  select: [id: string]
  toggleSelected: [id: string]
  selectAll: []
  clearSelection: []
  resetFilters: []
  bulkPromote: []
  bulkReject: []
  pickCompare: [id: string]
}>()

function deriveStatus(v: AdvisoryVariantSummary): VariantStatus {
  if (v.status) return v.status;
  if (v.promoted_candidate_id) return "PROMOTED";
  if (v.rejected) return "REJECTED";
  if ((v.rating ?? null) !== null || (v.notes ?? null)) return "REVIEWED";
  return "NEW";
}

function getHoverTitle(v: AdvisoryVariantSummary): string {
  const status = deriveStatus(v);
  if (status !== "REJECTED") return v.advisory_id;

  const parts: string[] = [];
  parts.push(`REJECTED: ${v.rejection_reason_code ?? "—"}`);
  if (v.rejection_reason_detail) parts.push(`Detail: ${v.rejection_reason_detail}`);
  if (v.rejection_operator_note) parts.push(`Note: ${v.rejection_operator_note}`);
  if (v.rejected_at_utc) parts.push(`At: ${v.rejected_at_utc}`);
  return parts.join("\n");
}
</script>

<style scoped>
.panel {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 10px;
  background: white;
}

.panel-title {
  font-weight: 800;
  margin-bottom: 8px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  text-align: left;
  padding: 10px;
  border: 1px solid rgba(0, 0, 0, 0.10);
  border-radius: 12px;
  background: white;
  cursor: pointer;
}

.row.on {
  border-color: rgba(0, 0, 0, 0.35);
}

.row-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.row-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
}

.row-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.sep {
  opacity: 0.35;
}

.row-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.btn {
  padding: 8px 10px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  background: white;
  cursor: pointer;
}

.btn.tiny {
  padding: 4px 8px;
  font-size: 0.9em;
}

.btn.secondary {
  opacity: 0.85;
}

.btn.danger {
  border-color: rgba(176, 0, 32, 0.35);
  background: rgba(176, 0, 32, 0.06);
}

.bulk-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 10px;
  margin-bottom: 8px;
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bulk-actions {
  display: flex;
  gap: 8px;
}

.select-all-row {
  margin-bottom: 8px;
}

.check-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.row-check {
  display: flex;
  align-items: center;
  padding-right: 8px;
}

.row.checked {
  background: rgba(0, 0, 0, 0.03);
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.subtle {
  opacity: 0.75;
}

.small {
  font-size: 12px;
}

.empty {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  border: 1px dashed rgba(0, 0, 0, 0.18);
  border-radius: 12px;
}

.compare-hint {
  margin-top: 10px;
}
</style>
