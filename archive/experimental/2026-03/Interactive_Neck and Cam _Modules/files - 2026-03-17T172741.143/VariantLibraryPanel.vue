<script setup lang="ts">
/**
 * VariantLibraryPanel.vue
 *
 * Mounted in WorkspaceView right panel (or as a modal overlay).
 * Reads from useVariantStore and reads current snapshots from
 * headstock + neck stores via props.
 *
 * Usage in WorkspaceView:
 *   import VariantLibraryPanel from '@/components/VariantLibraryPanel.vue'
 *   <VariantLibraryPanel
 *     :headstock-payload="headstockStore.exportPayload"
 *     :neck-payload="neckStore?.fullExportPayload ?? null"
 *     @load="onLoadVariant"
 *   />
 */
import { ref, computed } from 'vue'
import {
  useVariantStore,
  STATUS_LABELS, STATUS_COLORS, STATUS_ORDER,
  type Variant, type VariantStatus,
} from '@/stores/variants'

const props = defineProps<{
  headstockPayload: Record<string, any> | null
  neckPayload:      Record<string, any> | null
}>()

const emit = defineEmits<{
  load: [variant: Variant]
  toast: [msg: string]
}>()

const store = useVariantStore()

const newName    = ref('')
const filterStatus = ref<VariantStatus | 'all'>('all')
const editingId  = ref<string | null>(null)
const editNotes  = ref('')

// ── Filtered list ─────────────────────────────────────────────────────────
const filtered = computed(() => {
  if (filterStatus.value === 'all') return store.variants
  return store.variants.filter(v => v.status === filterStatus.value)
})

// ── Save current workspace as new variant ─────────────────────────────────
function saveNew() {
  const name = newName.value.trim() || `Variant ${store.variants.length + 1}`
  store.createVariant(name, props.headstockPayload, props.neckPayload)
  newName.value = ''
  emit('toast', `Saved variant: ${name}`)
}

// ── Refresh snapshot on active variant ───────────────────────────────────
function refreshActive() {
  if (!store.activeId) return
  store.refreshSnapshot(store.activeId, props.headstockPayload, props.neckPayload)
  emit('toast', 'Variant snapshot updated')
}

// ── Load variant into workspace ───────────────────────────────────────────
function load(v: Variant) {
  store.activeId = v.id
  emit('load', v)
}

// ── Status badge click cycles forward ────────────────────────────────────
function cycleStatus(v: Variant) {
  store.advanceStatus(v.id)
}

// ── Notes editing ─────────────────────────────────────────────────────────
function startEdit(v: Variant) {
  editingId.value = v.id
  editNotes.value = v.notes
}
function saveEdit(id: string) {
  store.updateVariant(id, { notes: editNotes.value })
  editingId.value = null
}

// ── Export / import JSON ──────────────────────────────────────────────────
function exportAll() {
  const json = store.exportJSON()
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([json], { type: 'application/json' })),
    download: 'ps-variants.json',
  })
  a.click()
  emit('toast', `Exported ${store.variants.length} variants`)
}

function importFile() {
  const input = document.createElement('input')
  input.type = 'file'; input.accept = '.json'
  input.onchange = () => {
    const file = input.files?.[0]; if (!file) return
    file.text().then(text => {
      const n = store.importJSON(text)
      emit('toast', n > 0 ? `Imported ${n} variants` : 'No new variants found')
    })
  }
  input.click()
}
</script>

