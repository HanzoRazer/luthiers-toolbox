/**
 * useTimeEstimates — composable for realistic machining time estimates.
 *
 * Applies safety margins for acceleration, material, operator skill,
 * and tool changes on top of theoretical cycle time.
 */

import { computed, type Ref } from "vue";
import type { MoveSegment } from "@/sdk/endpoints/cam/simulate";

export interface TimeEstimateConfig {
  rapidMargin: number;
  cutMargin: number;
  toolChangeTimeSec: number;
  setupTimeSec: number;
  material: "aluminum" | "steel" | "titanium" | "plastic" | "wood";
  skill: "beginner" | "intermediate" | "expert";
}

const DEFAULTS: TimeEstimateConfig = {
  rapidMargin: 1.3,
  cutMargin: 1.2,
  toolChangeTimeSec: 30,
  setupTimeSec: 300,
  material: "aluminum",
  skill: "intermediate",
};

const MATERIAL_FACTOR: Record<string, number> = {
  aluminum: 1.0,
  steel: 1.5,
  titanium: 2.5,
  plastic: 0.8,
  wood: 0.9,
};
const SKILL_FACTOR: Record<string, number> = {
  beginner: 1.3,
  intermediate: 1.1,
  expert: 1.0,
};

function fmtTime(sec: number): string {
  if (sec < 60) return `${Math.round(sec)}s`;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  if (m < 60) return `${m}m ${s}s`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}

export function useTimeEstimates(
  segments: Ref<MoveSegment[]>,
  cfg: Partial<TimeEstimateConfig> = {},
) {
  const c = { ...DEFAULTS, ...cfg };

  const theoreticalSec = computed(() =>
    segments.value.reduce((s, seg) => s + seg.duration_ms, 0) / 1000,
  );

  const toolChanges = computed(() => {
    const tools = new Set<number>();
    for (const seg of segments.value) {
      const m = seg.line_text.toUpperCase().match(/T(\d+)/);
      if (m) tools.add(parseInt(m[1], 10));
    }
    return Math.max(0, tools.size - 1);
  });

  const adjustedSec = computed(() => {
    let total = 0;
    for (const seg of segments.value) {
      const margin = seg.type === "rapid" ? c.rapidMargin : c.cutMargin;
      total += (seg.duration_ms / 1000) * margin;
    }
    total *= MATERIAL_FACTOR[c.material] ?? 1;
    total *= SKILL_FACTOR[c.skill] ?? 1;
    total += toolChanges.value * c.toolChangeTimeSec;
    return total;
  });

  const withSetup = computed(() => adjustedSec.value + c.setupTimeSec);

  const estimates = computed(() => ({
    machine: { seconds: Math.ceil(theoreticalSec.value), formatted: fmtTime(theoreticalSec.value) },
    realistic: { seconds: Math.ceil(adjustedSec.value), formatted: fmtTime(adjustedSec.value) },
    withSetup: { seconds: Math.ceil(withSetup.value), formatted: fmtTime(withSetup.value) },
    toolChanges: toolChanges.value,
  }));

  return { estimates };
}
