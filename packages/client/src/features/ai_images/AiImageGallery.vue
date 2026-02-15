<script setup lang="ts">
/**
 * AI Image Gallery — RMOS-integrated Gallery with Attach/Review/Promote
 *
 * Review Hardening Bundle (A+B): State-aware buttons + inline review panel
 * Wired to runs.ts canonical SDK and visionApi feature module.
 *
 * @package features/ai_images
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import VariantReviewPanel from "./components/VariantReviewPanel.vue";

const router = useRouter();

// Vision feature API (existing module)
import {
  generateImages,
  attachAdvisoryToRun,
  createRun,
  listRecentRuns,
  getProviders,
  type VisionAsset,
  type ProviderName,
} from "./api/visionApi";

// RMOS typed SDK (canonical)
import {
  listAdvisoryVariants,
  reviewAdvisoryVariant,
  promoteAdvisoryVariant,
  type AdvisoryVariantSummary,
  type RejectReasonCode,
} from "@/sdk/rmos/runs";

// Local type for run summaries from visionApi
type RunSummary = {
  run_id: string;
  created_at_utc?: string;
  event_type?: string;
  status?: string;
};

/** Base URL for cross-origin API deployments */
const API_BASE = (import.meta as any).env?.VITE_API_BASE || '';

/** Resolve asset URL to full URL (handles cross-origin deployments). */
function resolveAssetUrl(url: string | undefined): string {
  if (!url) return '/placeholder.svg';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  return `${API_BASE}${url}`;
}

// -----------------------------
// State
// -----------------------------
const prompt = ref("");
const provider = ref<ProviderName>("openai");
const numImages = ref(2);
const size = ref("1024x1024");
const quality = ref("standard");

const generatedAssets = ref<VisionAsset[]>([]);
const selectedRunId = ref<string | null>(null);
const runs = ref<RunSummary[]>([]);
const providers = ref<any[]>([]);

const isGenerating = ref(false);
const isAttaching = ref<string | null>(null); // sha256 being attached
const isPromoting = ref<string | null>(null); // advisory_id being promoted
const error = ref<string | null>(null);
const success = ref<string | null>(null);

// inline review panel toggles per advisory_id
const openReviewFor = ref<string | null>(null);

// authoritative run-side summaries keyed by advisory_id
const variantById = ref<Record<string, AdvisoryVariantSummary>>({});

// reconcile map: asset sha256 -> advisory_id (trust attach response)
const advisoryIdByAssetSha = ref<Record<string, string>>({});

// micro-follow: quick actions use per-row busy flags (prevents double clicks)
const busyByAdvisoryId = ref<Record<string, "review" | "promote" | null>>({});

// micro-follow: track last run we attached to (for fallback navigation)
const lastAttachedRunId = ref<string | null>(null);

// -----------------------------
// Helpers
// -----------------------------
function _toastOk(msg: string) {
  success.value = msg;
  window.setTimeout(() => (success.value = null), 1600);
}

function _toastErr(msg: string) {
  error.value = msg;
  window.setTimeout(() => (error.value = null), 2200);
}

function goToRunReview(runId: string) {
  router.push({ name: "RunVariantsReview", params: { run_id: runId } });
}

// micro-follow: toolbar Open Review with fallback to lastAttachedRunId
function goToReview(runId?: string | null) {
  const id = runId ?? selectedRunId.value ?? lastAttachedRunId.value;
  if (!id) return;
  router.push({ name: "RunVariantsReview", params: { run_id: id } });
}

function _advisoryIdForAsset(a: VisionAsset): string | null {
  const sha = (a as any).sha256 as string | undefined;
  if (!sha) return null;
  return advisoryIdByAssetSha.value[sha] ?? sha; // sha is typical advisory_id
}

function _variantForAsset(a: VisionAsset): AdvisoryVariantSummary | null {
  const advisoryId = _advisoryIdForAsset(a);
  if (!advisoryId) return null;
  return variantById.value[advisoryId] ?? null;
}

const canGenerate = computed(() => prompt.value.trim().length > 0 && !isGenerating.value);

function attachDisabledReason(a: VisionAsset): string | null {
  if (!selectedRunId.value) return "Select a run first.";
  const v = _variantForAsset(a);
  if (v) return "Already attached to this run.";
  return null;
}

