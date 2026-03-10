<template>
  <div class="toolpath-compare-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3>🔀 Compare Toolpaths</h3>
      <button class="close-btn" title="Close" @click="$emit('close')">×</button>
    </div>

    <!-- File Upload Section -->
    <div v-if="!comparisonResult" class="upload-section">
      <p class="upload-hint">
        Load a second G-code file to compare against the current toolpath.
      </p>

      <div class="upload-area" @dragover.prevent @drop.prevent="handleDrop">
        <input
          ref="fileInputRef"
          type="file"
          accept=".nc,.gcode,.ngc,.tap,.txt"
          style="display: none"
          @change="handleFileSelect"
        />

        <div class="upload-content">
          <span class="upload-icon">📄</span>
          <span class="upload-text">Drag & drop G-code file</span>
          <span class="upload-or">or</span>
          <button class="upload-btn" @click="fileInputRef?.click()">
            Browse Files
          </button>
        </div>
      </div>

      <!-- Paste G-code -->
      <div class="paste-section">
        <span class="paste-label">Or paste G-code:</span>
        <textarea
          v-model="pastedGcode"
          class="paste-input"
          placeholder="Paste G-code here..."
          rows="4"
        ></textarea>
        <button
          class="compare-btn"
          :disabled="!pastedGcode.trim()"
          @click="compareWithPasted"
        >
          Compare
        </button>
      </div>
    </div>

    <!-- Comparison Results -->
    <div v-else class="results-section">
      <!-- Summary Banner -->
      <div
        class="summary-banner"
        :class="comparisonResult.summary.verdict"
      >
        <span class="summary-icon">
          {{ comparisonResult.summary.verdict === 'improved' ? '✅' :
             comparisonResult.summary.verdict === 'degraded' ? '⚠️' : '≈' }}
        </span>
        <span class="summary-text">{{ comparisonResult.summary.summaryText }}</span>
      </div>

      <!-- Stats Comparison Grid -->
      <div class="stats-grid">
        <div class="stats-header">
          <span></span>
          <span>Base</span>
          <span>Compare</span>
          <span>Δ</span>
        </div>

        <div
          v-for="stat in keyStats"
          :key="stat.field"
          class="stats-row"
          :class="{ improved: stat.isImprovement && stat.difference !== 0 }"
        >
          <span class="stat-field">{{ stat.field }}</span>
          <span class="stat-base">{{ stat.baseFormatted }}</span>
          <span class="stat-compare">{{ stat.compareFormatted }}</span>
          <span class="stat-diff" :class="stat.isImprovement ? 'positive' : 'negative'">
            {{ stat.diffFormatted }}
          </span>
        </div>
      </div>

      <!-- Segment Changes Summary -->
      <div class="changes-summary">
        <h4>Segment Changes</h4>
        <div class="changes-chips">
          <span class="chip same">
            {{ sameCount }} unchanged
          </span>
          <span v-if="comparisonResult.summary.segmentsModified > 0" class="chip modified">
            {{ comparisonResult.summary.segmentsModified }} modified
          </span>
          <span v-if="comparisonResult.summary.segmentsAdded > 0" class="chip added">
            +{{ comparisonResult.summary.segmentsAdded }} added
          </span>
          <span v-if="comparisonResult.summary.segmentsRemoved > 0" class="chip removed">
            -{{ comparisonResult.summary.segmentsRemoved }} removed
          </span>
        </div>
      </div>

      <!-- Diff List (collapsible) -->
      <div class="diff-section">
        <button class="diff-toggle" @click="showDiffList = !showDiffList">
          {{ showDiffList ? '▼' : '▶' }} Detailed Changes ({{ changedDiffs.length }})
        </button>

        <ul v-if="showDiffList" class="diff-list">
          <li
            v-for="(diff, i) in changedDiffs.slice(0, 50)"
            :key="i"
            class="diff-item"
            :class="diff.type"
          >
            <span class="diff-badge">{{ diffBadge(diff.type) }}</span>
            <span class="diff-index">
              {{ diff.type === 'removed' ? `#${diff.baseIndex}` : `#${diff.compareIndex}` }}
            </span>
            <span class="diff-desc">{{ diff.description }}</span>
          </li>
          <li v-if="changedDiffs.length > 50" class="diff-more">
            +{{ changedDiffs.length - 50 }} more changes...
          </li>
        </ul>
      </div>

      <!-- Actions -->
      <div class="actions-bar">
        <button class="action-btn secondary" @click="reset">
          Compare Another
        </button>
        <button
          class="action-btn primary"
          :class="{ active: overlayEnabled }"
          @click="toggleOverlay"
        >
          {{ overlayEnabled ? '🔵 Overlay On' : '⚪ Overlay Off' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import {
  compareToolpaths,
  type MoveSegment,
  type ComparisonResult,
  type SegmentDiff,
} from "@/util/toolpathComparison";

// Props
const props = defineProps<{
  /** Base segments (current toolpath) */
  baseSegments: MoveSegment[];
  /** Base G-code string for hash comparison */
  baseGcode?: string;
}>();

// Emits
const emit = defineEmits<{
  (e: "close"): void;
  (e: "compare-segments", segments: MoveSegment[]): void;
  (e: "overlay-toggle", enabled: boolean): void;
}>();

// State
const fileInputRef = ref<HTMLInputElement | null>(null);
const pastedGcode = ref("");
const comparisonResult = ref<ComparisonResult | null>(null);
const compareSegments = ref<MoveSegment[]>([]);
const showDiffList = ref(false);
const overlayEnabled = ref(false);

// Computed
const keyStats = computed(() => {
  if (!comparisonResult.value) return [];
  // Show most important stats
  return comparisonResult.value.statsDiffs.filter(s =>
    ["Total Time", "Cut Distance", "Rapid Distance", "Segment Count"].includes(s.field)
  );
});

const sameCount = computed(() => {
  if (!comparisonResult.value) return 0;
  return comparisonResult.value.segmentDiffs.filter(d => d.type === "same").length;
});

const changedDiffs = computed(() => {
  if (!comparisonResult.value) return [];
  return comparisonResult.value.segmentDiffs.filter(d => d.type !== "same");
});

// Methods
function diffBadge(type: SegmentDiff["type"]): string {
  switch (type) {
    case "added": return "+";
    case "removed": return "−";
    case "modified": return "~";
    default: return "=";
  }
}

async function parseGcode(gcode: string): Promise<MoveSegment[]> {
  // Simple G-code parser for comparison
  const segments: MoveSegment[] = [];
  const lines = gcode.split("\n");

  let currentPos: [number, number, number] = [0, 0, 0];
  let currentFeed = 0;
  let isAbsolute = true;

  for (let lineNum = 0; lineNum < lines.length; lineNum++) {
    const line = lines[lineNum].trim().toUpperCase();
    if (!line || line.startsWith(";") || line.startsWith("(")) continue;

    // Parse modal commands
    if (line.includes("G90")) isAbsolute = true;
    if (line.includes("G91")) isAbsolute = false;

    // Parse move commands
    const g0Match = line.match(/G0\b/);
    const g1Match = line.match(/G1\b/);
    const g2Match = line.match(/G2\b/);
    const g3Match = line.match(/G3\b/);

    if (!g0Match && !g1Match && !g2Match && !g3Match) continue;

    // Parse coordinates
    const xMatch = line.match(/X([+-]?\d*\.?\d+)/);
    const yMatch = line.match(/Y([+-]?\d*\.?\d+)/);
    const zMatch = line.match(/Z([+-]?\d*\.?\d+)/);
    const fMatch = line.match(/F(\d*\.?\d+)/);

    if (fMatch) currentFeed = parseFloat(fMatch[1]);

    const newX = xMatch ? parseFloat(xMatch[1]) : (isAbsolute ? currentPos[0] : 0);
    const newY = yMatch ? parseFloat(yMatch[1]) : (isAbsolute ? currentPos[1] : 0);
    const newZ = zMatch ? parseFloat(zMatch[1]) : (isAbsolute ? currentPos[2] : 0);

    const toPos: [number, number, number] = isAbsolute
      ? [newX, newY, newZ]
      : [currentPos[0] + newX, currentPos[1] + newY, currentPos[2] + newZ];

    const dist = Math.sqrt(
      (toPos[0] - currentPos[0]) ** 2 +
      (toPos[1] - currentPos[1]) ** 2 +
      (toPos[2] - currentPos[2]) ** 2
    );

    const type = g0Match ? "rapid" : g2Match ? "arc_cw" : g3Match ? "arc_ccw" : "linear";
    const feed = type === "rapid" ? 10000 : currentFeed;
    const duration = feed > 0 ? (dist / feed) * 60000 : 0;

    segments.push({
      type,
      from_pos: [...currentPos] as [number, number, number],
      to_pos: toPos,
      feed,
      duration_ms: duration,
      line_number: lineNum + 1,
      line_text: lines[lineNum].trim(),
    });

    currentPos = toPos;
  }

  return segments;
}

async function handleFileSelect(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  const gcode = await file.text();
  await runComparison(gcode);
  input.value = "";
}

function handleDrop(event: DragEvent): void {
  const file = event.dataTransfer?.files[0];
  if (!file) return;

  file.text().then(runComparison);
}

async function compareWithPasted(): Promise<void> {
  if (!pastedGcode.value.trim()) return;
  await runComparison(pastedGcode.value);
}

async function runComparison(gcode: string): Promise<void> {
  const segments = await parseGcode(gcode);
  compareSegments.value = segments;

  comparisonResult.value = compareToolpaths(props.baseSegments, segments);
  emit("compare-segments", segments);
}

function toggleOverlay(): void {
  overlayEnabled.value = !overlayEnabled.value;
  emit("overlay-toggle", overlayEnabled.value);
}

function reset(): void {
  comparisonResult.value = null;
  compareSegments.value = [];
  pastedGcode.value = "";
  overlayEnabled.value = false;
  emit("overlay-toggle", false);
}
</script>

<style scoped>
.toolpath-compare-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
  font-size: 12px;
}

/* Header */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: linear-gradient(135deg, #7b2d8e, #5a2d82);
  color: white;
}

.panel-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
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

/* Upload Section */
.upload-section {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.upload-hint {
  margin: 0;
  color: #888;
  font-size: 12px;
  text-align: center;
}

.upload-area {
  border: 2px dashed #3a3a5c;
  border-radius: 8px;
  padding: 24px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;
}

.upload-area:hover {
  border-color: #7b2d8e;
  background: rgba(123, 45, 142, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.upload-icon {
  font-size: 32px;
}

.upload-text {
  color: #aaa;
}

.upload-or {
  color: #666;
  font-size: 11px;
}

.upload-btn {
  padding: 8px 16px;
  background: #7b2d8e;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.upload-btn:hover {
  background: #9b3dae;
}

/* Paste Section */
.paste-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.paste-label {
  color: #666;
  font-size: 11px;
}

.paste-input {
  width: 100%;
  padding: 8px;
  background: #252538;
  border: 1px solid #3a3a5c;
  border-radius: 4px;
  color: #ccc;
  font-family: monospace;
  font-size: 11px;
  resize: vertical;
}

.paste-input:focus {
  outline: none;
  border-color: #7b2d8e;
}

.compare-btn {
  align-self: flex-end;
  padding: 8px 20px;
  background: #7b2d8e;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 12px;
}

.compare-btn:disabled {
  background: #3a3a5c;
  cursor: not-allowed;
}

/* Results Section */
.results-section {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
}

/* Summary Banner */
.summary-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 8px;
  font-weight: 500;
}

.summary-banner.improved {
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid #2ecc71;
  color: #2ecc71;
}

.summary-banner.degraded {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid #e74c3c;
  color: #e74c3c;
}

.summary-banner.similar {
  background: rgba(243, 156, 18, 0.15);
  border: 1px solid #f39c12;
  color: #f39c12;
}

.summary-icon {
  font-size: 18px;
}

.summary-text {
  flex: 1;
  font-size: 12px;
}

/* Stats Grid */
.stats-grid {
  background: #252538;
  border-radius: 8px;
  overflow: hidden;
}

.stats-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 8px 12px;
  background: #1a1a2e;
  font-size: 10px;
  font-weight: 600;
  color: #666;
  text-transform: uppercase;
}

.stats-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 8px 12px;
  border-bottom: 1px solid #1a1a2e;
  font-size: 11px;
}

.stats-row:last-child {
  border-bottom: none;
}

.stats-row.improved {
  background: rgba(46, 204, 113, 0.05);
}

.stat-field {
  color: #888;
}

.stat-base,
.stat-compare {
  color: #ccc;
  font-family: monospace;
}

.stat-diff {
  font-family: monospace;
  font-weight: 600;
}

.stat-diff.positive {
  color: #2ecc71;
}

.stat-diff.negative {
  color: #e74c3c;
}

/* Changes Summary */
.changes-summary {
  background: #252538;
  border-radius: 8px;
  padding: 12px;
}

.changes-summary h4 {
  margin: 0 0 10px 0;
  font-size: 12px;
  font-weight: 600;
  color: #aaa;
}

.changes-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.chip.same {
  background: #1a2a1a;
  color: #2ecc71;
}

.chip.modified {
  background: #2a2a1a;
  color: #f39c12;
}

.chip.added {
  background: #1a2a3a;
  color: #3498db;
}

.chip.removed {
  background: #2a1a1a;
  color: #e74c3c;
}

/* Diff Section */
.diff-section {
  background: #252538;
  border-radius: 8px;
  overflow: hidden;
}

.diff-toggle {
  width: 100%;
  padding: 10px 12px;
  background: none;
  border: none;
  color: #888;
  font-size: 11px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
}

.diff-toggle:hover {
  background: rgba(255, 255, 255, 0.05);
}

.diff-list {
  list-style: none;
  margin: 0;
  padding: 0;
  max-height: 200px;
  overflow-y: auto;
  border-top: 1px solid #1a1a2e;
}

.diff-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-bottom: 1px solid #1a1a2e;
  font-size: 11px;
}

