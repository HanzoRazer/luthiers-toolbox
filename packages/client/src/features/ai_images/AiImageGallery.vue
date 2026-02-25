<script setup lang="ts">
/**
 * AI Image Gallery — RMOS-integrated Gallery with Attach/Review/Promote
 *
 * Review Hardening Bundle (A+B): State-aware buttons + inline review panel
 * Wired to runs.ts canonical SDK and visionApi feature module.
 *
 * @package features/ai_images
 */
import { onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { SUCCESS_TOAST_MS, ERROR_TOAST_MS } from '@/constants/timing'
import VariantReviewPanel from './components/VariantReviewPanel.vue'
import AssetQuickOpsPanel from './components/AssetQuickOpsPanel.vue'
import { getProviders, listRecentRuns } from './api/visionApi'
import type { RejectReasonCode } from '@/sdk/rmos/runs'

// Composables
import {
  useGalleryState,
  useVariantHelpers,
  useVariantActions,
  useImageGeneration,
  useAssetAttachment
} from './composables'

const router = useRouter()

/** Base URL for cross-origin API deployments */
const API_BASE = (import.meta as any).env?.VITE_API_BASE || ''

/** Resolve asset URL to full URL (handles cross-origin deployments). */
function resolveAssetUrl(url: string | undefined): string {
  if (!url) return '/placeholder.svg'
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  return `${API_BASE}${url}`
}

// Toast helpers
let _toastOkTimer: number | null = null
let _toastErrTimer: number | null = null

function _toastOk(msg: string) {
  success.value = msg
  if (_toastOkTimer) clearTimeout(_toastOkTimer)
  _toastOkTimer = window.setTimeout(() => (success.value = null), SUCCESS_TOAST_MS)
}

function _toastErr(msg: string) {
  error.value = msg
  if (_toastErrTimer) clearTimeout(_toastErrTimer)
  _toastErrTimer = window.setTimeout(() => (error.value = null), ERROR_TOAST_MS)
}

onBeforeUnmount(() => {
  if (_toastOkTimer) clearTimeout(_toastOkTimer)
  if (_toastErrTimer) clearTimeout(_toastErrTimer)
})

// Gallery state
const {
  prompt,
  provider,
  numImages,
  size,
  quality,
  generatedAssets,
  selectedRunId,
  runs,
  providers,
  isGenerating,
  isAttaching,
  isPromoting,
  error,
  success,
  openReviewFor,
  variantById,
  advisoryIdByAssetSha,
  busyByAdvisoryId,
  lastAttachedRunId,
  canGenerate
} = useGalleryState()

// Variant helpers
const {
  advisoryIdForAsset: _advisoryIdForAsset,
  variantForAsset: _variantForAsset,
  attachDisabledReason,
  promoteDisabledReason,
  rejectionHover,
  canUndoReject
} = useVariantHelpers(selectedRunId, variantById, advisoryIdByAssetSha, busyByAdvisoryId)

// Variant actions
const { refreshVariants, quickReject, undoReject, quickPromote } = useVariantActions(
  selectedRunId,
  variantById,
  busyByAdvisoryId,
  _toastOk,
  _toastErr
)

// Image generation
const { doGenerate } = useImageGeneration(
  prompt,
  provider,
  numImages,
  size,
  quality,
  generatedAssets,
  isGenerating,
  canGenerate,
  selectedRunId,
  refreshVariants,
  _toastOk,
  _toastErr
)

// Asset attachment
const { doAttach, doPromote, toggleReview } = useAssetAttachment(
  selectedRunId,
  runs,
  isAttaching,
  isPromoting,
  advisoryIdByAssetSha,
  lastAttachedRunId,
  openReviewFor,
  attachDisabledReason,
  promoteDisabledReason,
  _advisoryIdForAsset,
  _variantForAsset,
  refreshVariants,
  _toastOk,
  _toastErr
)

// Navigation helpers
function goToRunReview(runId: string) {
  router.push({ name: 'RunVariantsReview', params: { run_id: runId } })
}

function goToReview(runId?: string | null) {
  const id = runId ?? selectedRunId.value ?? lastAttachedRunId.value
  if (!id) return
  router.push({ name: 'RunVariantsReview', params: { run_id: id } })
}

// Init
onMounted(async () => {
  try {
    const res = await getProviders()
    providers.value = res.providers ?? []
  } catch {}
  try {
    const res = await listRecentRuns()
    runs.value = (res as any).runs ?? []
    if (!selectedRunId.value && runs.value.length) {
      selectedRunId.value = runs.value[0].run_id as any
    }
  } catch {}
  if (selectedRunId.value) await refreshVariants()
})
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
          <AssetQuickOpsPanel
            v-if="selectedRunId && _advisoryIdForAsset(a)"
            :advisory-id="_advisoryIdForAsset(a)!"
            :variant="_variantForAsset(a)"
            :promote-disabled-reason="promoteDisabledReason(a)"
            :can-undo-reject-reason="canUndoReject(_variantForAsset(a))"
            :busy="busyByAdvisoryId[_advisoryIdForAsset(a)!] ?? null"
            @quick-promote="quickPromote"
            @undo-reject="undoReject"
            @quick-reject="quickReject"
          />

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
