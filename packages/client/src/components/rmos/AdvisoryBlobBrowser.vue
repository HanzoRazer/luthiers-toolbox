<template>
  <div class="panel">
    <div class="header">
      <div>
        <div class="title">
          Advisory Blob Browser
        </div>
        <div class="subtle">
          Run: <code>{{ runId }}</code>
        </div>
      </div>
      <div class="actions">
        <button
          class="btn"
          :disabled="!items.length"
          @click="downloadAllZip"
        >
          Download all (.zip)
        </button>
        <button
          class="btn secondary"
          @click="refresh"
        >
          Refresh
        </button>
      </div>
    </div>

    <div
      v-if="loading"
      class="subtle"
    >
      Loading...
    </div>
    <div
      v-else-if="error"
      class="error"
    >
      {{ error }}
    </div>
    <div
      v-else-if="!items.length"
      class="subtle"
    >
      No advisory blobs linked to this run.
    </div>

    <div
      v-else
      class="grid"
    >
      <div class="left">
        <table class="tbl">
          <thead>
            <tr>
              <th>Kind</th>
              <th>Title</th>
              <th>Filename</th>
              <th>MIME</th>
              <th>SHA</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="b in items"
              :key="b.advisory_id"
              :class="{ selected: selected?.advisory_id === b.advisory_id }"
              @click="select(b)"
            >
              <td><code>{{ b.kind ?? "advisory" }}</code></td>
              <td>{{ b.title ?? "" }}</td>
              <td>{{ b.filename ?? "" }}</td>
              <td class="subtle">
                {{ b.mime ?? "" }}
              </td>
              <td class="mono">
                {{ b.advisory_id.slice(0, 12) }}...
              </td>
              <td
                class="row-actions"
                @click.stop
              >
                <button
                  class="btn tiny"
                  @click="downloadOne(b)"
                >
                  Download
                </button>
                <button
                  v-if="isSvg(b)"
                  class="btn tiny secondary"
                  @click="checkAndPreview(b)"
                >
                  Preview
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="right">
        <div class="preview-header">
          <div class="title">
            Preview
          </div>
          <div
            v-if="selected"
            class="subtle"
          >
            <code>{{ selected.filename ?? selected.advisory_id.slice(0, 12) }}</code>
          </div>
        </div>

        <div
          v-if="!selected"
          class="subtle"
        >
          Select an SVG blob to preview.
        </div>
        <div
          v-else-if="!isSvg(selected)"
          class="subtle"
        >
          Preview available only for SVG blobs.
        </div>
        <div
          v-else-if="previewBlocked"
          class="preview-blocked"
        >
          <div class="blocked-icon">
            !
          </div>
          <div class="blocked-reason">
            {{ previewBlockedReason }}
          </div>
          <button
            class="btn"
            @click="downloadOne(selected)"
          >
            Download Instead
          </button>
        </div>

        <div
          v-else
          class="preview-box"
        >
          <!-- Use backend run-authorized SVG preview endpoint -->
          <object
            :data="svgPreviewUrl(selected)"
            type="image/svg+xml"
            class="svg-object"
          >
            <div class="subtle">SVG preview failed to load.</div>
          </object>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

type AdvisoryBlobRef = {
  advisory_id: string;
  kind?: string | null;
  title?: string | null;
  mime?: string | null;
  filename?: string | null;
};

type PreviewStatus = {
  run_id: string;
  advisory_id: string;
  ok: boolean;
  mime?: string | null;
  reason?: string | null;
  blocked_by?: string | null;
  action: string;
};

const props = defineProps<{ runId: string; apiBase?: string }>();
const apiBase = computed(() => props.apiBase ?? "/api");

const loading = ref(false);
const error = ref<string | null>(null);
const items = ref<AdvisoryBlobRef[]>([]);
const selected = ref<AdvisoryBlobRef | null>(null);
const previewBlocked = ref(false);
const previewBlockedReason = ref<string | null>(null);