.diff-item:last-child {
  border-bottom: none;
}

.diff-item.added {
  background: rgba(52, 152, 219, 0.1);
}

.diff-item.removed {
  background: rgba(231, 76, 60, 0.1);
}

.diff-item.modified {
  background: rgba(243, 156, 18, 0.1);
}

.diff-badge {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  font-weight: 700;
  font-size: 12px;
}

.diff-item.added .diff-badge {
  background: #3498db;
  color: white;
}

.diff-item.removed .diff-badge {
  background: #e74c3c;
  color: white;
}

.diff-item.modified .diff-badge {
  background: #f39c12;
  color: white;
}

.diff-index {
  color: #666;
  font-family: monospace;
  min-width: 40px;
}

.diff-desc {
  flex: 1;
  color: #aaa;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.diff-more {
  padding: 8px 12px;
  color: #666;
  font-style: italic;
  text-align: center;
}

/* Actions Bar */
.actions-bar {
  display: flex;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #2a2a4a;
  margin-top: auto;
}

.action-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  transition: background 0.2s;
}

.action-btn.secondary {
  background: #3a3a5c;
  color: #aaa;
}

.action-btn.secondary:hover {
  background: #4a4a6c;
}

.action-btn.primary {
  background: #7b2d8e;
  color: white;
}

.action-btn.primary:hover {
  background: #9b3dae;
}

.action-btn.primary.active {
  background: #3498db;
}

/* Scrollbar */
.results-section::-webkit-scrollbar,
.diff-list::-webkit-scrollbar {
  width: 6px;
}

.results-section::-webkit-scrollbar-track,
.diff-list::-webkit-scrollbar-track {
  background: #1a1a2e;
}

.results-section::-webkit-scrollbar-thumb,
.diff-list::-webkit-scrollbar-thumb {
  background: #3a3a5a;
  border-radius: 3px;
}

.results-section::-webkit-scrollbar-thumb:hover,
.diff-list::-webkit-scrollbar-thumb:hover {
  background: #4a4a6a;
}
</style>
