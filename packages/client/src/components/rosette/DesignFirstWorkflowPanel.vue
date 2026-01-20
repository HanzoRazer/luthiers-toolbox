<template>
  <div class="wf-panel">
    <div class="wf-header">
      <div class="wf-title">Design-First Workflow</div>
      <div class="wf-pill" :data-state="state">{{ state || "—" }}</div>
    </div>

    <!-- Log Viewer split pane drawer (Bundle 32.7.4 + 32.7.5) -->
    <SideDrawer :open="logDrawerOpen" :title="drawerTitle" @close="closeDrawer">
      <template #actions>
        <button
          class="btn ghost"
          :class="{ active: isPinned }"
          title="Pin to this run (keep logs stable)"
          @click="togglePin"
        >
          {{ isPinned ? "📌" : "📍" }}
        </button>
        <button class="btn ghost" @click="openLogsNewTab" title="Open in new tab">↗</button>
      </template>
      <iframe
        v-if="logDrawerOpen && logsUrl"
        :src="logsUrl"
        class="log-iframe"
      />
    </SideDrawer>

    <div class="wf-actions">
      <button :disabled="busy" @click="ensure" class="btn">
        {{ hasSession ? "Restart" : "Start" }}
      </button>
      <button :disabled="busy || !hasSession" @click="toReview" class="btn">
        Review
      </button>
      <button :disabled="busy || !hasSession" @click="approve" class="btn">
        Approve
      </button>
      <button :disabled="busy || !hasSession" @click="reject" class="btn ghost">
        Reject
      </button>
      <button :disabled="busy || !hasSession" @click="reopen" class="btn ghost">
        Reopen
      </button>
      <button
        :disabled="busy || !canIntent"
        @click="intent"
        class="btn primary"
      >
        Get CAM Handoff Intent
      </button>
    </div>

    <!-- Download overrides (Bundle 32.8.4.2) -->
    <div class="overrides">
      <div class="ovTitle">Download overrides</div>

      <select v-model="overrideToolId" class="sel" title="Override tool_id">
        <option v-for="o in TOOL_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
      </select>

      <select v-model="overrideMaterialId" class="sel" title="Override material_id">
        <option v-for="o in MATERIAL_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
      </select>

      <select v-model="overrideMachineProfileId" class="sel" title="Override machine_profile_id">
        <option v-for="o in MACHINE_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
      </select>

      <select v-model="overrideCamProfileId" class="sel" title="Override requested_cam_profile_id">
        <option v-for="o in CAM_PROFILE_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
      </select>

      <select v-model="overrideRiskTolerance" class="sel" title="Override risk_tolerance">
        <option v-for="o in RISK_TOLERANCE_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
      </select>

      <button class="btn ghost" @click="clearOverrides" title="Clear overrides">
        Clear
      </button>
    </div>

    <!-- Export URL Preview (Bundle 32.8.4.5 + 32.8.4.8) -->
    <div v-if="hasSession" class="export-url-preview">
      <div class="export-url-label">Export URL</div>
      <input
        type="text"
        class="export-url-input"
        :value="exportUrlPreview"
        readonly
        @click="($event.target as HTMLInputElement)?.select()"
      />
      <button class="btn ghost" @click="copyExportUrl" title="Copy URL to clipboard">
        Copy URL
      </button>
      <button
        class="btn ghost"
        @click="copyExportPowerShell"
        :disabled="!exportUrlPreview"
        title="Copy PowerShell Invoke-WebRequest command (downloads JSON to a file)"
      >
        Copy PowerShell
      </button>
      <button
        class="btn ghost"
        @click="copyExportPython"
        :disabled="!exportUrlPreview"
        title="Copy Python requests snippet (downloads JSON to a file)"
      >
        Copy Python
      </button>
      <button
        class="btn ghost"
        @click="copyExportNode"
        :disabled="!exportUrlPreview"
        title="Copy Node 18+ fetch snippet (downloads JSON to a file)"
      >
        Copy Node
      </button>
    </div>

    <div v-if="err" class="wf-error">{{ err }}</div>

    <!-- History -->
    <div v-if="session?.history?.length" class="wf-history">
      <div class="wf-history-title">History ({{ session.history.length }})</div>
      <div
        v-for="(evt, idx) in session.history.slice().reverse().slice(0, 5)"
        :key="idx"
        class="wf-event"
      >
        <span class="wf-event-action">{{ evt.action }}</span>
        <span class="wf-event-transition">
          {{ evt.from_state }} → {{ evt.to_state }}
        </span>
        <span v-if="evt.note" class="wf-event-note">{{ evt.note }}</span>
      </div>
    </div>

    <!-- Last Intent Preview -->
    <div v-if="lastIntent" class="wf-intent-preview">
      <div class="wf-intent-title">Last Promotion Intent</div>
      <pre class="wf-intent-json">{{ JSON.stringify(lastIntent, null, 2) }}</pre>
      <div class="wf-intent-actions">
        <button class="btn ghost" @click="copyIntent">Copy JSON</button>
        <button class="btn ghost" @click="copySessionId">Copy Session ID</button>
        <button class="btn ghost" @click="copyIntentCurl" title="Copy cURL for promotion intent">Copy cURL</button>
        <button class="btn ghost" @click="openInLogViewer" title="Open Log Viewer filtered to this run">Open logs</button>
        <button class="btn ghost" @click="downloadIntent" title="Download intent as JSON file">Download intent</button>
        <button class="btn ghost" @click="clearIntent">Clear</button>
      </div>
    </div>

    <!-- Session Picker (Bundle 32.7.7) -->
    <WorkflowSessionPicker />
  </div>
