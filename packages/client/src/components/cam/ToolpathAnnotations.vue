<template>
  <div class="toolpath-annotations">
    <!-- Header -->
    <div class="annotations-header">
      <h3>📝 Annotations</h3>
      <div class="header-actions">
        <button
          class="action-btn"
          title="Import annotations"
          @click="handleImport"
        >
          📥
        </button>
        <button
          class="action-btn"
          title="Export annotations"
          @click="handleExport"
        >
          📤
        </button>
        <button class="close-btn" title="Close" @click="$emit('close')">×</button>
      </div>
    </div>

    <!-- Quick Add Bookmark -->
    <div v-if="currentSegment !== null" class="quick-bookmark">
      <button class="bookmark-btn" @click="addQuickBookmark">
        🔖 Bookmark Current Position
      </button>
    </div>

    <!-- Type Filter Tabs -->
    <div class="type-tabs">
      <button
        v-for="tab in typeTabs"
        :key="tab.type"
        class="type-tab"
        :class="{ active: activeTab === tab.type }"
        :style="{ '--tab-color': tab.color }"
        @click="activeTab = tab.type"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-count">{{ counts[tab.type] || 0 }}</span>
      </button>
    </div>

    <!-- Add New Annotation Form -->
    <div v-if="showAddForm" class="add-form">
      <div class="form-header">
        <span>Add {{ getCategoryLabel(newAnnotation.type) }}</span>
        <button class="close-btn small" @click="showAddForm = false">×</button>
      </div>

      <div class="form-row">
        <label>Type</label>
        <select v-model="newAnnotation.type">
          <option v-for="cat in categories" :key="cat.type" :value="cat.type">
            {{ cat.icon }} {{ cat.label }}
          </option>
        </select>
      </div>

      <div class="form-row">
        <label>Label</label>
        <input
          v-model="newAnnotation.label"
          type="text"
          placeholder="Short title..."
          maxlength="50"
        />
      </div>

      <div class="form-row">
        <label>Description</label>
        <textarea
          v-model="newAnnotation.description"
          placeholder="Add details..."
          rows="3"
        ></textarea>
      </div>

      <div class="form-actions">
        <button class="cancel-btn" @click="showAddForm = false">Cancel</button>
        <button
          class="save-btn"
          :disabled="!newAnnotation.label.trim()"
          @click="saveAnnotation"
        >
          Save
        </button>
      </div>
    </div>

    <!-- Add Button -->
    <button
      v-if="!showAddForm && currentSegment !== null"
      class="add-annotation-btn"
      @click="startAddAnnotation"
    >
      + Add Annotation at Current Position
    </button>

    <!-- Annotations List -->
    <div class="annotations-list">
      <div v-if="filteredAnnotations.length === 0" class="empty-state">
        <span class="empty-icon">{{ getTabIcon(activeTab) }}</span>
        <span class="empty-text">
          {{ activeTab === "all" ? "No annotations yet" : `No ${activeTab}s` }}
        </span>
      </div>

      <div
        v-for="ann in filteredAnnotations"
        :key="ann.id"
        class="annotation-item"
        :class="{ editing: editingId === ann.id }"
        :style="{ '--item-color': ann.color }"
      >
        <!-- View Mode -->
        <template v-if="editingId !== ann.id">
          <div class="item-header">
            <span class="item-icon">{{ ann.icon }}</span>
            <span class="item-label">{{ ann.label }}</span>
            <div class="item-actions">
              <button
                class="action-btn small"
                title="Go to position"
                @click="$emit('goto', ann)"
              >
                🎯
              </button>
              <button
                class="action-btn small"
                title="Edit"
                @click="startEdit(ann)"
              >
                ✏️
              </button>
              <button
                class="action-btn small danger"
                title="Delete"
                @click="deleteAnnotation(ann.id)"
              >
                🗑️
              </button>
            </div>
          </div>

          <div v-if="ann.description" class="item-description">
            {{ ann.description }}
          </div>

          <div class="item-meta">
            <span v-if="ann.segmentIndex !== null" class="meta-tag">
              Seg #{{ ann.segmentIndex }}
            </span>
            <span v-if="ann.lineNumber !== null" class="meta-tag">
              Line {{ ann.lineNumber }}
            </span>
            <span class="meta-tag">
              Z={{ ann.position[2].toFixed(2) }}
            </span>
          </div>
        </template>

        <!-- Edit Mode -->
        <template v-else>
          <div class="edit-form">
            <div class="form-row compact">
              <select v-model="editData.type">
                <option v-for="cat in categories" :key="cat.type" :value="cat.type">
                  {{ cat.icon }} {{ cat.label }}
                </option>
              </select>
            </div>

            <div class="form-row compact">
              <input
                v-model="editData.label"
                type="text"
                placeholder="Label..."
                maxlength="50"
              />
            </div>

            <div class="form-row compact">
              <textarea
                v-model="editData.description"
                placeholder="Description..."
                rows="2"
              ></textarea>
            </div>

            <div class="form-actions compact">
              <button class="cancel-btn small" @click="cancelEdit">Cancel</button>
              <button
                class="save-btn small"
                :disabled="!editData.label.trim()"
                @click="saveEdit"
              >
                Save
              </button>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- Footer Stats -->
    <div class="annotations-footer">
      <span class="total-count">{{ totalCount }} annotation{{ totalCount !== 1 ? 's' : '' }}</span>
      <button
        v-if="totalCount > 0"
        class="clear-btn"
        title="Clear all annotations"
        @click="confirmClearAll"
      >
        Clear All
      </button>
    </div>

    <!-- Hidden file input for import -->
    <input
      ref="fileInputRef"
      type="file"
      accept=".json"
      style="display: none"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import {
  annotationManager,
  ANNOTATION_CATEGORIES,
  type Annotation,
  type AnnotationType,
  type AnnotationExport,
} from "@/util/toolpathAnnotations";