<template>
  <div class="vlib">

    <!-- Save new -->
    <div class="sec">
      <div class="sec-lbl">Save current workspace</div>
      <div style="display:flex;gap:4px">
        <input class="vname-input" v-model="newName" placeholder="Variant name…"
          @keydown.enter="saveNew" />
        <button class="sbtn go" style="flex-shrink:0" @click="saveNew">Save</button>
      </div>
      <button v-if="store.activeId" class="sbtn" style="width:100%;margin-top:4px;font-size:8px"
        @click="refreshActive">
        ↻ Refresh snapshot on «{{ store.active?.name }}»
      </button>
    </div>

    <!-- Status counts -->
    <div class="sec status-counts">
      <div
        v-for="s in ['all', ...Object.keys(STATUS_LABELS)] as (VariantStatus | 'all')[]"
        :key="s"
        class="status-pill"
        :class="{ active: filterStatus === s }"
        :style="s !== 'all' ? { '--sc': STATUS_COLORS[s as VariantStatus] } : {}"
        @click="filterStatus = s"
      >
        {{ s === 'all' ? 'All' : STATUS_LABELS[s as VariantStatus] }}
        <span class="sc-count">{{ s === 'all' ? store.variants.length : store.counts[s as VariantStatus] }}</span>
      </div>
    </div>

    <!-- Variant list -->
    <div class="vlist">
      <div v-if="!filtered.length" class="no-variants">
        No variants{{ filterStatus !== 'all' ? ` with status "${filterStatus}"` : '' }}.
      </div>

      <div
        v-for="v in filtered" :key="v.id"
        class="vcard"
        :class="{ active: store.activeId === v.id }"
      >
        <!-- Header row -->
        <div class="vcard-head">
          <span class="vname" @click="load(v)">{{ v.name }}</span>
          <span
            class="vstatus"
            :style="{ background: STATUS_COLORS[v.status] + '22', color: STATUS_COLORS[v.status], borderColor: STATUS_COLORS[v.status] }"
            @click="cycleStatus(v)"
            title="Click to advance status"
          >{{ STATUS_LABELS[v.status] }}</span>
        </div>

        <!-- Metadata row -->
        <div class="vmeta">
          <span>{{ new Date(v.createdAt).toLocaleDateString() }}</span>
          <span v-if="v.orderId" class="vorder">Order {{ v.orderId }}</span>
          <span v-if="v.materialCostEst > 0" class="vcost">${{ v.materialCostEst.toFixed(2) }}</span>
        </div>

        <!-- Notes -->
        <template v-if="editingId === v.id">
          <textarea class="vnotes-edit" v-model="editNotes" rows="2" @blur="saveEdit(v.id)" @keydown.enter.ctrl="saveEdit(v.id)" />
        </template>
        <div v-else-if="v.notes" class="vnotes" @click="startEdit(v)">{{ v.notes }}</div>

        <!-- Actions -->
        <div class="vactions">
          <button class="sbtn" style="font-size:7px" @click="load(v)">↑ Load</button>
          <button class="sbtn" style="font-size:7px" @click="startEdit(v)">✎ Notes</button>
          <button class="sbtn" style="font-size:7px" @click="store.duplicateVariant(v.id)">⧉ Dupe</button>
          <button class="sbtn" style="font-size:7px;color:var(--red)" @click="store.deleteVariant(v.id)">✕</button>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="vfooter">
      <button class="sbtn" style="font-size:8px" @click="exportAll">↓ Export JSON</button>
      <button class="sbtn" style="font-size:8px" @click="importFile">↑ Import JSON</button>
    </div>

  </div>
</template>

<style scoped>
.vlib       { display:flex; flex-direction:column; height:100%; overflow:hidden; }
.sec        { padding:8px 12px 6px; border-bottom:1px solid var(--w3); flex-shrink:0; }
.sec-lbl    { font-size:8px; letter-spacing:1.4px; text-transform:uppercase; color:var(--br3); margin-bottom:6px; }

.vname-input {
  flex:1; padding:4px 7px; background:var(--w2); border:1px solid var(--w3);
  border-radius:3px; font-family:var(--mono); font-size:9px; color:var(--v1);
  outline:none;
}
.vname-input:focus { border-color:var(--br3); }

/* Status filter pills */
.status-counts { display:flex; flex-wrap:wrap; gap:4px; padding:7px 12px; }
.status-pill {
  padding:2px 7px; border-radius:10px; font-size:8px; cursor:pointer;
  background:var(--w2); color:var(--dim); border:1px solid var(--w3);
  transition:all .1s;
}
.status-pill.active { background:rgba(184,150,46,.1); border-color:var(--br3); color:var(--br2); }
.status-pill[style] { border-color:var(--sc) !important; color:var(--sc) !important; }
.status-pill[style].active { background:color-mix(in srgb, var(--sc) 12%, transparent); }
.sc-count { font-size:7px; opacity:.7; margin-left:3px; }

/* List */
.vlist { flex:1; overflow-y:auto; padding:6px 10px; }
.no-variants { font-size:9px; color:var(--dim3); text-align:center; padding:20px 0; font-style:italic; }

.vcard {
  background:var(--w2); border:1px solid var(--w3); border-radius:4px;
  padding:8px 10px; margin-bottom:6px; transition:border-color .1s;
}
.vcard.active { border-color:var(--br3); background:rgba(184,150,46,.06); }

.vcard-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.vname { font-size:10px; color:var(--v1); cursor:pointer; font-weight:500; }
.vname:hover { color:var(--br2); }
.vstatus {
  font-size:7px; padding:1px 6px; border-radius:2px; border:1px solid;
  cursor:pointer; letter-spacing:.4px; flex-shrink:0;
  transition:opacity .1s;
}
.vstatus:hover { opacity:.8; }

.vmeta { display:flex; gap:8px; font-size:8px; color:var(--dim3); margin-bottom:3px; }
.vorder { color:var(--blue2); }
.vcost  { color:var(--green2); }

.vnotes {
  font-size:8px; color:var(--dim); line-height:1.5; cursor:text;
  padding:3px 0; border-bottom:1px dashed var(--w3); margin-bottom:4px;
  white-space:pre-wrap;
}
.vnotes-edit {
  width:100%; background:var(--w1); border:1px solid var(--br3); border-radius:2px;
  font-size:8px; color:var(--v1); font-family:var(--mono); padding:4px;
  resize:vertical; margin-bottom:4px;
}

.vactions { display:flex; gap:3px; margin-top:4px; }

/* Footer */
.vfooter {
  border-top:1px solid var(--w3); padding:7px 12px;
  display:flex; gap:6px; flex-shrink:0;
}
</style>
