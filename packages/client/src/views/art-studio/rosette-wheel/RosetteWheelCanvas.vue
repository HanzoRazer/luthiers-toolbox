<script setup lang="ts">
/**
 * RosetteWheelCanvas — SVG wheel rendering component
 * Extracted from RosetteWheelView for decomposition
 */
import { computed } from "vue";
import { useRosetteWheelStore } from "@/stores/useRosetteWheelStore";

const store = useRosetteWheelStore();

// ── Props ───────────────────────────────────────────────────────────────
const props = defineProps<{
  hoveredCellKey: string | null;
  mfgOverlayCells: { ri: number; si: number; sev: string }[];
}>();

// ── Emits ───────────────────────────────────────────────────────────────
const emit = defineEmits<{
  (e: "cellClick", ri: number, si: number): void;
  (e: "cellEnter", ri: number, si: number): void;
  (e: "cellLeave"): void;
  (e: "cellDrop", ri: number, si: number): void;
}>();

// ── SVG geometry constants ─────────────────────────────────────────────
const CX = 310;
const CY = 310;
const SVG_W = 620;
const SVG_H = 620;

// ── Computed helpers ───────────────────────────────────────────────────
const segAng = computed(() => 360 / store.numSegs);
const ringDefs = computed(() => store.ringDefs);

// ── Guide circle radii ─────────────────────────────────────────────────
const GUIDE_CIRCLES = [
  { r: 150, dash: false, tab: false },
  { r: 190, dash: false, tab: false },
  { r: 200, dash: true, tab: true },
  { r: 210, dash: false, tab: false },
  { r: 300, dash: false, tab: false },
  { r: 312, dash: true, tab: true },
  { r: 320, dash: false, tab: false },
  { r: 350, dash: false, tab: false },
];

// ── SVG math helpers ───────────────────────────────────────────────────
function rad(deg: number) { return deg * Math.PI / 180; }
function ptOnCircle(r: number, deg: number): [number, number] {
  const a = rad(deg - 90);
  return [CX + r * Math.cos(a), CY + r * Math.sin(a)];
}
function fmt(n: number) { return n.toFixed(3); }

function arcCellPath(r1: number, r2: number, a1: number, a2: number): string {
  const [x1i, y1i] = ptOnCircle(r1, a1);
  const [x1o, y1o] = ptOnCircle(r2, a1);
  const [x2o, y2o] = ptOnCircle(r2, a2);
  const [x2i, y2i] = ptOnCircle(r1, a2);
  const lg = (a2 - a1) > 180 ? 1 : 0;
  return `M ${fmt(x1i)} ${fmt(y1i)} L ${fmt(x1o)} ${fmt(y1o)} A ${r2} ${r2} 0 ${lg} 1 ${fmt(x2o)} ${fmt(y2o)} L ${fmt(x2i)} ${fmt(y2i)} A ${r1} ${r1} 0 ${lg} 0 ${fmt(x1i)} ${fmt(y1i)} Z`;
}

function tabPathD(rI: number, rO: number, mid: number, halfW: number): string {
  const [x1, y1] = ptOnCircle(rI, mid - halfW);
  const [x2, y2] = ptOnCircle(rO, mid - halfW);
  const [x3, y3] = ptOnCircle(rO, mid + halfW);
  const [x4, y4] = ptOnCircle(rI, mid + halfW);
  return `M ${fmt(x1)} ${fmt(y1)} L ${fmt(x2)} ${fmt(y2)} L ${fmt(x3)} ${fmt(y3)} L ${fmt(x4)} ${fmt(y4)} Z`;
}

// ── Cell fill ──────────────────────────────────────────────────────────
function cellFill(tileId: string): string {
  if (!tileId || tileId === "clear") return "none";
  const tile = store.tiles[tileId];
  if (!tile) return "#888";
  if (tile.type === "solid") return tile.color || "#888";
  return `url(#pat-${tile.type})`;
}

// ── Expose for parent ──────────────────────────────────────────────────
defineExpose({ CX, CY, SVG_W, SVG_H });
</script>