// Props
const props = defineProps<{
  currentSegment: number | null;
  currentPosition: [number, number, number] | null;
  currentLineNumber: number | null;
  gcodeHash?: string;
}>();

// Emits
const emit = defineEmits<{
  (e: "close"): void;
  (e: "goto", annotation: Annotation): void;
}>();

// State
const annotations = ref<Annotation[]>([]);
const activeTab = ref<AnnotationType | "all">("all");
const showAddForm = ref(false);
const editingId = ref<string | null>(null);
const fileInputRef = ref<HTMLInputElement | null>(null);

const newAnnotation = ref({
  type: "note" as AnnotationType,
  label: "",
  description: "",
});

const editData = ref({
  type: "note" as AnnotationType,
  label: "",
  description: "",
});

// Categories for dropdowns
const categories = ANNOTATION_CATEGORIES;

// Type tabs including "all"
const typeTabs = computed(() => [
  { type: "all" as const, icon: "📋", color: "#666", label: "All" },
  ...ANNOTATION_CATEGORIES.map((c) => ({
    type: c.type,
    icon: c.icon,
    color: c.color,
    label: c.label,
  })),
]);

// Counts by type
const counts = computed(() => {
  const result: Record<string, number> = { all: annotations.value.length };
  for (const ann of annotations.value) {
    result[ann.type] = (result[ann.type] || 0) + 1;
  }
  return result;
});

// Filtered annotations
const filteredAnnotations = computed(() => {
  if (activeTab.value === "all") {
    return [...annotations.value].sort((a, b) => b.createdAt - a.createdAt);
  }
  return annotations.value
    .filter((a) => a.type === activeTab.value)
    .sort((a, b) => b.createdAt - a.createdAt);
});

// Total count
const totalCount = computed(() => annotations.value.length);

// Helpers
function getCategoryLabel(type: AnnotationType): string {
  return ANNOTATION_CATEGORIES.find((c) => c.type === type)?.label ?? type;
}

function getTabIcon(tab: AnnotationType | "all"): string {
  if (tab === "all") return "📋";
  return ANNOTATION_CATEGORIES.find((c) => c.type === tab)?.icon ?? "📝";
}

// Refresh annotations from manager
function refreshAnnotations(): void {
  annotations.value = annotationManager.getAll();
}

