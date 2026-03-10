<script setup lang="ts">
/**
 * GcodeViewer — P5 G-code Source Viewer
 *
 * Displays G-code source with line highlighting for selected segments.
 * Syncs with ToolpathPlayer selection state.
 *
 * Features:
 * - Syntax highlighting (G/M codes, comments, coordinates)
 * - Selected line highlighting
 * - Auto-scroll to selected line
 * - Click to select segment
 * - Line numbers
 */

import { ref, computed, watch, onMounted, nextTick } from "vue";
import { useToolpathPlayerStore } from "@/stores/useToolpathPlayerStore";

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

const store = useToolpathPlayerStore();

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface Props {
  /** Max height before scrolling */
  maxHeight?: string;
  /** Show line numbers */
  showLineNumbers?: boolean;
  /** Auto-scroll to selected line */
  autoScroll?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  maxHeight: "300px",
  showLineNumbers: true,
  autoScroll: true,
});

// ---------------------------------------------------------------------------
// Refs
// ---------------------------------------------------------------------------

const containerRef = ref<HTMLDivElement | null>(null);
const lineRefs = ref<Map<number, HTMLDivElement>>(new Map());

// ---------------------------------------------------------------------------
// Computed
// ---------------------------------------------------------------------------

const gcodeLines = computed(() => {
  if (!store.sourceGcode) return [];
  return store.sourceGcode.split("\n");
});

const selectedLineNumber = computed(() => {
  return store.selectedGcodeLine?.lineNumber ?? null;
});

// Build segment index -> line number map from segments
const lineToSegmentMap = computed(() => {
  const map = new Map<number, number>();
  for (let i = 0; i < store.segments.length; i++) {
    const seg = store.segments[i] as { line_number?: number };
    if (seg.line_number !== undefined) {
      map.set(seg.line_number, i);
    }
  }
  return map;
});

// ---------------------------------------------------------------------------
// Syntax Highlighting
// ---------------------------------------------------------------------------

function highlightLine(line: string): string {
  // Comments (parentheses or semicolon)
  line = line.replace(/(\(.*?\))/g, '<span class="comment">$1</span>');
  line = line.replace(/(;.*)$/g, '<span class="comment">$1</span>');

  // G-codes
  line = line.replace(/\b(G\d+(?:\.\d+)?)/gi, '<span class="gcode">$1</span>');

  // M-codes
  line = line.replace(/\b(M\d+)/gi, '<span class="mcode">$1</span>');

  // Coordinates (X, Y, Z, I, J, K)
  line = line.replace(/\b([XYZIJK])(-?\d+\.?\d*)/gi, '<span class="coord">$1</span><span class="value">$2</span>');

  // Feed rate
  line = line.replace(/\b(F)(\d+\.?\d*)/gi, '<span class="feed">$1</span><span class="value">$2</span>');

  // Spindle speed
  line = line.replace(/\b(S)(\d+)/gi, '<span class="spindle">$1</span><span class="value">$2</span>');

  // Tool number
  line = line.replace(/\b(T)(\d+)/gi, '<span class="tool">$1</span><span class="value">$2</span>');

  // Line numbers (N)
  line = line.replace(/^(N\d+)/gi, '<span class="linenum">$1</span>');

  return line;
}

// ---------------------------------------------------------------------------
// Methods
// ---------------------------------------------------------------------------

function onLineClick(lineNum: number): void {
  // Find segment index for this line
  const segIdx = lineToSegmentMap.value.get(lineNum);
  if (segIdx !== undefined) {
    store.selectSegment(segIdx);
  }
}

function scrollToLine(lineNum: number): void {
  if (!props.autoScroll || !containerRef.value) return;

  nextTick(() => {
    const lineEl = lineRefs.value.get(lineNum);
    if (lineEl && containerRef.value) {
      lineEl.scrollIntoView({
        behavior: "smooth",
        block: "center",
      });
    }
  });
}

function setLineRef(lineNum: number, el: HTMLDivElement | null): void {
  if (el) {
    lineRefs.value.set(lineNum, el);
  } else {
    lineRefs.value.delete(lineNum);
  }
}

// ---------------------------------------------------------------------------
// Watchers
// ---------------------------------------------------------------------------

watch(selectedLineNumber, (lineNum) => {
  if (lineNum !== null) {
    scrollToLine(lineNum);
  }
});
</script>

<template>
  <div
    ref="containerRef"
    class="gcode-viewer"
    :style="{ maxHeight: maxHeight }"
  >
    <div
      v-if="gcodeLines.length === 0"
      class="empty-state"
    >
      No G-code loaded
    </div>
    <div
      v-else
      class="gcode-content"
    >
      <div
        v-for="(line, index) in gcodeLines"
        :key="index"
        :ref="(el) => setLineRef(index + 1, el as HTMLDivElement)"
        class="gcode-line"
        :class="{
          selected: selectedLineNumber === index + 1,
          clickable: lineToSegmentMap.has(index + 1),
        }"
        @click="onLineClick(index + 1)"
      >
        <span
          v-if="showLineNumbers"
          class="line-number"
        >
          {{ index + 1 }}
        </span>
        <span
          class="line-text"
          v-html="highlightLine(line)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.gcode-viewer {
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-size: 12px;
  background: #13131f;
  border: 1px solid #2a2a4a;
  border-radius: 4px;
  overflow: auto;
}

.empty-state {
  padding: 20px;
  text-align: center;
  color: #666;
}

.gcode-content {
  padding: 8px 0;
}

.gcode-line {
  display: flex;
  align-items: flex-start;
  padding: 2px 12px;
  line-height: 1.5;
  transition: background 0.1s;
}

.gcode-line:hover {
  background: rgba(74, 144, 217, 0.1);
}

.gcode-line.clickable {
  cursor: pointer;
}

.gcode-line.selected {
  background: rgba(255, 215, 0, 0.2);
  border-left: 3px solid #ffd700;
  padding-left: 9px;
}

.line-number {
  min-width: 40px;
  padding-right: 12px;
  color: #555;
  text-align: right;
  user-select: none;
}

.line-text {
  flex: 1;
  color: #ccc;
  white-space: pre;
}

/* Syntax highlighting */
.gcode-viewer :deep(.gcode) {
  color: #4a90d9;
  font-weight: 600;
}

.gcode-viewer :deep(.mcode) {
  color: #e74c3c;
  font-weight: 600;
}

.gcode-viewer :deep(.coord) {
  color: #9b59b6;
}

.gcode-viewer :deep(.value) {
  color: #2ecc71;
}

.gcode-viewer :deep(.feed) {
  color: #e67e22;
}

.gcode-viewer :deep(.spindle) {
  color: #e74c3c;
}

.gcode-viewer :deep(.tool) {
  color: #f1c40f;
}

.gcode-viewer :deep(.comment) {
  color: #666;
  font-style: italic;
}

.gcode-viewer :deep(.linenum) {
  color: #666;
}
</style>