</template>

<script setup lang="ts">
/**
 * DesignFirstWorkflowPanel.vue (Bundle 32.7.0 + 32.7.2 + 32.7.3 + 32.7.4 + 32.7.5 + 32.7.7 + 32.8.4.1)
 *
 * UI panel for managing design-first workflow state.
 * Displays workflow state, history, and promotion intent.
 *
 * Bundle 32.7.2: Added session hydration on mount + Clear button.
 * Bundle 32.7.3: Added Copy cURL + Open in Log Viewer deep-link.
 * Bundle 32.7.4: Open logs in split pane drawer (iframe).
 * Bundle 32.7.5: Pin a run in drawer (iframe stays on pinned run_id).
 * Bundle 32.7.7: Session picker for jumping between sessions.
 * Bundle 32.8.4.1: Download Intent as JSON file.
 * Bundle 32.8.4.2: Download intent with overrides (tool/material/profile dropdowns).
 * Bundle 32.8.4.3: Remember overrides (localStorage persistence).
 * Bundle 32.8.4.5: Export URL preview + Copy URL for testers.
 * Bundle 32.8.4.8: Copy PowerShell Invoke-WebRequest command (Windows-first shops).
 */
import { computed, onMounted, ref, watch } from "vue";
import { useArtDesignFirstWorkflowStore } from "@/stores/artDesignFirstWorkflowStore";
import { useToastStore } from "@/stores/toastStore";
import SideDrawer from "@/components/ui/SideDrawer.vue";
import WorkflowSessionPicker from "@/components/rosette/WorkflowSessionPicker.vue";

const wf = useArtDesignFirstWorkflowStore();
const toast = useToastStore();

// ==========================================================================
// Bundle 32.8.4.2: Download intent with overrides
// ==========================================================================

type Option = { id: string; label: string };

const TOOL_OPTIONS: Option[] = [
  { id: "", label: "Tool (default)" },
  { id: "vbit_60", label: "V-bit 60°" },
  { id: "downcut_2mm", label: "Downcut 2mm" },
  { id: "upcut_2mm", label: "Upcut 2mm" },
];

const MATERIAL_OPTIONS: Option[] = [
  { id: "", label: "Material (default)" },
  { id: "ebony", label: "Ebony" },
  { id: "rosewood", label: "Rosewood" },
  { id: "maple", label: "Maple" },
  { id: "spruce", label: "Spruce" },
];

const MACHINE_OPTIONS: Option[] = [
  { id: "", label: "Machine (default)" },
  { id: "shopbot_alpha", label: "ShopBot Alpha" },
  { id: "shapeoko_pro", label: "Shapeoko Pro" },
];