function promoteDisabledReason(a: VisionAsset): string | null {
  const v = _variantForAsset(a);
  if (!v) return "Attach to a run first.";
  if (v.rejected) return "Rejected variants cannot be promoted.";
  if (v.promoted) return "Already promoted.";
  if (v.status !== "REVIEWED") return "Must be reviewed first (status=REVIEWED).";
  return null;
}

function rejectionHover(v: AdvisoryVariantSummary | null | undefined): string {
  if (!v) return "";
  if (!v.rejected) return "Not rejected.";
  const parts: string[] = [];
  if ((v as any).rejection_reason_code) parts.push(`Code: ${(v as any).rejection_reason_code}`);
  if ((v as any).rejection_reason_detail) parts.push(`Detail: ${(v as any).rejection_reason_detail}`);
  if ((v as any).rejection_operator_note) parts.push(`Note: ${(v as any).rejection_operator_note}`);
  if ((v as any).rejected_at_utc) parts.push(`At: ${(v as any).rejected_at_utc}`);
  return parts.length ? parts.join("\n") : "Rejected.";
}

function canUndoReject(v: AdvisoryVariantSummary | null | undefined): string | null {
  if (!v) return "Attach first";
  if (!v.rejected) return "Not rejected";
  if (v.status === "PROMOTED" || v.promoted) return "Already promoted";
  return null;
}

// cherry-pick: DRY helpers for busy state (from redundant diff)
function isRowBusy(advisoryId: string, kind: "review" | "promote"): boolean {
  return busyByAdvisoryId.value[advisoryId] === kind;
}

function _setBusy(advisoryId: string, v: "review" | "promote" | null) {
  busyByAdvisoryId.value = { ...busyByAdvisoryId.value, [advisoryId]: v };
}

async function quickReject(advisoryId: string, code: RejectReasonCode) {
  const runId = selectedRunId.value;
  if (!runId) return;
  if (busyByAdvisoryId.value[advisoryId]) return;
  _setBusy(advisoryId, "review");
  try {
    const res = await reviewAdvisoryVariant(runId, advisoryId, {
      rejected: true,
      rejection_reason_code: code,
      status: "REJECTED",
    });
    await refreshVariants();
    _toastOk(`Rejected (${code}).${res.requestId ? ` req:${res.requestId}` : ""}`);
  } catch (e: any) {
    _toastErr(e?.message || "Reject failed.");
  } finally {
    _setBusy(advisoryId, null);
  }
}

async function undoReject(advisoryId: string) {
  const runId = selectedRunId.value;
  if (!runId) return;
  if (busyByAdvisoryId.value[advisoryId]) return;
  _setBusy(advisoryId, "review");
  try {
    // IMPORTANT: undo reject uses the same canonical review endpoint
    const res = await reviewAdvisoryVariant(runId, advisoryId, {
      rejected: false,
      status: "REVIEWED",
      // clear reason fields server-side is preferred; client sets nulls defensively
      rejection_reason_code: null as any,
      rejection_reason_detail: null as any,
      rejection_operator_note: null as any,
    });
    await refreshVariants();
    _toastOk(`Rejection cleared.${res.requestId ? ` req:${res.requestId}` : ""}`);
  } catch (e: any) {
    _toastErr(e?.message || "Undo reject failed.");
  } finally {
    _setBusy(advisoryId, null);
  }
}

async function quickPromote(advisoryId: string) {
  const runId = selectedRunId.value;
  if (!runId) return;
  if (busyByAdvisoryId.value[advisoryId]) return;
  _setBusy(advisoryId, "promote");
  try {
    const res = await promoteAdvisoryVariant(runId, advisoryId);
    await refreshVariants();
    _toastOk(`Promoted.${res.requestId ? ` req:${res.requestId}` : ""}`);
  } catch (e: any) {
    _toastErr(e?.message || "Promote failed.");
  } finally {
    _setBusy(advisoryId, null);
  }
}

async function refreshVariants() {
  if (!selectedRunId.value) return;

  try {
    const res = await listAdvisoryVariants(selectedRunId.value);
    const next: Record<string, AdvisoryVariantSummary> = {};
    for (const it of res.items ?? []) next[it.advisory_id] = it;
    variantById.value = next;
  } catch (e: any) {
    _toastErr(e?.message || "Failed to load run variants.");
  }
}

