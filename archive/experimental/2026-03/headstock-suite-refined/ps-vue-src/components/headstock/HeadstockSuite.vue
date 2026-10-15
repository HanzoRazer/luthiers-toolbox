<template>
  <div class="ps-suite">

    <!-- Shell nav -->
    <nav class="ps-nav">
      <span class="ps-brand">Production<em>Shop</em></span>

      <div class="ps-tabs">
        <button
          v-for="tab in TABS"
          :key="tab.id"
          class="ps-tab"
          :class="{ on: store.activeTab === tab.id }"
          @click="store.setTab(tab.id)"
        >
          <span class="tab-dot" />
          {{ tab.label }}
          <span v-if="tab.pro" class="pro-badge">PRO</span>
        </button>
      </div>

      <div class="ps-nav-sep" />
      <div class="ps-nav-spacer" />

      <!-- Per-tab context actions -->
      <template v-if="store.activeTab === 'workspace'">
        <input ref="wFileInput" type="file" accept=".svg,.dxf" style="display:none" @change="onWFileChange" />
        <button class="ps-nbtn" @click="wFileInput?.click()">↑ Import</button>
        <button class="ps-nbtn" @click="emit('undo')">← Undo</button>
        <button class="ps-nbtn" @click="emit('clear')">Clear</button>
        <button class="ps-nbtn go" @click="emit('export')">↓ Export SVG</button>
      </template>

      <template v-else-if="store.activeTab === 'import'">
        <input ref="iFileInput" type="file" accept=".svg,.dxf" style="display:none" @change="onIFileChange" />
        <button class="ps-nbtn" @click="iFileInput?.click()">↑ Load file</button>
        <button class="ps-nbtn" @click="emit('reparse')">↻ Re-parse</button>
      </template>

      <template v-else-if="store.activeTab === 'parametric'">
        <button class="ps-nbtn" @click="emit('randomize')">⚄ Randomize</button>
        <button class="ps-nbtn" :class="{ on: store.showOverlay }" @click="store.showOverlay = !store.showOverlay">
          Corpus overlay
        </button>
        <button class="ps-nbtn go" @click="emit('p3export')">↓ Export SVG</button>
      </template>
    </nav>

    <!-- Panels -->
    <div class="ps-panels">
      <WorkspacePanel  v-show="store.activeTab === 'workspace'"  @loaded="onWorkspaceLoaded" />
      <ImportPanel     v-show="store.activeTab === 'import'"     @loaded="onImportLoaded" />
      <ParametricPanel v-show="store.activeTab === 'parametric'" @loaded="onParametricLoaded" />
    </div>

    <!-- Status bar -->
    <footer class="ps-status">
      <span class="st-chip">{{ statusMode }}</span>
      <span class="st-chip">{{ statusA }}</span>
      <span class="st-chip">{{ statusB }}</span>
      <span class="st-chip st-hint">{{ statusHint }}</span>
    </footer>

    <!-- Handoff toast -->
    <Transition name="toast">
      <div v-if="toastMsg" class="ps-toast">{{ toastMsg }}</div>
    </Transition>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, provide } from 'vue'
import { useHeadstockStore } from '@/stores/headstock'
import WorkspacePanel  from './workspace/WorkspacePanel.vue'
import ImportPanel     from './import/ImportPanel.vue'
import ParametricPanel from './parametric/ParametricPanel.vue'

// ─── Store ────────────────────────────────────────────────────────────────────
const store = useHeadstockStore()

// ─── Toast ────────────────────────────────────────────────────────────────────
const toastMsg = ref('')
let toastTimer: ReturnType<typeof setTimeout> | null = null

function toast(msg: string) {
  toastMsg.value = msg
  if (toastTimer) clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toastMsg.value = '' }, 2800)
}

provide('toast', toast)

// ─── Events (forwarded from nav buttons to active panel) ─────────────────────
const emit = defineEmits<{
  undo:      []
  clear:     []
  export:    []
  reparse:   []
  randomize: []
  p3export:  []
  fileImport:[file: File, target: 'workspace' | 'import']
}>()

// ─── File inputs ──────────────────────────────────────────────────────────────
const wFileInput = ref<HTMLInputElement | null>(null)
const iFileInput = ref<HTMLInputElement | null>(null)

function onWFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) emit('fileImport', file, 'workspace')
  ;(e.target as HTMLInputElement).value = ''
}
function onIFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) emit('fileImport', file, 'import')
  ;(e.target as HTMLInputElement).value = ''
}