const CAM_PROFILE_OPTIONS: Option[] = [
  { id: "", label: "CAM profile (default)" },
  { id: "vbit_60_ebony_safe", label: "V-bit 60 / Ebony / Safe" },
  { id: "downcut_maple_fast", label: "Downcut / Maple / Fast" },
];

const RISK_TOLERANCE_OPTIONS: Option[] = [
  { id: "", label: "Risk tolerance (default)" },
  { id: "GREEN_ONLY", label: "GREEN only" },
  { id: "ALLOW_YELLOW", label: "Allow YELLOW" },
];

// Selected overrides (empty = not sent)
const overrideToolId = ref<string>("");
const overrideMaterialId = ref<string>("");
const overrideMachineProfileId = ref<string>("");
const overrideCamProfileId = ref<string>("");
const overrideRiskTolerance = ref<string>("");

// ==========================================================================
// Bundle 32.8.4.3 + 32.8.4.4: Remember overrides (per-mode localStorage)
// ==========================================================================

/** Prefix used for per-mode storage keys */
const OVERRIDES_LS_KEY_PREFIX = "artStudio.promotionIntentExport.overrides.v1";

function _overridesKeyForMode(mode: string | undefined | null): string {
  const m = (mode || "unknown").trim() || "unknown";
  return `${OVERRIDES_LS_KEY_PREFIX}:${m}`;
}

type ExportOverrides = {
  tool_id: string;
  material_id: string;
  machine_profile_id: string;
  requested_cam_profile_id: string;
  risk_tolerance: string;
};

function _readOverridesFromStorage(key: string): ExportOverrides | null {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const j = JSON.parse(raw);
    if (!j || typeof j !== "object") return null;
    return {
      tool_id: String((j as any).tool_id ?? ""),
      material_id: String((j as any).material_id ?? ""),
      machine_profile_id: String((j as any).machine_profile_id ?? ""),
      requested_cam_profile_id: String((j as any).requested_cam_profile_id ?? ""),
      risk_tolerance: String((j as any).risk_tolerance ?? ""),
    };
  } catch {
    return null;
  }
}

function _writeOverridesToStorage(key: string, v: ExportOverrides) {
  try {
    localStorage.setItem(key, JSON.stringify(v));
  } catch {
    // ignore (private browsing / storage disabled)
  }
}

function _clearOverridesStorage(key: string) {
  try {
    localStorage.removeItem(key);
  } catch {
    // ignore
  }
}

const session = computed(() => wf.session);
const state = computed(() => wf.stateName);
const busy = computed(() => wf.loading);
const err = computed(() => wf.error);
const hasSession = computed(() => wf.hasSession);
const canIntent = computed(() => wf.canRequestIntent);
const lastIntent = computed(() => wf.lastPromotionIntent);

// Per-mode storage key (Bundle 32.8.4.4)
const currentMode = computed(() => (wf.session?.mode as any) ?? "design_first");
const overridesStorageKey = computed(() => _overridesKeyForMode(String(currentMode.value)));

// Log Viewer drawer state (Bundle 32.7.4 + 32.7.5)
const logDrawerOpen = ref(false);

// Pinned run_id for the drawer — keeps iframe stable across workflow changes (Bundle 32.7.5)
const pinnedRunId = ref<string>("");

const effectiveRunId = computed(() => {
  // If pinned, use pinned; else follow current sessionId
  return pinnedRunId.value || wf.sessionId || "";
});

const logsUrl = computed(() => {
  const id = effectiveRunId.value;
  if (!id) return "";
  return buildLogViewerUrl(id);
});

const isPinned = computed(() => !!pinnedRunId.value);

const drawerTitle = computed(() => {
  if (isPinned.value) {
    return `Log Viewer (pinned: ${pinnedRunId.value.slice(0, 8)}…)`;
  }
  return "Log Viewer";
});