// -----------------------------
// Actions
// -----------------------------
async function doGenerate() {
  if (!canGenerate.value) return;
  isGenerating.value = true;
  try {
    const req = {
      prompt: prompt.value,
      provider: provider.value,
      num_images: numImages.value,
      size: size.value,
      quality: quality.value,
    };
    const res = await generateImages(req as any);
    generatedAssets.value = res.assets ?? [];
    _toastOk(`Generated ${generatedAssets.value.length} asset(s).`);

    // If a run is selected, refresh so state-aware buttons work immediately
    if (selectedRunId.value) await refreshVariants();
  } catch (e: any) {
    _toastErr(e?.message || "Generate failed.");
  } finally {
    isGenerating.value = false;
  }
}

// -----------------------------------------------------------------------------
// micro-follow: auto-create run on first attach (extracted for reusability)
// -----------------------------------------------------------------------------
async function ensureRunSelected(): Promise<string | null> {
  if (selectedRunId.value) return selectedRunId.value;

  try {
    const created = await createRun({ event_type: "vision_image_review" });
    selectedRunId.value = created.run_id;

    // keep dropdown in sync (best-effort, non-blocking)
    try {
      runs.value = (await listRecentRuns()).runs;
    } catch {
      // ignore
    }

    _toastOk("Created new run.");
    return created.run_id;
  } catch (e: any) {
    _toastErr(e?.message || "Create run failed.");
    return null;
  }
}

async function doAttach(a: VisionAsset) {
  const sha = (a as any).sha256 as string | undefined;
  if (!sha) {
    _toastErr("Asset missing sha256.");
    return;
  }
  const deny = attachDisabledReason(a);
  if (deny) {
    _toastErr(deny);
    return;
  }

  const runId = await ensureRunSelected();
  if (!runId) return;

  isAttaching.value = sha;
  try {
    // IMPORTANT: trust attach response for advisory_id
    const res = await attachAdvisoryToRun(runId, {
      advisory_id: sha, // canonical
      kind: "advisory",
    });

    const advisoryId = (res?.advisory_id ?? sha) as string;
    advisoryIdByAssetSha.value = { ...advisoryIdByAssetSha.value, [sha]: advisoryId };
    lastAttachedRunId.value = selectedRunId.value;

    await refreshVariants();

    // micro-follow: auto-deeplink to review surface immediately after attach
    // Canonical route: /rmos/runs/:run_id/variants (name: RunVariantsReview)
    try {
      router.push({ name: "RunVariantsReview", params: { run_id: selectedRunId.value } });
    } catch {
      // non-fatal; keep UX usable even if route name differs in local forks
    }

    _toastOk("Attached to run.");
  } catch (e: any) {
    _toastErr(e?.message || "Attach failed.");
  } finally {
    isAttaching.value = null;
  }
}

async function doPromote(a: VisionAsset) {
  const deny = promoteDisabledReason(a);
  if (deny) {
    _toastErr(deny);
    return;
  }
  if (!selectedRunId.value) return;

  const advisoryId = _advisoryIdForAsset(a);
  if (!advisoryId) {
    _toastErr("Missing advisory id.");
    return;
  }

  isPromoting.value = advisoryId;
  try {
    await promoteAdvisoryVariant(selectedRunId.value, advisoryId);
    await refreshVariants();
    _toastOk("Promoted to manufacturing.");
  } catch (e: any) {
    _toastErr(e?.message || "Promote failed.");
  } finally {
    isPromoting.value = null;
  }
}

function toggleReview(a: VisionAsset) {
  const v = _variantForAsset(a);
  if (!v) {
    _toastErr("Attach to a run first.");
    return;
  }
  openReviewFor.value = openReviewFor.value === v.advisory_id ? null : v.advisory_id;
}

// -----------------------------
// Init
// -----------------------------
onMounted(async () => {
  try {
    const res = await getProviders();
    providers.value = res.providers ?? [];
  } catch {}
  try {
    const res = await listRecentRuns();
    runs.value = (res as any).runs ?? [];
    if (!selectedRunId.value && runs.value.length) {
      selectedRunId.value = runs.value[0].run_id as any;
    }
  } catch {}
  if (selectedRunId.value) await refreshVariants();
});
</script>

