<script setup lang="ts">
/**
 * GcodePreviewPanel.vue
 *
 * Read-only G-code preview with:
 *  - Syntax highlighting (motion codes, comments, tool changes, safety)
 *  - Line count + cycle time display
 *  - Download .nc button
 *  - Copy to clipboard
 */

import { ref, computed } from 'vue'

const props = defineProps<{
  gcode:           string
  filename?:       string
  cycleTimeSecs?:  number
  opName?:         string
}>()

const emit = defineEmits<{ toast: [msg: string] }>()

// ── Syntax highlighter ────────────────────────────────────────────────────────
// Returns HTML string with <span class="..."> wrappers.
function highlight(line: string): string {
  if (!line.trim()) return '&nbsp;'

  // Comments
  if (line.trim().startsWith('(')) {
    // Tool change comments get special treatment
    if (/tool change/i.test(line))
      return `<span class="gc-tc">${esc(line)}</span>`
    return `<span class="gc-cmt">${esc(line)}</span>`
  }

  // Segment headers
  if (/^=+$/.test(line.trim()))
    return `<span class="gc-cmt">${esc(line)}</span>`

  let h = esc(line)
  // Motion codes
  h = h.replace(/\b(G0|G00)\b/g,  '<span class="gc-rapid">$1</span>')
  h = h.replace(/\b(G1|G01)\b/g,  '<span class="gc-feed">$1</span>')
  h = h.replace(/\b(G2|G02|G3|G03)\b/g, '<span class="gc-arc">$1</span>')
  h = h.replace(/\b(G4|G04)\b/g,  '<span class="gc-dwell">$1</span>')
  h = h.replace(/\b(G2[01]|G4[09]|G9[08]|G17|G54|G80|G64)\b/g, '<span class="gc-mod">$1</span>')
  // Spindle / tool
  h = h.replace(/\b(M3|M5|M6|M30)\b/g, '<span class="gc-m">$1</span>')
  h = h.replace(/\b(M1|M0)\b/g,   '<span class="gc-pause">$1</span>')  // operator pause
  h = h.replace(/\b(T\d+)\b/g,    '<span class="gc-tool">$1</span>')
  h = h.replace(/\b(G43)\b/g,     '<span class="gc-tlc">G43</span>')   // tool length comp
  // Coordinates
  h = h.replace(/([XYZIJKF])(-?[\d.]+)/g, '<span class="gc-coord">$1</span><span class="gc-num">$2</span>')
  // S (spindle speed)
  h = h.replace(/\b(S\d+)/g,      '<span class="gc-s">$1</span>')
  return h
}

function esc(s: string): string {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
}

const lines = computed(() => props.gcode ? props.gcode.split('\n') : [])

const cycleLabel = computed(() => {
  const s = props.cycleTimeSecs
  if (!s || s <= 0) return null
  if (s < 60) return `${s.toFixed(0)}s`
  const m = Math.floor(s / 60)
  const sec = Math.round(s % 60)
  return `${m}m ${sec}s`
})

// ── Download ──────────────────────────────────────────────────────────────────
function download() {
  if (!props.gcode) return
  const name = props.filename || `${props.opName || 'neck'}.nc`
  const blob = new Blob([props.gcode], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href = url; a.download = name; a.click()
  URL.revokeObjectURL(url)
  emit('toast', `Downloaded ${name}`)
}

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(props.gcode)
    emit('toast', 'G-code copied to clipboard')
  } catch {
    emit('toast', 'Copy failed — select text manually')
  }
}
</script>

<template>
  <div class="gp-wrap">
    <!-- Header -->
    <div class="gp-header">
      <div class="gp-title">
        <span class="gp-op">{{ opName || 'G-code' }}</span>
        <span class="gp-meta">{{ lines.length }} lines</span>
        <span v-if="cycleLabel" class="gp-meta">≈ {{ cycleLabel }}</span>
      </div>
      <div class="gp-actions" v-if="gcode">
        <button class="gp-btn" @click="copyToClipboard" title="Copy to clipboard">⎘</button>
        <button class="gp-btn dl" @click="download" title="Download .nc file">↓ .nc</button>
      </div>
    </div>

    <!-- Code area -->
    <div class="gp-code" v-if="gcode">
      <div v-for="(line, i) in lines" :key="i" class="gp-line">
        <span class="gp-ln">{{ i + 1 }}</span>
        <span class="gp-content" v-html="highlight(line)"></span>
      </div>
    </div>
    <div class="gp-empty" v-else>
      Generate G-code to preview
    </div>
  </div>
</template>

<style scoped>
.gp-wrap {
  display: flex; flex-direction: column;
  height: 100%; overflow: hidden;
  background: var(--w0);
}

.gp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 5px 10px; border-bottom: 1px solid var(--w3);
  background: var(--w1); flex-shrink: 0;
}
.gp-title { display: flex; align-items: center; gap: 8px; }
.gp-op    { font-family: var(--mono); font-size: 9px; color: var(--br2); letter-spacing: .6px; text-transform: uppercase; }
.gp-meta  { font-size: 8px; color: var(--dim3); }

.gp-actions { display: flex; gap: 4px; }
.gp-btn {
  padding: 2px 8px; background: none; border: 1px solid var(--w3);
  border-radius: 2px; font-size: 9px; color: var(--dim); cursor: pointer;
  font-family: var(--mono); transition: all .1s;
}
.gp-btn:hover { border-color: var(--w4); color: var(--v1); }
.gp-btn.dl    { border-color: var(--br3); color: var(--br2); }
.gp-btn.dl:hover { background: var(--br); color: #0f0d0a; }

.gp-code {
  flex: 1; overflow-y: auto; overflow-x: auto;
  padding: 6px 0; font-family: var(--mono);
}
.gp-line {
  display: flex; align-items: baseline;
  min-height: 16px; padding: 0 8px 0 0;
}
.gp-line:hover { background: rgba(255,255,255,.03); }
.gp-ln {
  flex-shrink: 0; width: 36px; text-align: right;
  font-size: 8px; color: var(--dim3); padding-right: 10px;
  user-select: none;
}
.gp-content { font-size: 9px; color: var(--dim); white-space: pre; }

.gp-empty {
  flex: 1; display: flex; align-items: center; justify-content: center;
  font-size: 9px; color: var(--dim3); font-family: var(--mono);
}

/* Syntax colours */
:deep(.gc-rapid)  { color: #5b8fa8; }   /* G0  blue — rapid */
:deep(.gc-feed)   { color: #90c080; }   /* G1  green — feed */
:deep(.gc-arc)    { color: #80c0a0; }   /* G2/3 teal — arc */
:deep(.gc-dwell)  { color: #a0a870; }   /* G4  olive — dwell */
:deep(.gc-mod)    { color: var(--dim); }
:deep(.gc-m)      { color: #c08050; }   /* M3/5/6/30 amber */
:deep(.gc-pause)  { color: var(--amber); font-weight: 600; } /* M1 — highlight operator pause */
:deep(.gc-tool)   { color: var(--br2); font-weight: 600; }   /* T1 etc */
:deep(.gc-tlc)    { color: var(--br); }                      /* G43 */
:deep(.gc-s)      { color: #a08060; }   /* Spindle speed */
:deep(.gc-coord)  { color: var(--dim); }
:deep(.gc-num)    { color: var(--v1); }
:deep(.gc-cmt)    { color: #5a5545; font-style: italic; }
:deep(.gc-tc)     { color: var(--br3); font-style: italic; } /* Tool change comments */
</style>
