<script setup lang="ts">
/**
 * SavedViewsPanel.vue - Reusable saved filter views panel
 *
 * Drop into any dashboard that needs saved filter presets.
 *
 * Props:
 * - storageKey: localStorage key for persistence
 * - getCurrentFilters: function returning current filter state
 *
 * Events:
 * - apply: emitted with filters when a saved view is applied
 *
 * Example:
 * ```vue
 * <SavedViewsPanel
 *   storage-key="my_dashboard_views"
 *   :get-current-filters="getCurrentFilters"
 *   @apply="applyFilters"
 * />
 * ```
 */
import { onMounted, watch } from 'vue'
import { useSavedViews, type SavedView } from '@/composables'

const props = defineProps<{
  storageKey: string
  getCurrentFilters: () => Record<string, string>
}>()

const emit = defineEmits<{
  apply: [filters: Record<string, string>]
}>()

const {
  // State
  savedViews,
  newViewName,
  newViewDescription,
  newViewTags,
  saveError,
  saveHint,
  viewSearch,
  viewTagFilter,
  viewSortMode,
  importInputRef,

  // Computed
  canSaveCurrentView,
  defaultViewLabel,
  defaultView,
  allViewTags,
  sortedViews,
  recentViews,

  // Methods
  loadSavedViews,
  saveCurrentView,
  applySavedView,
  renameView,
  duplicateView,
  deleteSavedView,
  setDefaultView,
  triggerImport,
  handleImportFile,
  exportViews,
  viewTooltip,
  formatMetaTime,
  formatRelativeTime,
} = useSavedViews({
  storageKey: props.storageKey,
  getCurrentFilters: props.getCurrentFilters,
  onApply: (filters) => emit('apply', filters),
})

// Load saved views on mount
onMounted(() => {
  loadSavedViews()
})

// Expose default view for parent to auto-apply on mount if needed
defineExpose({
  defaultView,
  savedViews,
  loadSavedViews,
})
</script>