<template>
  <div class="wrap">
    <div class="top">
      <div class="controls">
        <input
          v-model="prompt"
          class="input"
          placeholder="Prompt…"
        >
        <select
          v-model="provider"
          class="select"
        >
          <option value="openai">
            openai
          </option>
          <option value="stub">
            stub
          </option>
        </select>
        <select
          v-model="numImages"
          class="select"
        >
          <option :value="1">
            1
          </option>
          <option :value="2">
            2
          </option>
          <option :value="3">
            3
          </option>
        </select>
        <button
          class="btn primary"
          :disabled="!canGenerate"
          @click="doGenerate"
        >
          {{ isGenerating ? "Generating…" : "Generate" }}
        </button>

        <button
          class="btn"
          type="button"
          :disabled="!selectedRunId && !lastAttachedRunId"
          :title="(selectedRunId || lastAttachedRunId) ? 'Open the run review surface' : 'Attach an asset first to create/select a run'"
          @click="goToReview()"
        >
          Open Review
        </button>

        <select
          v-model="selectedRunId"
          class="select"
          @change="refreshVariants"
        >
          <option :value="null">
            Select run…
          </option>
          <option
            v-for="r in runs"
            :key="r.run_id"
            :value="r.run_id"
          >
            {{ r.run_id }}
          </option>
        </select>
      </div>

      <div
        v-if="error"
        class="toast err"
      >
        {{ error }}
      </div>
      <div
        v-if="success"
        class="toast ok"
      >
        {{ success }}
      </div>

      <!-- micro-follow: run context actions -->
      <div
        v-if="selectedRunId"
        class="runActions"
      >
        <button
          class="btn small"
          type="button"
          @click="goToRunReview(selectedRunId)"
        >
          Open Review
        </button>
        <button
          class="btn small"
          type="button"
          @click="refreshVariants"
        >
          Refresh Variants
        </button>
        <span class="mono small muted">run: {{ selectedRunId }}</span>
      </div>
    </div>

    <div
      v-if="generatedAssets.length"
      class="grid"
    >
      <div
        v-for="a in generatedAssets"
        :key="(a as any).sha256 || (a as any).url"
        class="card"
      >
        <img
          v-if="(a as any).url"
          class="img"
          :src="resolveAssetUrl((a as any).url)"
        >
        <div class="meta">
          <div class="mono small">
            {{ (a as any).sha256 || "—" }}
          </div>

          <div class="rowBtns">
            <button
              class="btn small"
              :disabled="Boolean(attachDisabledReason(a)) || isAttaching === (a as any).sha256"
              :title="attachDisabledReason(a) || 'Attach this asset to the selected run'"
              @click="doAttach(a)"
            >
              {{ isAttaching === (a as any).sha256 ? "Attaching…" : "Attach" }}
            </button>

            <button
              class="btn small"
              :disabled="!_variantForAsset(a)"
              :title="_variantForAsset(a) ? 'Open review panel' : 'Attach first'"
              @click="toggleReview(a)"
            >
              {{ openReviewFor === (_variantForAsset(a)?.advisory_id ?? null) ? "Close Review" : "Review" }}
            </button>

            <button
              class="btn small primary"
              :disabled="Boolean(promoteDisabledReason(a)) || isPromoting === _advisoryIdForAsset(a)"
              :title="promoteDisabledReason(a) || 'Promote reviewed variant to manufacturing'"
              @click="doPromote(a)"
            >
              {{ isPromoting === _advisoryIdForAsset(a) ? "Promoting…" : "Promote" }}
            </button>
          </div>

          <div
            v-if="_variantForAsset(a)"
            class="badges"
          >
            <span
              class="badge"
              :data-b="(_variantForAsset(a)?.status ?? 'NEW')"
              :title="(_variantForAsset(a) as any)?.risk_level ? `Risk: ${(_variantForAsset(a) as any)?.risk_level}` : 'Risk: —'"
            >{{ _variantForAsset(a)?.status }}</span>
            <span
              v-if="_variantForAsset(a)?.rejected"
              class="badge warn"
              data-b="REJECTED"
              :title="rejectionHover(_variantForAsset(a))"
            >REJECTED</span>
            <span
              v-if="_variantForAsset(a)?.promoted"
              class="badge"
              data-b="PROMOTED"
            >PROMOTED</span>
          </div>

          <!-- micro-follow: per-asset quick reject/promote surface -->
          <div
            v-if="selectedRunId && _advisoryIdForAsset(a)"
            class="assetOps"
          >
            <div class="row">
              <button
                class="btn small primary"
                type="button"
                :disabled="Boolean(promoteDisabledReason(a)) || !!busyByAdvisoryId[_advisoryIdForAsset(a)!]"
                :title="promoteDisabledReason(a) || 'Promote to manufacturing candidate'"
                @click="quickPromote(_advisoryIdForAsset(a)!)"
              >
                {{ busyByAdvisoryId[_advisoryIdForAsset(a)!] === 'promote' ? 'Promoting…' : 'Quick Promote' }}
              </button>

              <button
                v-if="_variantForAsset(a)?.rejected"
                class="btn small"
                type="button"
                :disabled="!!canUndoReject(_variantForAsset(a)) || !!busyByAdvisoryId[_advisoryIdForAsset(a)!]"
                :title="canUndoReject(_variantForAsset(a)) || 'Clear rejection (Undo Reject)'"
                @click="undoReject(_advisoryIdForAsset(a)!)"
              >
                {{ busyByAdvisoryId[_advisoryIdForAsset(a)!] === 'review' ? 'Clearing…' : 'Undo Reject' }}
              </button>

              <select
                class="select small"
                :disabled="!!busyByAdvisoryId[_advisoryIdForAsset(a)!]"
                title="Reject this variant (records reason code)"
                @change="(ev:any) => { const v = ev?.target?.value as RejectReasonCode; if (v) quickReject(_advisoryIdForAsset(a)!, v); ev.target.value=''; }"
              >
                <option value="">
                  Quick Reject…
                </option>
                <option value="GEOMETRY_UNSAFE">
                  GEOMETRY_UNSAFE
                </option>
                <option value="TEXT_REQUIRES_OUTLINE">
                  TEXT_REQUIRES_OUTLINE
                </option>
                <option value="AESTHETIC">
                  AESTHETIC
                </option>
                <option value="DUPLICATE">
                  DUPLICATE
                </option>
                <option value="OTHER">
                  OTHER
                </option>
              </select>
            </div>
          </div>

          <div
            v-if="openReviewFor === (_variantForAsset(a)?.advisory_id ?? null)"
            class="reviewSlot"
          >
            <VariantReviewPanel
              :run-id="String(selectedRunId)"
              :advisory-id="String(_variantForAsset(a)?.advisory_id)"
              :filename="(_variantForAsset(a)?.filename ?? null) as any"
              :mime="(_variantForAsset(a)?.mime ?? null) as any"
              :initial="_variantForAsset(a) as any"
              @saved="async () => { await refreshVariants(); _toastOk('Review saved.'); }"
              @error="_toastErr"
            />
          </div>
        </div>
      </div>
    </div>

    <div
      v-else
      class="empty"
    >
      Generate images to begin.
    </div>
  </div>