// Hydrate session from localStorage on mount (Bundle 32.7.2)
// + Hydrate overrides from localStorage (Bundle 32.8.4.3 + 32.8.4.4 per-mode)
onMounted(() => {
  wf.hydrateFromLocalStorage();

  // Restore saved overrides for current mode (32.8.4.4)
  const saved = _readOverridesFromStorage(overridesStorageKey.value);
  if (saved) {
    overrideToolId.value = saved.tool_id;
    overrideMaterialId.value = saved.material_id;
    overrideMachineProfileId.value = saved.machine_profile_id;
    overrideCamProfileId.value = saved.requested_cam_profile_id;
    overrideRiskTolerance.value = saved.risk_tolerance;
  }
});

// When mode changes, swap overrides (load the saved set for that mode) (32.8.4.4)
watch(
  overridesStorageKey,
  (newKey, oldKey) => {
    if (newKey === oldKey) return;
    const saved = _readOverridesFromStorage(newKey);

    if (saved) {
      overrideToolId.value = saved.tool_id;
      overrideMaterialId.value = saved.material_id;
      overrideMachineProfileId.value = saved.machine_profile_id;
      overrideCamProfileId.value = saved.requested_cam_profile_id;
      overrideRiskTolerance.value = saved.risk_tolerance;
      toast.info(`Loaded export overrides for mode: ${String(currentMode.value)}`);
    } else {
      // No saved overrides for this mode -> reset to default empty overrides
      overrideToolId.value = "";
      overrideMaterialId.value = "";
      overrideMachineProfileId.value = "";
      overrideCamProfileId.value = "";
      overrideRiskTolerance.value = "";
    }
  },
  { immediate: false }
);

// Auto-save overrides to current mode key when changed (Bundle 32.8.4.3 + 32.8.4.4)
watch(
  [
    overrideToolId,
    overrideMaterialId,
    overrideMachineProfileId,
    overrideCamProfileId,
    overrideRiskTolerance,
    overridesStorageKey,
  ],
  () => {
    _writeOverridesToStorage(overridesStorageKey.value, {
      tool_id: overrideToolId.value || "",
      material_id: overrideMaterialId.value || "",
      machine_profile_id: overrideMachineProfileId.value || "",
      requested_cam_profile_id: overrideCamProfileId.value || "",
      risk_tolerance: overrideRiskTolerance.value || "",
    });
  },
  { deep: false }
);

async function ensure() {
  if (wf.hasSession) {
    wf.clearSession();
  }
  await wf.ensureSessionDesignFirst();
}

async function toReview() {
  if (!wf.hasSession) {
    await wf.ensureSessionDesignFirst();
  }
  await wf.transition("in_review");
}

async function approve() {
  await wf.transition("approved");
}

async function reject() {
  await wf.transition("rejected", "Design needs revision");
}

async function reopen() {
  await wf.transition("draft");
}

async function intent() {
  const payload = await wf.requestPromotionIntent();
  if (payload) {
    toast.info("Intent payload ready. Use Log Viewer / CAM lane to consume.");
    console.log("[ArtStudio] CAM handoff intent:", payload);
  }
}

async function copyIntent() {
  if (!lastIntent.value) return;
  try {
    await navigator.clipboard.writeText(JSON.stringify(lastIntent.value, null, 2));
    toast.success("Intent JSON copied to clipboard");
  } catch {
    toast.error("Failed to copy to clipboard");
  }
}

async function copySessionId() {
  const sid = wf.sessionId;
  if (!sid) return;
  try {
    await navigator.clipboard.writeText(sid);
    toast.success("Session ID copied to clipboard");
  } catch {
    toast.error("Failed to copy to clipboard");
  }
}

function clearIntent() {
  wf.clearSession();
  toast.info("Session cleared");
}

// ==========================================================================
// Bundle 32.7.3: Copy cURL + Open in Log Viewer
// ==========================================================================

function _baseUrl(): string {
  // Prefer explicit VITE_API_URL if provided; otherwise assume same-origin /api
  const envBase = (import.meta as any).env?.VITE_API_URL;
  const base = envBase && typeof envBase === "string" ? envBase : "/api";
  const origin = window.location.origin;
  if (base.startsWith("http://") || base.startsWith("https://")) return base;
  return origin + base;
}

