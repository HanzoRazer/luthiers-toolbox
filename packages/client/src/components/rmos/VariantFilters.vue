<script setup lang="ts">
/**
 * VariantFilters.vue
 *
 * Filter bar for variant triage: status filter, risk filter, and sorting.
 * Part of the Variant Status & Filters UX bundle.
 *
 * Emits filter changes to parent; does not fetch data itself.
 */
import { computed, ref, watch } from "vue";

type VariantStatus = "NEW" | "REVIEWED" | "PROMOTED" | "REJECTED";
type SortOption = "created" | "rating" | "risk" | "status";

export interface VariantFilters {
  status: VariantStatus | "ALL";
  riskNeedsAttention: boolean;
  sort: SortOption;
}

const props = defineProps<{
  /** Total count before filtering */
  totalCount: number;
  /** Count after filtering */
  filteredCount: number;
  /** Count of NEW variants */
  newCount?: number;
  /** Count of variants needing attention (YELLOW + RED) */
  attentionCount?: number;
}>();

const emit = defineEmits<{
  (e: "filter-change", filters: VariantFilters): void;
}>();

// Filter state
const statusFilter = ref<VariantStatus | "ALL">("ALL");
const riskNeedsAttention = ref(false);
const sortBy = ref<SortOption>("created");

// Emit changes when any filter changes
watch(
  [statusFilter, riskNeedsAttention, sortBy],
  () => {
    emit("filter-change", {
      status: statusFilter.value,
      riskNeedsAttention: riskNeedsAttention.value,
      sort: sortBy.value,
    });
  },
  { immediate: true }
);

// Status filter options
const statusOptions: { value: VariantStatus | "ALL"; label: string }[] = [
  { value: "ALL", label: "All" },
  { value: "NEW", label: "New" },
  { value: "REVIEWED", label: "Reviewed" },
  { value: "PROMOTED", label: "Promoted" },
  { value: "REJECTED", label: "Rejected" },
];

// Sort options
const sortOptions: { value: SortOption; label: string }[] = [
  { value: "created", label: "Created" },
  { value: "rating", label: "Rating" },
  { value: "risk", label: "Risk" },
  { value: "status", label: "Status" },
];

function clearFilters() {
  statusFilter.value = "ALL";
  riskNeedsAttention.value = false;
  sortBy.value = "created";
}

const hasActiveFilters = computed(
  () => statusFilter.value !== "ALL" || riskNeedsAttention.value
);
</script>

<template>
  <div class="variant-filters">
    <!-- Status filter -->
    <div class="filter-group">
      <label class="filter-label">Status</label>
      <select v-model="statusFilter" class="filter-select">
        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <!-- Needs Attention toggle -->
    <div class="filter-group">
      <label class="filter-checkbox">
        <input type="checkbox" v-model="riskNeedsAttention" />
        <span>
          Needs Attention
          <span v-if="attentionCount !== undefined" class="count-badge attention">
            {{ attentionCount }}
          </span>
        </span>
      </label>
    </div>

    <!-- Sort dropdown -->
    <div class="filter-group">
      <label class="filter-label">Sort by</label>
      <select v-model="sortBy" class="filter-select">
        <option v-for="opt in sortOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>
    </div>

    <!-- Spacer -->
    <div class="filter-spacer" />

    <!-- Clear filters button -->
    <button
      v-if="hasActiveFilters"
      class="btn-clear"
      @click="clearFilters"
      title="Clear all filters"
    >
      Clear
    </button>

    <!-- Counts -->
    <div class="filter-counts">
      <span v-if="filteredCount !== totalCount" class="filtered">
        {{ filteredCount }} / {{ totalCount }}
      </span>
      <span v-else class="total">{{ totalCount }} variants</span>
      <span v-if="newCount !== undefined && newCount > 0" class="new-indicator">
        • {{ newCount }} new
      </span>
    </div>
  </div>
</template>

<style scoped>
.variant-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.filter-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #6c757d;
}

.filter-select {
  padding: 4px 8px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.85rem;
  background: #fff;
  cursor: pointer;
  min-width: 90px;
}

.filter-select:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.filter-checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  cursor: pointer;
  user-select: none;
}

.filter-checkbox input {
  width: 14px;
  height: 14px;
  cursor: pointer;
}

.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  font-size: 0.7rem;
  font-weight: 600;
}

.count-badge.attention {
  background: #fff3cd;
  color: #856404;
}

.filter-spacer {
  flex: 1;
}

.btn-clear {
  padding: 4px 10px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.8rem;
  background: #fff;
  cursor: pointer;
  color: #6c757d;
}

.btn-clear:hover {
  background: #f0f0f0;
  border-color: #adb5bd;
}

.filter-counts {
  font-size: 0.8rem;
  color: #6c757d;
  display: flex;
  align-items: center;
  gap: 4px;
}

.filter-counts .filtered {
  font-weight: 600;
  color: #0066cc;
}

.filter-counts .new-indicator {
  color: #0f5132;
  font-weight: 500;
}
</style>
