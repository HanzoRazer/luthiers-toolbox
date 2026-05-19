/**
 * Nut Slot CAM Preview Store
 *
 * CAM Dev Order 2A: Frontend preview state for nut slot toolpath visualization.
 * Backend contract from commit 64d7ebc7 — do not modify backend.
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import {
  previewNutSlots,
  type NutSlotPreviewRequest,
  type NutSlotPreviewResponse,
  type CamGate,
  type CamIssue,
} from "@/sdk/endpoints/cam";
import {
  buildNutCamPrefillFromNeckA,
  type NeckANutState,
} from "@/utils/cam/neckAToNutCam";

// ---------------------------------------------------------------------------
// Default Values (6-string guitar)
// ---------------------------------------------------------------------------

const DEFAULT_6_STRING: NutSlotPreviewRequest = {
  nut_width_mm: 43.0,
  num_strings: 6,
  edge_offset_bass_mm: 3.5,
  edge_offset_treble_mm: 3.5,
  string_positions_x_mm: null,
  slot_length_mm: 4.0,
  slot_depth_mm: 1.5,
  slot_width_mm: 0.56,
  stock_thickness_mm: 6.0,
  tool_diameter_mm: 0.5,
  safe_z_mm: 5.0,
};

// ---------------------------------------------------------------------------
// Store
// ---------------------------------------------------------------------------

export const useNutSlotCamStore = defineStore("nutSlotCam", () => {
  // ── Input State ──────────────────────────────────────────────────────────
  const nutWidthMm = ref(DEFAULT_6_STRING.nut_width_mm);
  const numStrings = ref(DEFAULT_6_STRING.num_strings);
  const edgeOffsetBassMm = ref(DEFAULT_6_STRING.edge_offset_bass_mm);
  const edgeOffsetTrebleMm = ref(DEFAULT_6_STRING.edge_offset_treble_mm);
  const slotLengthMm = ref(DEFAULT_6_STRING.slot_length_mm);
  const slotDepthMm = ref(DEFAULT_6_STRING.slot_depth_mm);
  const slotWidthMm = ref(DEFAULT_6_STRING.slot_width_mm);
  const stockThicknessMm = ref(DEFAULT_6_STRING.stock_thickness_mm);
  const toolDiameterMm = ref(DEFAULT_6_STRING.tool_diameter_mm);
  const safeZMm = ref(DEFAULT_6_STRING.safe_z_mm ?? 5.0);

  // ── Preview State ────────────────────────────────────────────────────────
  const previewResult = ref<NutSlotPreviewResponse | null>(null);
  const previewLoading = ref(false);
  const previewError = ref<string | null>(null);

  // ── Prefill Source (Dev Order 3B) ────────────────────────────────────────
  const prefillSource = ref<"defaults" | "neck_a" | null>(null);

  // ── Computed ─────────────────────────────────────────────────────────────
  const gate = computed<CamGate | null>(() => previewResult.value?.gate ?? null);

  const hasPreview = computed(() => previewResult.value !== null);

  const toolpaths = computed(() => previewResult.value?.toolpaths ?? []);

  const warnings = computed(() => previewResult.value?.warnings ?? []);

  const errors = computed(() => previewResult.value?.errors ?? []);

  const issues = computed(() => previewResult.value?.issues ?? []);

  const redIssues = computed(() =>
    issues.value.filter((i: CamIssue) => i.severity === "red")
  );

  const yellowIssues = computed(() =>
    issues.value.filter((i: CamIssue) => i.severity === "yellow")
  );

  const statistics = computed(() => previewResult.value?.statistics ?? null);

  const gateColor = computed(() => {
    switch (gate.value) {
      case "green":
        return "#10b981";
      case "yellow":
        return "#f59e0b";
      case "red":
        return "#ef4444";
      default:
        return "#6b7280";
    }
  });

  const gateBgColor = computed(() => {
    switch (gate.value) {
      case "green":
        return "#065f46";
      case "yellow":
        return "#78350f";
      case "red":
        return "#7f1d1d";
      default:
        return "#374151";
    }
  });

  const gateTextColor = computed(() => {
    switch (gate.value) {
      case "green":
        return "#6ee7b7";
      case "yellow":
        return "#fcd34d";
      case "red":
        return "#fca5a5";
      default:
        return "#d1d5db";
    }
  });

  const canDownloadPreviewJson = computed(() => {
    return !!previewResult.value && previewResult.value.gate !== "red";
  });

  // ── Actions ──────────────────────────────────────────────────────────────

  function loadDefaults(): void {
    nutWidthMm.value = DEFAULT_6_STRING.nut_width_mm;
    numStrings.value = DEFAULT_6_STRING.num_strings;
    edgeOffsetBassMm.value = DEFAULT_6_STRING.edge_offset_bass_mm;
    edgeOffsetTrebleMm.value = DEFAULT_6_STRING.edge_offset_treble_mm;
    slotLengthMm.value = DEFAULT_6_STRING.slot_length_mm;
    slotDepthMm.value = DEFAULT_6_STRING.slot_depth_mm;
    slotWidthMm.value = DEFAULT_6_STRING.slot_width_mm;
    stockThicknessMm.value = DEFAULT_6_STRING.stock_thickness_mm;
    toolDiameterMm.value = DEFAULT_6_STRING.tool_diameter_mm;
    safeZMm.value = DEFAULT_6_STRING.safe_z_mm ?? 5.0;
    prefillSource.value = "defaults";
    previewResult.value = null;
    previewError.value = null;
  }

  async function generatePreview(): Promise<void> {
    previewLoading.value = true;
    previewError.value = null;

    const request: NutSlotPreviewRequest = {
      nut_width_mm: nutWidthMm.value,
      num_strings: numStrings.value,
      edge_offset_bass_mm: edgeOffsetBassMm.value,
      edge_offset_treble_mm: edgeOffsetTrebleMm.value,
      string_positions_x_mm: null,
      slot_length_mm: slotLengthMm.value,
      slot_depth_mm: slotDepthMm.value,
      slot_width_mm: slotWidthMm.value,
      stock_thickness_mm: stockThicknessMm.value,
      tool_diameter_mm: toolDiameterMm.value,
      safe_z_mm: safeZMm.value,
    };

    try {
      previewResult.value = await previewNutSlots(request);
    } catch (err) {
      previewError.value = err instanceof Error ? err.message : String(err);
      previewResult.value = null;
    } finally {
      previewLoading.value = false;
    }
  }

  function clearPreview(): void {
    previewResult.value = null;
    previewError.value = null;
  }

  function makeNutSlotPreviewFilename(): string {
    const now = new Date();
    const pad = (n: number) => String(n).padStart(2, "0");
    const stamp =
      `${now.getFullYear()}${pad(now.getMonth() + 1)}${pad(now.getDate())}-` +
      `${pad(now.getHours())}${pad(now.getMinutes())}${pad(now.getSeconds())}`;
    return `nut-slot-preview-${stamp}.toolpath.json`;
  }

  function downloadJson(filename: string, data: unknown): void {
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function downloadPreviewJson(): void {
    if (!previewResult.value) return;
    if (previewResult.value.gate === "red") return;

    if (previewResult.value.gate === "yellow") {
      const confirmed = window.confirm(
        "This CAM preview has warnings. Download JSON for review only?"
      );
      if (!confirmed) return;
    }

    const filename = makeNutSlotPreviewFilename();
    downloadJson(filename, previewResult.value);
  }

  /**
   * Load CAM form values from NECK-A setup workflow state.
   *
   * Dev Order 3B: One-way handoff, advisory only.
   * Does NOT auto-preview or auto-export.
   * CAM validation still required after prefill.
   */
  function loadFromNeckA(neckAState: NeckANutState): void {
    const prefill = buildNutCamPrefillFromNeckA(neckAState);

    if (prefill.nut_width_mm !== undefined) nutWidthMm.value = prefill.nut_width_mm;
    if (prefill.num_strings !== undefined) numStrings.value = prefill.num_strings;
    if (prefill.edge_offset_bass_mm !== undefined) edgeOffsetBassMm.value = prefill.edge_offset_bass_mm;
    if (prefill.edge_offset_treble_mm !== undefined) edgeOffsetTrebleMm.value = prefill.edge_offset_treble_mm;
    if (prefill.slot_length_mm !== undefined) slotLengthMm.value = prefill.slot_length_mm;
    if (prefill.slot_depth_mm !== undefined) slotDepthMm.value = prefill.slot_depth_mm;
    if (prefill.slot_width_mm !== undefined) slotWidthMm.value = prefill.slot_width_mm;
    if (prefill.stock_thickness_mm !== undefined) stockThicknessMm.value = prefill.stock_thickness_mm;
    if (prefill.tool_diameter_mm !== undefined) toolDiameterMm.value = prefill.tool_diameter_mm;
    if (prefill.safe_z_mm !== undefined) safeZMm.value = prefill.safe_z_mm;

    prefillSource.value = "neck_a";
    previewResult.value = null;
    previewError.value = null;
  }

  return {
    // Input state
    nutWidthMm,
    numStrings,
    edgeOffsetBassMm,
    edgeOffsetTrebleMm,
    slotLengthMm,
    slotDepthMm,
    slotWidthMm,
    stockThicknessMm,
    toolDiameterMm,
    safeZMm,

    // Preview state
    previewResult,
    previewLoading,
    previewError,
    prefillSource,

    // Computed
    gate,
    hasPreview,
    toolpaths,
    warnings,
    errors,
    issues,
    redIssues,
    yellowIssues,
    statistics,
    gateColor,
    gateBgColor,
    gateTextColor,
    canDownloadPreviewJson,

    // Actions
    loadDefaults,
    generatePreview,
    clearPreview,
    downloadPreviewJson,
    loadFromNeckA,
  };
});