<template>
  <svg
    :viewBox="`0 0 ${SVG_W} ${SVG_H}`"
    :width="SVG_W"
    :height="SVG_H"
    class="rd-wheel-svg"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Pattern defs -->
    <defs>
      <!-- Abalone gradient + pattern -->
      <linearGradient id="g-abalone" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#6ae0d0"/><stop offset="28%" stop-color="#50c8e8"/>
        <stop offset="55%" stop-color="#8860d0"/><stop offset="78%" stop-color="#50e890"/>
        <stop offset="100%" stop-color="#60b8e8"/>
      </linearGradient>
      <pattern id="pat-abalone" x="0" y="0" width="28" height="28" patternUnits="userSpaceOnUse">
        <rect width="28" height="28" fill="url(#g-abalone)" opacity="0.88"/>
        <ellipse cx="9" cy="9" rx="7" ry="4" fill="rgba(255,255,255,0.18)" transform="rotate(-30,9,9)"/>
        <ellipse cx="20" cy="20" rx="5" ry="3" fill="rgba(255,255,255,0.12)" transform="rotate(20,20,20)"/>
      </pattern>
      <!-- MOP -->
      <linearGradient id="g-mop" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#f0f0ee"/><stop offset="45%" stop-color="#e8ddf8"/>
        <stop offset="100%" stop-color="#d8f0ee"/>
      </linearGradient>
      <pattern id="pat-mop" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
        <rect width="18" height="18" fill="url(#g-mop)"/>
        <line x1="0" y1="9" x2="18" y2="9" stroke="rgba(200,190,220,0.28)" stroke-width="0.5"/>
        <line x1="9" y1="0" x2="9" y2="18" stroke="rgba(200,190,220,0.2)" stroke-width="0.5"/>
      </pattern>
      <!-- Burl -->
      <pattern id="pat-burl" x="0" y="0" width="22" height="15" patternUnits="userSpaceOnUse">
        <rect width="22" height="15" fill="#C8A048"/>
        <ellipse cx="6" cy="7" rx="4.5" ry="2.5" fill="none" stroke="#a07828" stroke-width="1" opacity="0.55"/>
        <ellipse cx="15" cy="5" rx="3.5" ry="2" fill="none" stroke="#b09030" stroke-width="0.8" opacity="0.5"/>
      </pattern>
      <!-- Herringbone -->
      <pattern id="pat-herringbone" x="0" y="0" width="20" height="20" patternUnits="userSpaceOnUse">
        <rect width="20" height="20" fill="#C09850"/>
        <line x1="-2" y1="12" x2="8" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
        <line x1="2" y1="16" x2="14" y2="-2" stroke="#7a5c28" stroke-width="2.8"/>
        <line x1="7" y1="20" x2="20" y2="4" stroke="#7a5c28" stroke-width="2.8"/>
        <line x1="10" y1="-2" x2="22" y2="14" stroke="#5a3c10" stroke-width="2.8"/>
        <line x1="5" y1="-2" x2="20" y2="16" stroke="#5a3c10" stroke-width="2.8"/>
        <line x1="-2" y1="4" x2="12" y2="20" stroke="#5a3c10" stroke-width="2.8"/>
      </pattern>
      <!-- Checker -->
      <pattern id="pat-checker" x="0" y="0" width="14" height="14" patternUnits="userSpaceOnUse">
        <rect width="14" height="14" fill="#f0e8d8"/>
        <rect x="0" y="0" width="7" height="7" fill="#1a1a1a"/>
        <rect x="7" y="7" width="7" height="7" fill="#1a1a1a"/>
      </pattern>
      <!-- Celtic -->
      <pattern id="pat-celtic" x="0" y="0" width="24" height="24" patternUnits="userSpaceOnUse">
        <rect width="24" height="24" fill="#1a3a2a"/>
        <path d="M4,4 Q12,12 20,4 Q12,0 4,4Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
        <path d="M4,20 Q12,12 20,20 Q12,24 4,20Z" fill="none" stroke="#50c880" stroke-width="2" opacity="0.8"/>
        <circle cx="12" cy="12" r="3" fill="none" stroke="#50c880" stroke-width="1.5"/>
      </pattern>
      <!-- Diagonal -->
      <pattern id="pat-diagonal" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
        <rect width="12" height="12" fill="#c8922a"/>
        <line x1="-2" y1="10" x2="10" y2="-2" stroke="#8B5a10" stroke-width="3.5"/>
        <line x1="4" y1="14" x2="14" y2="4" stroke="#8B5a10" stroke-width="3.5"/>
      </pattern>
      <!-- Dots -->
      <pattern id="pat-dots" x="0" y="0" width="12" height="12" patternUnits="userSpaceOnUse">
        <rect width="12" height="12" fill="#f5e6c8"/>
        <circle cx="6" cy="6" r="2.4" fill="#1a1a1a"/>
      </pattern>
      <!-- BWB stripes -->
      <pattern id="pat-stripes" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
        <rect x="0" y="0" width="9" height="3" fill="#111"/>
        <rect x="0" y="3" width="9" height="3" fill="#eee"/>
        <rect x="0" y="6" width="9" height="3" fill="#111"/>
      </pattern>
      <!-- RBR stripes -->
      <pattern id="pat-stripes2" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
        <rect x="0" y="0" width="9" height="3" fill="#cc0033"/>
        <rect x="0" y="3" width="9" height="3" fill="#111"/>
        <rect x="0" y="6" width="9" height="3" fill="#cc0033"/>
      </pattern>
      <!-- WBW stripes -->
      <pattern id="pat-stripes3" x="0" y="0" width="9" height="9" patternUnits="userSpaceOnUse">
        <rect x="0" y="0" width="9" height="3" fill="#eee"/>
        <rect x="0" y="3" width="9" height="3" fill="#111"/>
        <rect x="0" y="6" width="9" height="3" fill="#eee"/>
      </pattern>
      <!-- Soundhole gradient -->
      <radialGradient id="g-soundhole" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#060402"/>
        <stop offset="100%" stop-color="#0d0905"/>
      </radialGradient>
      <!-- MFG hatch pattern -->
      <pattern id="pat-mfg-hatch" x="0" y="0" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <line x1="0" y1="0" x2="0" y2="8" stroke="rgba(255,40,40,0.55)" stroke-width="3"/>
      </pattern>
    </defs>

    <!-- Outer decorative ring -->
    <circle :cx="CX" :cy="CY" r="354" fill="none" stroke="rgba(200,146,42,0.12)" stroke-width="8"/>

    <!-- Soundhole -->
    <circle :cx="CX" :cy="CY" r="148" fill="url(#g-soundhole)" stroke="rgba(200,146,42,0.45)" stroke-width="1.2"/>

    <!-- Ring backgrounds -->
    <template v-for="(rd, ri) in ringDefs" :key="`bg-${ri}`">
      <path
        :d="arcCellPath(rd.r1, rd.r2, 0, 359.999)"
        :fill="rd.has_tabs && store.ringActive[ri] ? '#12282e' : store.ringActive[ri] ? rd.color : 'rgba(20,18,14,0.5)'"
        :opacity="store.ringActive[ri] ? 1 : 0.35"
        stroke="none"
      />
    </template>

    <!-- Cells (interactive) -->
    <template v-for="(rd, ri) in ringDefs" :key="`cells-${ri}`">
      <template v-for="si in store.numSegs" :key="`cell-${ri}-${si - 1}`">
        <path
          :d="arcCellPath(rd.r1, rd.r2, (si - 1) * segAng, si * segAng)"
          :fill="store.grid[`${ri}-${si - 1}`] ? cellFill(store.grid[`${ri}-${si - 1}`]) : 'none'"
          :stroke="hoveredCellKey === `${ri}-${si - 1}` ? 'rgba(255,220,100,0.8)' : 'rgba(200,146,42,0.22)'"
          :stroke-width="hoveredCellKey === `${ri}-${si - 1}` ? 2 : 0.5"
          class="rd-cell"
          :class="{ 'rd-cell-active': store.ringActive[ri] }"
          @click="emit('cellClick', ri, si - 1)"
          @mouseenter="emit('cellEnter', ri, si - 1)"
          @mouseleave="emit('cellLeave')"
          @mouseup="emit('cellDrop', ri, si - 1)"
        />
      </template>
    </template>

    <!-- Extension tabs (Main Channel) -->
    <template v-if="store.showTabs">
      <template v-for="(rd, ri) in ringDefs" :key="`tabs-${ri}`">
        <template v-if="rd.has_tabs && store.ringActive[ri]">
          <template v-for="si in store.numSegs" :key="`tab-${ri}-${si - 1}`">
            <!-- Outer tab -->
            <path
              :d="tabPathD(rd.r2, rd.tab_outer_r, ((si - 1) + 0.5) * segAng, rd.tab_ang_width / 2)"
              :fill="store.grid[`${ri}-${si - 1}`]
                ? cellFill(store.grid[`${ri}-${si - 1}`])
                : ((si - 1) % 2 === 0 ? rd.tab_fill_even : rd.tab_fill_odd)"
              stroke="#1a1a2e"
              stroke-width="0.7"
              opacity="0.92"
            />
            <!-- Inner tab -->
            <path
              :d="tabPathD(rd.tab_inner_r, rd.r1, ((si - 1) + 0.5) * segAng, rd.tab_ang_width / 2)"
              :fill="store.grid[`${ri}-${si - 1}`]
                ? cellFill(store.grid[`${ri}-${si - 1}`])
                : ((si - 1) % 2 === 0 ? rd.tab_fill_even : rd.tab_fill_odd)"
              stroke="#1a1a2e"
              stroke-width="0.7"
              opacity="0.85"
            />
          </template>
        </template>
      </template>
    </template>

    <!-- MFG Overlay -->
    <template v-if="store.showMfgOverlay && store.mfgResult">
      <template v-for="mc in mfgOverlayCells" :key="`mfg-${mc.ri}-${mc.si}`">
        <path
          v-if="ringDefs[mc.ri]"
          :d="arcCellPath(ringDefs[mc.ri].r1, ringDefs[mc.ri].r2,
            mc.si * segAng, (mc.si + 1) * segAng)"
          fill="url(#pat-mfg-hatch)"
          stroke="rgba(255,40,40,0.7)"
          stroke-width="1.5"
          pointer-events="none"
        />
      </template>
    </template>

    <!-- Guide circles -->
    <template v-for="gc in GUIDE_CIRCLES" :key="`guide-${gc.r}`">
      <circle
        :cx="CX" :cy="CY" :r="gc.r"
        fill="none"
        :stroke="gc.tab ? 'rgba(200,146,42,0.18)' : 'rgba(200,146,42,0.38)'"
        :stroke-width="gc.tab ? 0.4 : 0.7"
        :stroke-dasharray="gc.dash ? '2,3' : 'none'"
      />
    </template>

    <!-- Radial lines -->
    <template v-for="si in store.numSegs" :key="`radial-${si}`">
      <line
        :x1="ptOnCircle(150, (si - 1) * segAng)[0]"
        :y1="ptOnCircle(150, (si - 1) * segAng)[1]"
        :x2="ptOnCircle(350, (si - 1) * segAng)[0]"
        :y2="ptOnCircle(350, (si - 1) * segAng)[1]"
        stroke="rgba(200,146,42,0.28)"
        stroke-width="0.55"
      />
    </template>

    <!-- Center crosshair -->
    <line :x1="CX - 14" :y1="CY" :x2="CX + 14" :y2="CY" stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>
    <line :x1="CX" :y1="CY - 14" :x2="CX" :y2="CY + 14" stroke="rgba(200,146,42,0.55)" stroke-width="0.8" stroke-dasharray="2,2"/>
    <circle :cx="CX" :cy="CY" r="4" fill="none" stroke="rgba(200,146,42,0.55)" stroke-width="0.8"/>

    <!-- Annotations (drafting overlay) -->
    <template v-if="store.showAnnotations">
      <rect x="0" y="0" :width="SVG_W" :height="SVG_H" fill="#f5f0e8" opacity="0.85"/>
      <!-- Diameter dims -->
      <g v-for="dim in [
        { r: 350, label: 'Ø 7.00″', yOff: -15 },
        { r: 300, label: 'Ø 6.00″', yOff: -10 },
        { r: 150, label: 'Ø 3.00″', yOff: 20 },
      ]" :key="dim.r">
        <line :x1="CX - dim.r" :y1="CY + dim.yOff" :x2="CX + dim.r" :y2="CY + dim.yOff"
          stroke="#1a1a2e" stroke-width="0.7"/>
        <text :x="CX" :y="CY + dim.yOff - 5" fill="#1a1a2e" font-family="monospace"
          font-size="8" text-anchor="middle">{{ dim.label }}</text>
      </g>
      <!-- Segment label -->
      <text :x="CX" :y="CY + 180" fill="#1a1a2e" font-family="monospace" font-size="8"
        text-anchor="middle">
        {{ store.numSegs }} EQUAL DIVISIONS × {{ segAng.toFixed(1) }}°
      </text>
      <!-- Section line -->
      <line x1="30" :y1="CY" :x2="SVG_W - 30" :y2="CY" stroke="#1a1a2e" stroke-width="0.8"
        stroke-dasharray="8,4,2,4"/>
    </template>
  </svg>
</template>

<style scoped>
.rd-wheel-svg { max-width: 100%; max-height: 100%; }
.rd-cell { cursor: pointer; transition: stroke 0.1s; }
.rd-cell.rd-cell-active:hover { stroke: rgba(255, 220, 100, 0.7) !important; stroke-width: 2 !important; }
</style>