function buildPromotionIntentCurl(session_id: string): string {
  const url = `${_baseUrl()}/art/workflow/sessions/${encodeURIComponent(session_id)}/promotion_intent`;
  return [
    `curl -X POST "${url}"`,
    `  -H "Accept: application/json"`,
    `  -H "Content-Type: application/json"`,
  ].join(" \\\n");
}

async function copyIntentCurl() {
  const sid = wf.sessionId;
  if (!sid) return;
  const curl = buildPromotionIntentCurl(sid);
  try {
    await navigator.clipboard.writeText(curl);
    toast.success("cURL copied to clipboard");
  } catch {
    toast.error("Failed to copy cURL");
  }
}

// ==========================================================================
// Bundle 32.8.4.1 + 32.8.4.2: Download Intent as JSON file with overrides
// ==========================================================================

function buildPromotionIntentExportUrl(session_id: string): string {
  const base = _baseUrl();
  const url = new URL(
    `${base}/art/workflow/sessions/${encodeURIComponent(session_id)}/promotion_intent.json`,
    window.location.origin
  );

  // Append only if provided (32.8.4.2)
  if (overrideToolId.value) url.searchParams.set("tool_id", overrideToolId.value);
  if (overrideMaterialId.value) url.searchParams.set("material_id", overrideMaterialId.value);
  if (overrideMachineProfileId.value) url.searchParams.set("machine_profile_id", overrideMachineProfileId.value);
  if (overrideCamProfileId.value) url.searchParams.set("requested_cam_profile_id", overrideCamProfileId.value);
  if (overrideRiskTolerance.value) url.searchParams.set("risk_tolerance", overrideRiskTolerance.value);

  return url.toString();
}

function clearOverrides() {
  overrideToolId.value = "";
  overrideMaterialId.value = "";
  overrideMachineProfileId.value = "";
  overrideCamProfileId.value = "";
  overrideRiskTolerance.value = "";

  _clearOverridesStorage(overridesStorageKey.value); // (32.8.4.4 per-mode)
  toast.info(`Download overrides cleared for mode: ${String(currentMode.value)}`);
}

// ==========================================================================
// Bundle 32.8.4.5: Export URL preview + Copy URL
// ==========================================================================

const exportUrlPreview = computed(() => {
  const sid = wf.sessionId;
  if (!sid) return "";
  return buildPromotionIntentExportUrl(sid);
});

async function copyExportUrl() {
  const url = exportUrlPreview.value;
  if (!url) return;
  try {
    await navigator.clipboard.writeText(url);
    toast.success("Export URL copied to clipboard");
  } catch {
    toast.error("Failed to copy URL");
  }
}

// ==========================================================================
// Bundle 32.8.4.8: Copy PowerShell Invoke-WebRequest (Windows-first shops)
// ==========================================================================

function _psEscape(s: string): string {
  // Single-quote safe for PowerShell: ' becomes ''
  return `'${String(s).replace(/'/g, "''")}'`;
}

function _safeFilenameFromSession(session_id: string): string {
  return `promotion_intent_v1_${session_id}.json`.replace(/[^a-zA-Z0-9._-]/g, "_");
}

function buildExportPowerShellIwr(url: string, session_id: string): string {
  const out = _safeFilenameFromSession(session_id);

  // Use Invoke-WebRequest with -OutFile
  // Add -UseBasicParsing for older PS compatibility (harmless on newer)
  return [
    `$url = ${_psEscape(url)}`,
    `$out = ${_psEscape(out)}`,
    `Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing`,
    `Write-Host ("Saved: " + $out)`,
  ].join("\r\n");
}

async function copyExportPowerShell() {
  const sid = wf.sessionId;
  const url = exportUrlPreview.value;
  if (!sid || !url) return;

  const cmd = buildExportPowerShellIwr(url, sid);

  const combined = [
    "# Promotion intent export (PowerShell)",
    cmd,
    "",
  ].join("\n");

  try {
    await navigator.clipboard.writeText(combined);
    toast.success("Copied PowerShell command.");
  } catch {
    toast.error("Copy failed.");
  }
}

// ==========================================================================
// Bundle 32.8.4.9: Copy Python requests snippet (CI/script repro)
// ==========================================================================

