<script setup lang="ts">
/**
 * AI Image Filter Toolbar — Filtering & Sorting Controls
 * 
 * Provides filter dropdowns and sort controls for the gallery.
 * Syncs with the store's filter/sort state.
 * 
 * @package features/ai_images
 */

import { computed } from 'vue';
import { useAiImageStore } from './useAiImageStore';
import {
  GuitarCategory,
  ImageProvider,
  AssetStatus,
  type GallerySortBy,
  type SortDirection,
} from './types';

// =============================================================================
// STORE
// =============================================================================

const store = useAiImageStore();

// =============================================================================
// COMPUTED
// =============================================================================

const hasActiveFilters = computed(() => {
  const f = store.filters;
  return !!(f.category || f.provider || f.status || f.minRating || f.search);
});

const activeFilterCount = computed(() => {
  let count = 0;
  const f = store.filters;
  if (f.category) count++;
  if (f.provider) count++;
  if (f.status) count++;
  if (f.minRating) count++;
  if (f.search) count++;
  return count;
});

// =============================================================================
// OPTIONS
// =============================================================================

const categoryOptions = [
  { value: '', label: 'All Categories' },
  { value: GuitarCategory.ELECTRIC, label: 'Electric' },
  { value: GuitarCategory.ACOUSTIC, label: 'Acoustic' },
  { value: GuitarCategory.CLASSICAL, label: 'Classical' },
  { value: GuitarCategory.BASS, label: 'Bass' },
  { value: GuitarCategory.ARCHTOP, label: 'Archtop' },
];

const providerOptions = computed(() => {
  const options = [{ value: '', label: 'All Providers' }];
  for (const p of store.providers) {
    options.push({
      value: p.id,
      label: p.name,
    });
  }
  return options;
});

const statusOptions = [
  { value: '', label: 'All Status' },
  { value: AssetStatus.READY, label: 'Ready' },
  { value: AssetStatus.GENERATING, label: 'Generating' },
  { value: AssetStatus.ATTACHED, label: 'Attached' },
  { value: AssetStatus.FAILED, label: 'Failed' },
];

const ratingOptions = [
  { value: 0, label: 'Any Rating' },
  { value: 1, label: '★ and up' },
  { value: 2, label: '★★ and up' },
  { value: 3, label: '★★★ and up' },
  { value: 4, label: '★★★★ and up' },
  { value: 5, label: '★★★★★ only' },
];

const sortOptions: { value: GallerySortBy; label: string }[] = [
  { value: 'createdAt', label: 'Date' },
  { value: 'rating', label: 'Rating' },
  { value: 'cost', label: 'Cost' },
  { value: 'provider', label: 'Provider' },
];

// =============================================================================
// HANDLERS
// =============================================================================

function handleCategoryChange(e: Event): void {
  const value = (e.target as HTMLSelectElement).value;
  store.setFilter('category', value ? (value as GuitarCategory) : undefined);
}

function handleProviderChange(e: Event): void {
  const value = (e.target as HTMLSelectElement).value;
  store.setFilter('provider', value ? (value as ImageProvider) : undefined);
}

function handleStatusChange(e: Event): void {
  const value = (e.target as HTMLSelectElement).value;
  store.setFilter('status', value ? (value as AssetStatus) : undefined);
}

function handleRatingChange(e: Event): void {
  const value = parseInt((e.target as HTMLSelectElement).value, 10);
  store.setFilter('minRating', value > 0 ? value : undefined);
}

function handleSearchInput(e: Event): void {
  const value = (e.target as HTMLInputElement).value;
  store.setFilter('search', value || undefined);
}

function handleSortChange(e: Event): void {
  const value = (e.target as HTMLSelectElement).value as GallerySortBy;
  store.setSort(value, store.sortDirection);
}

function toggleSortDirection(): void {
  const newDir: SortDirection = store.sortDirection === 'desc' ? 'asc' : 'desc';
  store.setSort(store.sortBy, newDir);
}

function handleClearFilters(): void {
  store.clearFilters();
}
</script>

<template>
  <div class="ai-filter-toolbar">
    <!-- Search -->
    <div class="filter-group search-group">
      <input
        type="text"
        class="search-input"
        placeholder="Search prompts..."
        :value="store.filters.search ?? ''"
        @input="handleSearchInput"
      >
      <span class="search-icon">🔍</span>
    </div>

    <!-- Filters Row -->
    <div class="filters-row">
      <!-- Category -->
      <select
        class="filter-select"
        :value="store.filters.category ?? ''"
        @change="handleCategoryChange"
      >
        <option
          v-for="opt in categoryOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- Provider -->
      <select
        class="filter-select"
        :value="store.filters.provider ?? ''"
        @change="handleProviderChange"
      >
        <option
          v-for="opt in providerOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- Status -->
      <select
        class="filter-select"
        :value="store.filters.status ?? ''"
        @change="handleStatusChange"
      >
        <option
          v-for="opt in statusOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- Rating -->
      <select
        class="filter-select"
        :value="store.filters.minRating ?? 0"
        @change="handleRatingChange"
      >
        <option
          v-for="opt in ratingOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </option>
      </select>

      <!-- Spacer -->
      <div class="spacer" />

      <!-- Sort -->
      <div class="sort-group">
        <select
          class="filter-select sort-select"
          :value="store.sortBy"
          @change="handleSortChange"
        >
          <option
            v-for="opt in sortOptions"
            :key="opt.value"
            :value="opt.value"
          >
            {{ opt.label }}
          </option>
        </select>
        <button
          class="sort-direction-btn"
          :title="store.sortDirection === 'desc' ? 'Newest first' : 'Oldest first'"
          @click="toggleSortDirection"
        >
          {{ store.sortDirection === 'desc' ? '↓' : '↑' }}
        </button>
      </div>
    </div>

    <!-- Active Filters -->
    <div
      v-if="hasActiveFilters"
      class="active-filters"
    >
      <span class="filter-count">{{ activeFilterCount }} active</span>
      <button
        class="clear-btn"
        @click="handleClearFilters"
      >
        Clear all
      </button>
    </div>
  </div>
</template>

<style scoped>
.ai-filter-toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: var(--bg-panel, #16213e);
  border-bottom: 1px solid var(--border, #2a3f5f);
}

/* Search */
.search-group {
  position: relative;
}

.search-input {
  width: 100%;
  background: var(--bg-input, #0f1629);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 12px 8px 32px;
  color: var(--text, #e0e0e0);
  font-size: 13px;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent, #4fc3f7);
}

.search-input::placeholder {
  color: var(--text-dim, #8892a0);
}

.search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 12px;
  opacity: 0.6;
}

/* Filters Row */
.filters-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.filter-select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--text);
  font-size: 12px;
  min-width: 100px;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: var(--accent);
}

.spacer {
  flex: 1;
}

/* Sort */
.sort-group {
  display: flex;
  gap: 4px;
  align-items: center;
}

.sort-select {
  min-width: 80px;
}

.sort-direction-btn {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
  color: var(--text);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.15s;
}

.sort-direction-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
}

/* Active Filters */
.active-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
  border-top: 1px solid var(--border);
}

.filter-count {
  font-size: 11px;
  color: var(--accent);
}

.clear-btn {
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 11px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}

.clear-btn:hover {
  background: rgba(244, 67, 54, 0.1);
  color: #f44336;
}

/* Responsive */
@media (max-width: 600px) {
  .filters-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-select {
    width: 100%;
  }
  
  .spacer {
    display: none;
  }
  
  .sort-group {
    width: 100%;
  }
  
  .sort-select {
    flex: 1;
  }
}
</style>
