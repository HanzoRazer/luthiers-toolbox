<script setup lang="ts">
/**
 * Physics Summary Badges (Wave 12)
 *
 * Compact badge strip for physics results:
 * - Chipload
 * - Heat
 * - Deflection
 * - Rim Speed
 * - Kickback
 */
import { computed } from "vue";
import type { CamPhysicsResults } from "@/stores/camAdvisorStore";

const props = defineProps<{
  physics: CamPhysicsResults | null;
}>();

// ─────────────────────────────────────────────────────────────────────────────
// Computed labels and styles
// ─────────────────────────────────────────────────────────────────────────────

const chiploadLabel = computed(() => {
  const c = props.physics?.chipload as
    | { chipload_mm?: number; in_range?: boolean; message?: string }
    | undefined;
  if (!c) return "Chipload: —";
  const val = c.chipload_mm ?? null;
  const inRange = c.in_range ?? false;
  return val !== null
    ? `Chipload: ${val.toFixed(3)} mm/tooth (${inRange ? "OK" : "OUT"})`
    : `Chipload: —`;
});

const chiploadClass = computed(() => {
  const c = props.physics?.chipload as { in_range?: boolean } | undefined;
  if (!c) return "bg-slate-700 text-slate-300";
  return c.in_range
    ? "bg-emerald-800 text-emerald-100"
    : "bg-amber-800 text-amber-100";
});

const heatLabel = computed(() => {
  const h = props.physics?.heat as
    | { category?: string; heat_risk?: number; message?: string }
    | undefined;
  if (!h) return "Heat: —";
  const cat = h.category ?? "UNKNOWN";
  return `Heat: ${cat}`;
});

const heatClass = computed(() => {
  const h = props.physics?.heat as { category?: string } | undefined;
  if (!h) return "bg-slate-700 text-slate-300";
  const cat = (h.category ?? "").toUpperCase();
  if (cat === "COLD") return "bg-sky-800 text-sky-100";
  if (cat === "WARM") return "bg-amber-800 text-amber-100";
  if (cat === "HOT") return "bg-red-800 text-red-100";
  return "bg-slate-700 text-slate-300";
});

const deflectionLabel = computed(() => {
  const d = props.physics?.deflection as
    | { deflection_mm?: number; risk?: string; message?: string }
    | undefined;
  if (!d) return "Deflection: —";
  const val = d.deflection_mm ?? null;
  const risk = d.risk ?? "UNKNOWN";
  return val !== null
    ? `Deflection: ${val.toFixed(3)} mm (${risk})`
    : `Deflection: —`;
});

const deflectionClass = computed(() => {
  const d = props.physics?.deflection as { risk?: string } | undefined;
  if (!d) return "bg-slate-700 text-slate-300";
  const risk = (d.risk ?? "").toUpperCase();
  if (risk === "GREEN") return "bg-emerald-800 text-emerald-100";
  if (risk === "YELLOW") return "bg-amber-800 text-amber-100";
  if (risk === "RED") return "bg-red-800 text-red-100";
  return "bg-slate-700 text-slate-300";
});

const rimSpeedLabel = computed(() => {
  const r = props.physics?.rim_speed as
    | {
        surface_speed_m_per_s?: number;
        within_limits?: boolean;
        message?: string;
      }
    | undefined;
  if (!r) return "Rim Speed: —";
  const val = r.surface_speed_m_per_s ?? null;
  const ok = r.within_limits ?? false;
  return val !== null
    ? `Rim Speed: ${val.toFixed(1)} m/s (${ok ? "OK" : "OUT"})`
    : `Rim Speed: —`;
});

const rimSpeedClass = computed(() => {
  const r = props.physics?.rim_speed as { within_limits?: boolean } | undefined;
  if (!r) return "bg-slate-700 text-slate-300";
  return r.within_limits
    ? "bg-emerald-800 text-emerald-100"
    : "bg-amber-800 text-amber-100";
});

const kickbackLabel = computed(() => {
  const k = props.physics?.kickback as
    | { risk_score?: number; category?: string; message?: string }
    | undefined;
  if (!k) return "Kickback: —";
  const cat = k.category ?? "UNKNOWN";
  return `Kickback: ${cat}`;
});

const kickbackClass = computed(() => {
  const k = props.physics?.kickback as { category?: string } | undefined;
  if (!k) return "bg-slate-700 text-slate-300";
  const cat = (k.category ?? "").toUpperCase();
  if (cat === "LOW") return "bg-emerald-800 text-emerald-100";
  if (cat === "MEDIUM") return "bg-amber-800 text-amber-100";
  if (cat === "HIGH") return "bg-red-800 text-red-100";
  return "bg-slate-700 text-slate-300";
});
</script>

<template>
  <div class="flex flex-wrap gap-2 text-xs">
    <span
      class="inline-flex items-center rounded-full px-2 py-1"
      :class="chiploadClass"
    >
      {{ chiploadLabel }}
    </span>
    <span
      class="inline-flex items-center rounded-full px-2 py-1"
      :class="heatClass"
    >
      {{ heatLabel }}
    </span>
    <span
      class="inline-flex items-center rounded-full px-2 py-1"
      :class="deflectionClass"
    >
      {{ deflectionLabel }}
    </span>
    <span
      class="inline-flex items-center rounded-full px-2 py-1"
      :class="rimSpeedClass"
    >
      {{ rimSpeedLabel }}
    </span>
    <span
      class="inline-flex items-center rounded-full px-2 py-1"
      :class="kickbackClass"
    >
      {{ kickbackLabel }}
    </span>
  </div>
</template>