// Add quick bookmark
function addQuickBookmark(): void {
  if (props.currentPosition) {
    annotationManager.add({
      type: "bookmark",
      label: `Bookmark ${counts.value.bookmark + 1}`,
      position: props.currentPosition,
      segmentIndex: props.currentSegment,
      lineNumber: props.currentLineNumber,
    });
    refreshAnnotations();
  }
}

// Start adding annotation
function startAddAnnotation(): void {
  newAnnotation.value = {
    type: "note",
    label: "",
    description: "",
  };
  showAddForm.value = true;
}

// Save new annotation
function saveAnnotation(): void {
  if (!newAnnotation.value.label.trim() || !props.currentPosition) return;

  annotationManager.add({
    type: newAnnotation.value.type,
    label: newAnnotation.value.label.trim(),
    description: newAnnotation.value.description.trim(),
    position: props.currentPosition,
    segmentIndex: props.currentSegment,
    lineNumber: props.currentLineNumber,
  });

  showAddForm.value = false;
  refreshAnnotations();
}

// Start editing
function startEdit(ann: Annotation): void {
  editingId.value = ann.id;
  editData.value = {
    type: ann.type,
    label: ann.label,
    description: ann.description,
  };
}

// Cancel editing
function cancelEdit(): void {
  editingId.value = null;
}

// Save edit
function saveEdit(): void {
  if (!editingId.value || !editData.value.label.trim()) return;

  annotationManager.update(editingId.value, {
    type: editData.value.type,
    label: editData.value.label.trim(),
    description: editData.value.description.trim(),
  });

  editingId.value = null;
  refreshAnnotations();
}

// Delete annotation
function deleteAnnotation(id: string): void {
  annotationManager.remove(id);
  refreshAnnotations();
}

// Clear all
function confirmClearAll(): void {
  if (confirm("Delete all annotations? This cannot be undone.")) {
    annotationManager.clearSaved();
    refreshAnnotations();
  }
}