<template>
  <div class="flex flex-col gap-2 text-[11px] text-gray-700 border rounded bg-gray-50/60 p-2">
    <div class="flex flex-wrap items-start gap-3">
      <span class="font-semibold text-gray-800 mt-1">Saved Views:</span>

      <!-- Create view block -->
      <div class="flex flex-col gap-1 w-full max-w-lg">
        <div class="flex items-center gap-2">
          <input
            v-model="newViewName"
            type="text"
            placeholder="e.g. My Filter Preset"
            class="px-2 py-1 border rounded text-[11px] w-52"
          >
          <button
            class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
            :disabled="!canSaveCurrentView"
            @click="saveCurrentView"
          >
            Save current view
          </button>
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <input
            v-model="newViewDescription"
            type="text"
            placeholder="Optional description"
            class="px-2 py-1 border rounded text-[11px] flex-1 min-w-[220px]"
          >
        </div>
        <div class="flex flex-wrap items-center gap-2">
          <input
            v-model="newViewTags"
            type="text"
            placeholder="Tags (comma-separated)"
            class="px-2 py-1 border rounded text-[11px] flex-1 min-w-[220px]"
          >
          <span class="text-[10px] text-gray-500">
            Tags help organize saved views.
          </span>
        </div>
      </div>

      <!-- View list controls -->
      <div class="flex flex-col gap-1 ml-auto min-w-[260px]">
        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Sort:</span>
          <select
            v-model="viewSortMode"
            class="px-2 py-1 border rounded text-[10px]"
          >
            <option value="default">
              Default
            </option>
            <option value="name">
              Name
            </option>
            <option value="created">
              Created
            </option>
            <option value="lastUsed">
              Last used
            </option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Search:</span>
          <input
            v-model="viewSearch"
            type="text"
            placeholder="Filter views"
            class="px-2 py-1 border rounded text-[10px] flex-1"
          >
        </div>

        <div class="flex items-center gap-2">
          <span class="text-[10px] text-gray-500">Tag:</span>
          <select
            v-model="viewTagFilter"
            class="px-2 py-1 border rounded text-[10px] flex-1"
          >
            <option value="">
              All tags
            </option>
            <option
              v-for="tag in allViewTags"
              :key="tag"
              :value="tag"
            >
              {{ tag }}
            </option>
          </select>
        </div>

        <div class="flex items-center gap-2">
          <input
            ref="importInputRef"
            type="file"
            accept="application/json"
            class="hidden"
            @change="handleImportFile"
          >
          <button
            class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100"
            @click="triggerImport"
          >
            Import
          </button>
          <button
            class="px-2 py-1 rounded border text-[11px] text-gray-700 hover:bg-gray-100 disabled:opacity-50"
            :disabled="!savedViews.length"
            @click="exportViews"
          >
            Export
          </button>
        </div>
      </div>
    </div>

    <!-- Recently used strip -->
    <div
      v-if="recentViews.length"
      class="flex flex-wrap items-center gap-2 mt-1"
    >
      <span class="text-[10px] text-gray-500">
        Recent:
      </span>
      <button
        v-for="view in recentViews"
        :key="view.id"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border bg-white text-[10px] text-gray-800 hover:bg-gray-100"
        :title="viewTooltip(view)"
        @click="applySavedView(view)"
      >
        <span class="font-mono truncate max-w-[160px]">
          {{ view.name }}
        </span>
        <span class="text-[9px] text-gray-500">
          ({{ formatRelativeTime(view.lastUsedAt || view.createdAt) }})
        </span>
      </button>
    </div>

    <!-- Status line -->
    <div class="flex flex-wrap items-center gap-2 mt-1">
      <span
        v-if="saveError"
        class="text-[10px] text-rose-600"
      >
        {{ saveError }}
      </span>
      <span
        v-else-if="saveHint"
        class="text-[10px] text-gray-500"
      >
        {{ saveHint }}
      </span>
      <span
        v-else
        class="text-[10px] text-gray-500"
      >
        Default: <span class="font-mono">{{ defaultViewLabel }}</span>
        <span
          v-if="viewSearch || viewTagFilter"
          class="ml-2"
        >
          · {{ sortedViews.length }} of {{ savedViews.length }} views
        </span>
      </span>
    </div>

    <!-- Saved views list -->
    <div
      v-if="sortedViews.length"
      class="flex flex-col gap-1"
    >
      <div class="text-[10px] text-gray-500">
        Click name to apply · ✏ rename · ⧉ duplicate · ⭐ default · 🗑 delete
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div
          v-for="view in sortedViews"
          :key="view.id"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full border bg-white shadow-sm"
        >
          <button
            class="text-[10px] text-gray-800 font-medium hover:underline"
            :title="viewTooltip(view)"
            @click="applySavedView(view)"
          >
            {{ view.name }}
          </button>
          <span
            v-if="view.tags && view.tags.length"
            class="inline-flex items-center gap-0.5 ml-1"
          >
            <span
              v-for="tag in view.tags"
              :key="view.id + ':' + tag"
              class="px-1 rounded-full bg-sky-50 border border-sky-100 text-[9px] text-sky-700"
            >
              {{ tag }}
            </span>
          </span>
          <button
            class="text-[10px] text-gray-500 hover:text-gray-700"
            title="Rename"
            @click="renameView(view.id)"
          >
            ✏
          </button>
          <button
            class="text-[10px] text-gray-500 hover:text-gray-700"
            title="Duplicate"
            @click="duplicateView(view.id)"
          >
            ⧉
          </button>
          <button
            class="text-[10px]"
            :class="view.isDefault ? 'text-amber-500' : 'text-gray-400 hover:text-amber-500'"
            :title="view.isDefault ? 'Default view' : 'Set as default'"
            @click="setDefaultView(view.id)"
          >
            ⭐
          </button>
          <button
            class="text-[10px] text-gray-500 hover:text-rose-600"
            title="Delete"
            @click="deleteSavedView(view.id)"
          >
            🗑
          </button>
        </div>
      </div>

      <!-- View metadata -->
      <div class="text-[10px] text-gray-500 mt-1 max-w-full space-y-0.5">
        <div
          v-for="view in sortedViews"
          :key="view.id + 'meta'"
          class="flex flex-wrap items-center gap-2"
        >
          <span class="font-mono text-[10px]">
            {{ view.name }}
          </span>
          <span
            v-if="view.isDefault"
            class="text-amber-600 text-[10px]"
          >
            (default)
          </span>
          <span
            v-if="view.description"
            class="text-gray-600 text-[10px]"
          >
            — {{ view.description }}
          </span>
          <span class="text-gray-500 text-[10px]">
            created: {{ formatMetaTime(view.createdAt) }}
          </span>
          <span class="text-gray-500 text-[10px]">
            used: {{ formatMetaTime(view.lastUsedAt || view.createdAt) }}
          </span>
        </div>
      </div>
    </div>

    <div
      v-else
      class="text-[10px] text-gray-500 italic"
    >
      <span v-if="savedViews.length">
        No views match the current filter.
      </span>
      <span v-else>
        No saved views yet. Create your first view above.
      </span>
    </div>
  </div>
</template>