</template>

<style scoped>
.wrap { padding: 14px; }
.top { margin-bottom: 12px; }
.controls { display: flex; flex-wrap: wrap; gap: 10px; align-items: center; }
.input, .select {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
}
.btn {
  border: 1px solid rgba(0,0,0,0.18);
  border-radius: 12px;
  padding: 8px 12px;
  font-size: 13px;
  background: white;
  cursor: pointer;
}
.btn.primary { background: rgba(0,0,0,0.08); font-weight: 600; }
.btn.small { padding: 6px 10px; font-size: 12px; border-radius: 10px; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }

.toast { margin-top: 10px; padding: 8px 10px; border-radius: 12px; border: 1px solid rgba(0,0,0,0.14); font-size: 13px; }
.toast.err { background: rgba(255, 235, 235, 0.9); }
.toast.ok { background: rgba(235, 255, 235, 0.9); }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
}
.card {
  border: 1px solid rgba(0,0,0,0.14);
  border-radius: 16px;
  overflow: hidden;
  background: rgba(255,255,255,0.7);
}
.img { width: 100%; height: 220px; object-fit: cover; display: block; }
.meta { padding: 10px; display: flex; flex-direction: column; gap: 8px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.small { font-size: 12px; opacity: 0.8; }
.rowBtns { display: flex; gap: 8px; flex-wrap: wrap; }
.badges { display: flex; gap: 8px; flex-wrap: wrap; }
.badge {
  font-size: 11px;
  padding: 3px 9px;
  border-radius: 999px;
  border: 1px solid rgba(0,0,0,0.14);
  background: rgba(0,0,0,0.03);
}
.reviewSlot { margin-top: 6px; }
.empty { opacity: 0.7; padding: 20px; }

/* micro-follow: run action strip + per-asset ops */
.runActions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 10px 0 0;
}
.muted { opacity: 0.6; }
.assetOps {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.assetOps .row {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
.badge.warn {
  cursor: help;
}
.select.small {
  padding: 6px 10px;
  font-size: 12px;
  border-radius: 10px;
}
</style>