// ─── Panel ready callbacks ────────────────────────────────────────────────────
function onWorkspaceLoaded()  { /* canvas ready */ }
function onImportLoaded()     { /* canvas ready */ }
function onParametricLoaded() { /* canvas ready */ }

// ─── Status bar ───────────────────────────────────────────────────────────────
const TABS = [
  { id: 'workspace'  as const, label: 'Workspace',  pro: false },
  { id: 'import'     as const, label: 'Import',      pro: false },
  { id: 'parametric' as const, label: 'Parametric',  pro: true  },
]

const statusMode = computed(() => ({
  workspace:  'Workspace',
  import:     'Import pipeline',
  parametric: 'Parametric designer',
}[store.activeTab]))

const statusA = ref('')
const statusB = ref('')
const statusHint = ref('Workspace · drop SVG/DXF to import · Parametric = Pro tier')

provide('setStatusA', (v: string) => { statusA.value = v })
provide('setStatusB', (v: string) => { statusB.value = v })
</script>

<style scoped>
.ps-suite {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--ps-bg);
  color: var(--ps-text);
  font-family: var(--ps-mono);
  font-size: 11px;
  overflow: hidden;
}

/* Nav */
.ps-nav {
  display: flex;
  align-items: center;
  height: 40px;
  flex-shrink: 0;
  background: var(--ps-surface1);
  border-bottom: 1px solid var(--ps-border);
  padding: 0 14px;
  gap: 0;
}
.ps-brand {
  font-family: var(--ps-serif);
  font-size: 14px;
  font-style: italic;
  color: var(--ps-text-dim);
  white-space: nowrap;
  margin-right: 14px;
}
.ps-brand em { color: var(--ps-brass2); font-style: normal; }
.ps-tabs { display: flex; align-items: stretch; }
.ps-tab {
  display: flex; align-items: center; gap: 6px;
  padding: 0 13px;
  border: none; background: none;
  border-bottom: 2px solid transparent;
  font-family: var(--ps-mono); font-size: 10px; letter-spacing: .6px;
  text-transform: uppercase; color: var(--ps-dim); cursor: pointer;
  transition: color .12s, border-color .12s; white-space: nowrap;
}
.ps-tab:hover { color: var(--ps-text); }
.ps-tab.on { color: var(--ps-brass2); border-bottom-color: var(--ps-brass); }
.tab-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--ps-border); }
.ps-tab.on .tab-dot { background: var(--ps-brass); }
.pro-badge {
  padding: 1px 5px; background: rgba(184,150,46,.1);
  border: 1px solid var(--ps-brass3); border-radius: 2px;
  font-size: 7px; letter-spacing: .8px; color: var(--ps-brass);
}
.ps-nav-sep { width: 1px; height: 20px; background: var(--ps-border); margin: 0 8px; }
.ps-nav-spacer { flex: 1; }
.ps-nbtn {
  margin: 6px 2px; padding: 0 8px; height: 26px;
  background: none; border: 1px solid transparent; border-radius: 2px;
  color: var(--ps-dim); font-family: var(--ps-mono); font-size: 9px;
  letter-spacing: .6px; text-transform: uppercase; cursor: pointer;
  transition: all .12s; white-space: nowrap;
}
.ps-nbtn:hover { border-color: var(--ps-border); color: var(--ps-text); }
.ps-nbtn.go { border-color: var(--ps-brass3); color: var(--ps-brass2); }
.ps-nbtn.go:hover { background: var(--ps-brass3); color: var(--ps-bg); }
.ps-nbtn.on { background: var(--ps-surface2); border-color: var(--ps-brass3); color: var(--ps-brass2); }

/* Panels */
.ps-panels { flex: 1; position: relative; overflow: hidden; }

/* Status */
.ps-status {
  display: flex; align-items: center; height: 26px; flex-shrink: 0;
  background: var(--ps-surface1); border-top: 1px solid var(--ps-border);
  padding: 0 12px; gap: 12px;
}
.st-chip { font-size: 9px; color: var(--ps-dim); letter-spacing: .3px; }
.st-hint { margin-left: auto; color: var(--ps-dim3); }

/* Toast */
.ps-toast {
  position: fixed; top: 48px; right: 18px; z-index: 9999;
  background: var(--ps-surface1); border: 1px solid var(--ps-brass3);
  border-radius: 4px; padding: 9px 14px;
  font-size: 10px; color: var(--ps-brass2); pointer-events: none;
}
.toast-enter-active, .toast-leave-active { transition: opacity .2s, transform .2s; }
.toast-enter-from { opacity: 0; transform: translateY(-8px); }
.toast-leave-to   { opacity: 0; transform: translateY(-4px); }
</style>