function _pyEscape(s: string): string {
  // Safe for python triple-quoted strings
  return String(s).replace(/\\/g, "\\\\").replace(/"""/g, '\\"\\"\\"');
}

function buildExportPythonRequests(url: string, session_id: string): string {
  const out = _safeFilenameFromSession(session_id);
  const u = _pyEscape(url);

  return [
    "# Promotion intent export (Python requests)",
    "import sys",
    "import json",
    "import requests",
    "",
    `url = """${u}"""`,
    `out = r"""${out}"""`,
    "",
    "resp = requests.get(url, headers={'Accept': 'application/json'}, timeout=30)",
    "resp.raise_for_status()",
    "",
    "# Save raw body",
    "with open(out, 'wb') as f:",
    "    f.write(resp.content)",
    "",
    "# Optional: quick sanity parse",
    "try:",
    "    data = resp.json()",
    "    print('Downloaded intent:', data.get('intent_version'), 'session_id=', data.get('session_id'))",
    "except Exception as e:",
    "    print('Downloaded file saved, but JSON parse failed:', e, file=sys.stderr)",
    "",
    "print('Saved:', out)",
    "",
  ].join("\n");
}

async function copyExportPython() {
  const sid = wf.sessionId;
  const url = exportUrlPreview.value;
  if (!sid || !url) return;

  const snippet = buildExportPythonRequests(url, sid);

  try {
    await navigator.clipboard.writeText(snippet);
    toast.success("Copied Python requests snippet.");
  } catch {
    toast.error("Copy failed.");
  }
}

// ==========================================================================
// Bundle 32.8.4.10: Copy Node fetch snippet (Node 18+ / JS CI runners)
// ==========================================================================

function _jsEscape(s: string): string {
  // Escape for JS template literal (backticks)
  return String(s).replace(/\/g, "\\\\").replace(/`/g, "\`");
}

function buildExportNodeFetch(url: string, session_id: string): string {
  const out = _safeFilenameFromSession(session_id);
  const u = _jsEscape(url);

  return [
    "// Promotion intent export (Node fetch, Node 18+)",
    "import fs from 'node:fs';",
    "",
    "const url = \`" + u + "\`;",
    "const out = " + JSON.stringify(out) + ";",
    "",
    "const res = await fetch(url, {",
    "  method: 'GET',",
    "  headers: { 'Accept': 'application/json' },",
    "});",
    "",
    "if (!res.ok) {",
    "  const ct = res.headers.get('content-type') || '';",
    "  let body = '';",
    "  try { body = ct.includes('application/json') ? JSON.stringify(await res.json()) : await res.text(); } catch {}",
    "  throw new Error(\`HTTP \${res.status} \${res.statusText} :: \${body}\`);",
    "}",
    "",
    "const buf = Buffer.from(await res.arrayBuffer());",
    "fs.writeFileSync(out, buf);",
    "",
    "// Optional: sanity parse",
    "try {",
    "  const json = JSON.parse(buf.toString('utf8'));",
    "  console.log('Downloaded intent:', json.intent_version, 'session_id=', json.session_id);",
    "} catch (e) {",
    "  console.warn('Saved file but JSON parse failed:', e?.message || e);",
    "}",
    "",
    "console.log('Saved:', out);",
    "",
  ].join("\n");
}

async function copyExportNode() {
  const sid = wf.sessionId;
  const url = exportUrlPreview.value;
  if (!sid || !url) return;

  const snippet = buildExportNodeFetch(url, sid);

  try {
    await navigator.clipboard.writeText(snippet);
    toast.success("Copied Node fetch snippet.");
  } catch {
    toast.error("Copy failed.");
  }
}


async function downloadIntent() {
  const sid = wf.sessionId;
  if (!sid) return;
  const url = buildPromotionIntentExportUrl(sid);
  try {
    const resp = await fetch(url, { method: "GET" });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${txt}`);
    }
    const blob = await resp.blob();
    const filename = `promotion_intent_${sid.slice(0, 8)}.json`;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(a.href);
    toast.success(`Downloaded ${filename}`);
  } catch (e: any) {
    toast.error(`Download failed: ${e.message || e}`);
  }
}

function buildLogViewerUrl(session_id: string): string {
  const u = new URL(window.location.href);
  u.pathname = "/rmos/logs";
  u.searchParams.set("mode", "art_studio");
  u.searchParams.set("run_id", session_id);
  return u.toString();
}

function openInLogViewer() {
  const sid = wf.sessionId;
  if (!sid) return;
  // Bundle 32.7.5: Pin to the current session when opening
  pinnedRunId.value = sid;
  logDrawerOpen.value = true;
}

function openLogsNewTab() {
  if (logsUrl.value) {
    window.open(logsUrl.value, "_blank");
  }
}

function togglePin() {
  if (isPinned.value) {
    // Unpin: follow current session
    pinnedRunId.value = "";
  } else {
    // Pin to current effective run_id
    pinnedRunId.value = effectiveRunId.value;
  }
}

function closeDrawer() {
  logDrawerOpen.value = false;
  // Clear pin when closing (optional: remove this line to persist pin)
  pinnedRunId.value = "";
}
</script>

<style scoped>
.wf-panel {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 12px;
  margin: 10px 0;
  background: #fff;
}

.wf-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.wf-title {
  font-weight: 700;
  font-size: 14px;
}

.wf-pill {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(0, 0, 0, 0.15);
  text-transform: uppercase;
  font-weight: 600;
}

.wf-pill[data-state="draft"] {
  background: rgba(100, 100, 100, 0.08);
}
.wf-pill[data-state="in_review"] {
  background: rgba(200, 160, 0, 0.12);
  border-color: rgba(200, 160, 0, 0.35);
}
.wf-pill[data-state="approved"] {
  background: rgba(0, 180, 0, 0.12);
  border-color: rgba(0, 180, 0, 0.35);
}
.wf-pill[data-state="rejected"] {
  background: rgba(200, 0, 0, 0.12);
  border-color: rgba(200, 0, 0, 0.35);
}

.wf-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.btn {
  border: 1px solid rgba(0, 0, 0, 0.18);
  border-radius: 10px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  background: #fff;
  transition: background 0.1s;
}

.btn:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.04);
}

.btn:disabled {
  opacity: 0.5;
  cursor: default;
}

.btn.primary {
  background: rgba(0, 0, 0, 0.06);
  font-weight: 600;
}

.btn.ghost {
  background: transparent;
}

.wf-error {
  color: #b00020;
  font-size: 12px;
  margin-top: 8px;
}

.wf-history {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-history-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-event {
  font-size: 11px;
  padding: 4px 0;
  display: flex;
  gap: 8px;
  align-items: center;
}

.wf-event-action {
  font-weight: 600;
}

.wf-event-transition {
  opacity: 0.7;
}

.wf-event-note {
  font-style: italic;
  opacity: 0.6;
}

.wf-intent-preview {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
}

.wf-intent-title {
  font-size: 11px;
  font-weight: 600;
  opacity: 0.7;
  margin-bottom: 6px;
}

.wf-intent-json {
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 8px;
  font-size: 10px;
  overflow-x: auto;
  max-height: 200px;
  overflow-y: auto;
}

.wf-intent-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.wf-intent-actions .btn {
  font-size: 11px;
  padding: 4px 8px;
}

/* Bundle 32.7.4: Log viewer iframe in drawer */
.log-iframe {
  flex: 1;
  width: 100%;
  border: none;
}

/* Bundle 32.8.4.2: Download overrides */
.overrides {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

/* Bundle 32.8.4.5: Export URL preview */
.export-url-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(0, 0, 0, 0.08);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.export-url-label {
  font-size: 12px;
  font-weight: 700;
  opacity: 0.85;
}

.export-url-input {
  flex: 1;
  min-width: 200px;
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 11px;
  font-family: monospace;
  background: rgba(0, 0, 0, 0.02);
  color: #333;
}

.ovTitle {
  font-size: 12px;
  font-weight: 800;
  opacity: 0.85;
  margin-right: 4px;
}

.sel {
  border: 1px solid rgba(0, 0, 0, 0.16);
  border-radius: 10px;
  padding: 6px 8px;
  font-size: 12px;
  background: white;
}
</style>
