// packages/client/src/stores/fretSlotsCamStore.ts
/**
 * Fret Slots CAM Store
 * 
 * Manages state for fret slot CAM preview:
 * - Calls /api/cam/fret_slots/preview
 * - Stores slots and RMOS messages
 * - Derives per-fret and per-string risk maps for overlays
 * 
 * Wave 6 Implementation (Fret Slots UI Overlay Bundle)
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type {
  FretSlotsPreviewRequest,
  FretSlotsPreviewResponse,
  FretSlot,
  RmosMessage,
  RmosSeverity,
  FretRiskSummary,
  FretStringRisk,
} from "@/types/fretSlots";


function severityRank(sev: RmosSeverity): number {
  switch (sev) {
    case "info": return 0;
    case "warning": return 1;
    case "error": return 2;
    case "fatal": return 3;
    default: return 0;
  }
}


export const useFretSlotsCamStore = defineStore("fretSlotsCam", () => {
  // State
  const loading = ref(false);
  const lastRequest = ref<FretSlotsPreviewRequest | null>(null);
  const slots = ref<FretSlot[]>([]);
  const messages = ref<RmosMessage[]>([]);
  const error = ref<string | null>(null);

  // Actions
  async function fetchPreview(req: FretSlotsPreviewRequest): Promise<void> {
    loading.value = true;
    error.value = null;
    lastRequest.value = req;

    try {
      const res = await fetch("/api/cam/fret_slots/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(req),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }

      const data = (await res.json()) as FretSlotsPreviewResponse;
      slots.value = data.slots ?? [];
      messages.value = data.messages ?? [];
    } catch (err: any) {
      console.error("Failed to fetch fret-slots preview:", err);
      error.value = err?.message ?? String(err);
      slots.value = [];
      messages.value = [];
    } finally {
      loading.value = false;
    }
  }

  function reset(): void {
    loading.value = false;
    lastRequest.value = null;
    slots.value = [];
    messages.value = [];
    error.value = null;
  }

  // Computed: Per-fret risk map
  const fretRiskMap = computed<Record<number, FretRiskSummary>>(() => {
    const map: Record<number, FretRiskSummary> = {};

    for (const msg of messages.value) {
      const ctxFret = (msg.context?.fret as number | undefined) ?? null;
      if (ctxFret === null || Number.isNaN(ctxFret)) {
        continue;
      }

      if (!map[ctxFret]) {
        map[ctxFret] = {
          fret: ctxFret,
          worstSeverity: null,
          messages: [],
        };
      }

      map[ctxFret].messages.push(msg);

      const sev = msg.severity as RmosSeverity;
      const current = map[ctxFret].worstSeverity;
      if (!current || severityRank(sev) > severityRank(current)) {
        map[ctxFret].worstSeverity = sev;
      }
    }

    return map;
  });

  // Computed: Per-string-per-fret risk map (for matrix overlay)
  const stringFretRiskMap = computed<Record<string, FretStringRisk>>(() => {
    const map: Record<string, FretStringRisk> = {};

    for (const msg of messages.value) {
      const fret = (msg.context?.fret as number | undefined) ?? null;
      const stringIdx = (msg.context?.string_index as number | undefined) ?? null;

      if (fret === null || stringIdx === null) {
        continue;
      }

      const key = `${fret}-${stringIdx}`;
      if (!map[key]) {
        map[key] = {
          fret,
          stringIndex: stringIdx,
          severity: null,
          messages: [],
        };
      }

      map[key].messages.push(msg);

      const sev = msg.severity as RmosSeverity;
      const current = map[key].severity;
      if (!current || severityRank(sev) > severityRank(current)) {
        map[key].severity = sev;
      }
    }

    return map;
  });

  const hasAnyRisk = computed(() => Object.keys(fretRiskMap.value).length > 0);

  const worstOverallSeverity = computed<RmosSeverity | null>(() => {
    if (messages.value.length === 0) return null;
    let worst: RmosSeverity | null = null;
    for (const msg of messages.value) {
      if (!worst || severityRank(msg.severity) > severityRank(worst)) {
        worst = msg.severity;
      }
    }
    return worst;
  });

  const errorCount = computed(() => 
    messages.value.filter(m => m.severity === "error" || m.severity === "fatal").length
  );

  const warningCount = computed(() => 
    messages.value.filter(m => m.severity === "warning").length
  );

  return {
    // State
    loading,
    lastRequest,
    slots,
    messages,
    error,
    
    // Computed
    fretRiskMap,
    stringFretRiskMap,
    hasAnyRisk,
    worstOverallSeverity,
    errorCount,
    warningCount,
    
    // Actions
    fetchPreview,
    reset,
  };
});