// Export
function handleExport(): void {
  const data = annotationManager.export();
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `toolpath-annotations-${Date.now()}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

// Import
function handleImport(): void {
  fileInputRef.value?.click();
}

function handleFileSelect(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const data = JSON.parse(e.target?.result as string) as AnnotationExport;
      const count = annotationManager.import(data);
      refreshAnnotations();
      alert(`Imported ${count} annotation${count !== 1 ? "s" : ""}`);
    } catch {
      alert("Failed to import annotations. Invalid file format.");
    }
  };
  reader.readAsText(file);

  // Reset input
  input.value = "";
}

// Subscribe to manager updates
let unsubscribe: (() => void) | null = null;

onMounted(() => {
  unsubscribe = annotationManager.subscribe(refreshAnnotations);
  refreshAnnotations();
});

onUnmounted(() => {
  unsubscribe?.();
});

// Watch for G-code changes
watch(
  () => props.gcodeHash,
  () => {
    refreshAnnotations();
  }
);
</script>

<style scoped>
.toolpath-annotations {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

/* Header */
.annotations-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: linear-gradient(135deg, #4a90d9, #357abd);
  color: white;
}

.annotations-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 4px;
}

.action-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.action-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.action-btn.small {
  padding: 2px 6px;
  font-size: 11px;
}

.action-btn.danger:hover {
  background: rgba(231, 76, 60, 0.5);
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 18px;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.close-btn.small {
  width: 20px;
  height: 20px;
  font-size: 14px;
}

/* Quick Bookmark */
.quick-bookmark {
  padding: 8px 12px;
  border-bottom: 1px solid #2a2a4a;
}

.bookmark-btn {
  width: 100%;
  padding: 8px 12px;
  background: linear-gradient(135deg, #4a90d9, #357abd);
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: transform 0.1s, box-shadow 0.2s;
}

.bookmark-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(74, 144, 217, 0.3);
}

/* Type Tabs */
.type-tabs {
  display: flex;
  gap: 2px;
  padding: 8px;
  background: #15152a;
  overflow-x: auto;
}

.type-tab {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  background: #2a2a4a;
  border: none;
  border-radius: 6px;
  color: #888;
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
  white-space: nowrap;
}

.type-tab:hover {
  background: #3a3a5a;
  color: #aaa;
}

.type-tab.active {
  background: var(--tab-color, #4a90d9);
  color: white;
}

.tab-icon {
  font-size: 12px;
}

.tab-count {
  background: rgba(0, 0, 0, 0.3);
  padding: 1px 5px;
  border-radius: 8px;
  font-size: 10px;
}

/* Add Form */
.add-form {
  padding: 12px;
  background: #252545;
  border-bottom: 1px solid #2a2a4a;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  color: #ccc;
  font-weight: 500;
}

.form-row {
  margin-bottom: 8px;
}

.form-row label {
  display: block;
  margin-bottom: 4px;
  color: #888;
  font-size: 11px;
}

.form-row input,
.form-row select,
.form-row textarea {
  width: 100%;
  padding: 8px;
  background: #1a1a2e;
  border: 1px solid #3a3a5a;
  border-radius: 4px;
  color: #eee;
  font-size: 12px;
  font-family: inherit;
}

.form-row input:focus,
.form-row select:focus,
.form-row textarea:focus {
  outline: none;
  border-color: #4a90d9;
}

.form-row textarea {
  resize: vertical;
  min-height: 60px;
}

.form-row.compact {
  margin-bottom: 6px;
}

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 10px;
}

.form-actions.compact {
  margin-top: 8px;
}

.cancel-btn,
.save-btn {
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.cancel-btn {
  background: #3a3a5a;
  color: #aaa;
}

.cancel-btn:hover {
  background: #4a4a6a;
}

.save-btn {
  background: #4a90d9;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #357abd;
}

.save-btn:disabled {
  background: #3a3a5a;
  color: #666;
  cursor: not-allowed;
}

.cancel-btn.small,
.save-btn.small {
  padding: 4px 10px;
  font-size: 11px;
}

/* Add Button */
.add-annotation-btn {
  margin: 8px 12px;
  padding: 10px;
  background: #252545;
  border: 1px dashed #4a4a6a;
  border-radius: 6px;
  color: #888;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.add-annotation-btn:hover {
  background: #2a2a4a;
  border-color: #4a90d9;
  color: #aaa;
}

/* Annotations List */
.annotations-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #666;
}

.empty-icon {
  font-size: 32px;
  margin-bottom: 8px;
  opacity: 0.5;
}

.empty-text {
  font-size: 13px;
}

/* Annotation Item */
.annotation-item {
  background: #252545;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 8px;
  border-left: 3px solid var(--item-color, #4a90d9);
  transition: background 0.2s;
}

.annotation-item:hover {
  background: #2a2a4a;
}

.annotation-item.editing {
  background: #2a2a4a;
  border-left-width: 4px;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.item-icon {
  font-size: 14px;
}

.item-label {
  flex: 1;
  color: #eee;
  font-weight: 500;
}

.item-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.annotation-item:hover .item-actions {
  opacity: 1;
}

.item-description {
  margin-top: 6px;
  padding-left: 22px;
  color: #999;
  font-size: 11px;
  line-height: 1.4;
}

.item-meta {
  display: flex;
  gap: 6px;
  margin-top: 8px;
  padding-left: 22px;
}

.meta-tag {
  padding: 2px 6px;
  background: #1a1a2e;
  border-radius: 4px;
  color: #777;
  font-size: 10px;
  font-family: monospace;
}

/* Edit Form */
.edit-form {
  padding-top: 4px;
}

/* Footer */
.annotations-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #15152a;
  border-top: 1px solid #2a2a4a;
}

.total-count {
  color: #666;
  font-size: 11px;
}

.clear-btn {
  background: none;
  border: none;
  color: #e74c3c;
  cursor: pointer;
  font-size: 11px;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.2s;
}

.clear-btn:hover {
  background: rgba(231, 76, 60, 0.2);
}

/* Scrollbar */
.annotations-list::-webkit-scrollbar {
  width: 6px;
}

.annotations-list::-webkit-scrollbar-track {
  background: #1a1a2e;
}

.annotations-list::-webkit-scrollbar-thumb {
  background: #3a3a5a;
  border-radius: 3px;
}

.annotations-list::-webkit-scrollbar-thumb:hover {
  background: #4a4a6a;
}
</style>
