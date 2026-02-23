/**
 * useBridgeExport - Export functions for Bridge Calculator
 */
import { api } from "@/services/apiBase";
import type { Ref, ComputedRef } from "vue";
import type { BridgeUIState } from "./useBridgeUnits";
import type { Point2D } from "./useBridgeGeometry";

export interface BridgeModel {
  units: "mm" | "in";
  scaleLength: number;
  stringSpread: number;
  compTreble: number;
  compBass: number;
  slotWidth: number;
  slotLength: number;
  angleDeg: number;
  endpoints: {
    treble: { x: number; y: number };
    bass: { x: number; y: number };
  };
  slotPolygon: { x: number; y: number }[];
}

function round2(x: number): number {
  return Math.round(x * 100) / 100;
}

function round3(x: number): number {
  return Math.round(x * 1000) / 1000;
}

export function useBridgeExport(
  ui: BridgeUIState,
  isMM: Ref<boolean>,
  angleDeg: ComputedRef<number>,
  treble: ComputedRef<Point2D>,
  bass: ComputedRef<Point2D>,
  slotPoly: ComputedRef<Point2D[]>,
  svgViewBox: ComputedRef<string>,
  svgH: ComputedRef<number>,
  scale: ComputedRef<number>,
  slotPolygonPoints: ComputedRef<string>
) {
  function currentModel(): BridgeModel {
    return {
      units: isMM.value ? "mm" : "in",
      scaleLength: round2(ui.scale),
      stringSpread: round2(ui.spread),
      compTreble: round2(ui.compTreble),
      compBass: round2(ui.compBass),
      slotWidth: round2(ui.slotWidth),
      slotLength: round2(ui.slotLength),
      angleDeg: round3(angleDeg.value),
      endpoints: {
        treble: { x: round3(treble.value.x), y: round3(treble.value.y) },
        bass: { x: round3(bass.value.x), y: round3(bass.value.y) },
      },
      slotPolygon: slotPoly.value.map((p) => ({
        x: round3(p.x),
        y: round3(p.y),
      })),
    };
  }

  async function copyJSON() {
    const j = JSON.stringify(currentModel(), null, 2);
    await navigator.clipboard.writeText(j);
    alert("Model JSON copied to clipboard.");
  }

  function downloadSVG() {
    const vb = svgViewBox.value.split(" ");
    const [minX, minY, w, h] = vb.map(Number);
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${minX} ${minY} ${w} ${h}">
  <line x1="0" y1="${-svgH.value / 2}" x2="0" y2="${svgH.value / 2}" stroke="#d1d5db" stroke-width="0.2"/>
  <line x1="${scale.value}" y1="-3" x2="${scale.value}" y2="3" stroke="#94a3b8" stroke-width="0.3"/>
  <line x1="${treble.value.x}" y1="${treble.value.y}" x2="${bass.value.x}" y2="${bass.value.y}" stroke="#0ea5e9" stroke-width="0.5"/>
  <polygon points="${slotPolygonPoints.value}" fill="rgba(14,165,233,0.25)" stroke="#0284c7" stroke-width="0.4"/>
</svg>`;
    const blob = new Blob([svg], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `saddle_slot_${isMM.value ? "mm" : "in"}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function exportDXF() {
    try {
      const model = currentModel();
      const payload = {
        geometry: model,
        filename: `bridge_${model.scaleLength.toFixed(1)}${model.units}_ct${model.compTreble.toFixed(1)}_cb${model.compBass.toFixed(1)}`,
      };

      const response = await api("/api/cam/bridge/export_dxf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`DXF export failed: ${error}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${payload.filename}.dxf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      console.error("DXF export error:", err);
      alert(`DXF export failed: ${message}`);
    }
  }

  return {
    currentModel,
    copyJSON,
    downloadSVG,
    exportDXF,
  };
}