function isSvg(b: AdvisoryBlobRef) {
  const m = (b.mime ?? "").toLowerCase();
  return m === "image/svg+xml" || m === "image/svg" || m === "text/svg+xml";
}

async function refresh() {
  if (!props.runId) return;
  loading.value = true;
  error.value = null;
  try {
    const url = `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/blobs`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to load advisory blobs (${res.status})`);
    const data = await res.json();
    items.value = Array.isArray(data?.items) ? data.items : [];
    if (selected.value) {
      const keep = items.value.find((x) => x.advisory_id === selected.value!.advisory_id);
      selected.value = keep ?? null;
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    loading.value = false;
  }
}

function select(b: AdvisoryBlobRef) {
  selected.value = b;
  previewBlocked.value = false;
  previewBlockedReason.value = null;
}

async function checkAndPreview(b: AdvisoryBlobRef) {
  select(b);

  // Check preview status first
  try {
    const url = `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/blobs/${encodeURIComponent(b.advisory_id)}/preview/status`;
    const res = await fetch(url);
    if (res.ok) {
      const status: PreviewStatus = await res.json();
      if (!status.ok) {
        previewBlocked.value = true;
        previewBlockedReason.value = status.reason || "Preview blocked";
        return;
      }
    }
  } catch {
    // If status check fails, try preview anyway
  }

  previewBlocked.value = false;
  previewBlockedReason.value = null;
}

function downloadUrl(b: AdvisoryBlobRef) {
  return `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/blobs/${encodeURIComponent(b.advisory_id)}/download`;
}

function svgPreviewUrl(b: AdvisoryBlobRef) {
  return `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/blobs/${encodeURIComponent(b.advisory_id)}/preview/svg`;
}

function downloadOne(b: AdvisoryBlobRef) {
  window.open(downloadUrl(b), "_blank");
}

function downloadAllZip() {
  const url = `${apiBase.value}/runs/${encodeURIComponent(props.runId)}/advisory/blobs/download-all.zip`;
  window.open(url, "_blank");
}

onMounted(refresh);
watch(() => props.runId, () => refresh());
</script>

<style scoped>
.panel { display:flex; flex-direction:column; gap:12px; }
.header { display:flex; justify-content:space-between; gap:12px; }
.title { font-weight:700; }
.subtle { opacity:0.75; }
.actions { display:flex; gap:8px; }

.btn { padding:8px 10px; border:1px solid rgba(0,0,0,0.2); border-radius:8px; background:white; cursor:pointer; }
.btn.secondary { opacity:0.85; }
.btn.tiny { padding:4px 8px; font-size:0.9em; }
.btn:disabled { opacity:0.5; cursor:not-allowed; }

.error { color:#b00020; }

.grid { display:grid; grid-template-columns: 1.2fr 0.8fr; gap:12px; }
.left, .right { border:1px solid rgba(0,0,0,0.12); border-radius:12px; padding:10px; }
.tbl { width:100%; border-collapse:collapse; }
.tbl th, .tbl td { padding:8px; border-bottom:1px solid rgba(0,0,0,0.08); }
.tbl tr { cursor:pointer; }
.tbl tr.selected { background:rgba(0,0,0,0.04); }
.row-actions { display:flex; gap:6px; justify-content:flex-end; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }

.preview-header { display:flex; justify-content:space-between; gap:8px; align-items:baseline; }
.preview-box { border:1px dashed rgba(0,0,0,0.18); border-radius:12px; overflow:hidden; height:420px; }
.svg-object { width:100%; height:100%; display:block; background:white; }
code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }

.preview-blocked {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 12px;
  gap: 12px;
}
.blocked-icon {
  width: 48px;
  height: 48px;
  background: #ffc107;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  color: #856404;
}
.blocked-reason {
  color: #856404;
  text-align: center;
  font-size: 0.95em;
}
</style>
