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
import VariantReviewPanel from "./components/VariantReviewPanel.vue";

// Vision feature API (existing module)
import {
  generateImages,
  attachAdvisoryToRun,
  listRecentRuns,
  getProviders,
  type VisionAsset,
  type ProviderName,
} from "./api/visionApi";

// RMOS typed SDK (canonical)
import {
  listAdvisoryVariants,
  promoteAdvisoryVariant,
  type AdvisoryVariantSummary,
} from "@/sdk/rmos/runs";

// Local type for run summaries from visionApi
type RunSummary = {
  run_id: string;
  created_at_utc?: string;
  event_type?: string;
  status?: string;
};

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
  if (!selectedRunId.value) return;

  isAttaching.value = sha;
  try {
    // IMPORTANT: trust attach response for advisory_id
    const res = await attachAdvisoryToRun(selectedRunId.value, {
      advisory_id: sha, // canonical
      kind: "advisory",
    });

    const advisoryId = (res?.advisory_id ?? sha) as string;
    advisoryIdByAssetSha.value = { ...advisoryIdByAssetSha.value, [sha]: advisoryId };

    await refreshVariants();
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
        <input v-model="prompt" class="input" placeholder="Prompt…" />
        <select v-model="provider" class="select">
          <option value="openai">openai</option>
          <option value="stub">stub</option>
        </select>
        <select v-model="numImages" class="select">
          <option :value="1">1</option>
          <option :value="2">2</option>
          <option :value="3">3</option>
        </select>
        <button class="btn primary" :disabled="!canGenerate" @click="doGenerate">
          {{ isGenerating ? "Generating…" : "Generate" }}
        </button>

        <select v-model="selectedRunId" class="select" @change="refreshVariants">
          <option :value="null">Select run…</option>
          <option v-for="r in runs" :key="r.run_id" :value="r.run_id">
            {{ r.run_id }}
          </option>
        </select>
      </div>

      <div v-if="error" class="toast err">{{ error }}</div>
      <div v-if="success" class="toast ok">{{ success }}</div>
    </div>

    <div class="grid" v-if="generatedAssets.length">
      <div v-for="a in generatedAssets" :key="(a as any).sha256 || (a as any).url" class="card">
        <img v-if="(a as any).url" class="img" :src="(a as any).url" />
        <div class="meta">
          <div class="mono small">{{ (a as any).sha256 || "—" }}</div>

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

          <div class="badges" v-if="_variantForAsset(a)">
            <span class="badge" :data-b="(_variantForAsset(a)?.status ?? 'NEW')">{{ _variantForAsset(a)?.status }}</span>
            <span class="badge" v-if="_variantForAsset(a)?.rejected" data-b="REJECTED">REJECTED</span>
            <span class="badge" v-if="_variantForAsset(a)?.promoted" data-b="PROMOTED">PROMOTED</span>
          </div>

          <div v-if="openReviewFor === (_variantForAsset(a)?.advisory_id ?? null)" class="reviewSlot">
            <VariantReviewPanel
              :runId="String(selectedRunId)"
              :advisoryId="String(_variantForAsset(a)?.advisory_id)"
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

    <div v-else class="empty">
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
</style>
