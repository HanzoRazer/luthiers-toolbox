/**
 * useCurveHistory - History management and export for CurveLab
 */
import { ref, type Ref } from "vue";

import { exportCurveDxf } from "@/api/curvelab";

export type Point = { x: number; y: number };

export function useCurveHistory() {
  const pts = ref<Point[]>([]);
  const stack: Point[][] = [];

  function pushHistory() {
    stack.push(pts.value.map(p => ({ x: p.x, y: p.y })));
  }

  function undo(redraw: () => void) {
    if (stack.length) {
      pts.value = stack.pop()!;
      redraw();
    }
  }

  function clearAll(redraw: () => void, resetClothoid?: () => void) {
    pushHistory();
    pts.value = [];
    resetClothoid?.();
    redraw();
  }

  function exportJSON() {
    const data = JSON.stringify(
      { points: pts.value.map(p => [p.x, p.y]) },
      null,
      2
    );
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "curve.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function exportDXF() {
    if (pts.value.length < 2) {
      alert("Need at least two points to export a DXF.");
      return;
    }
    try {
      const blob = await exportCurveDxf({
        curves: [
          {
            points: pts.value.map((p) => ({ x: p.x, y: p.y })),
            label: "curve",
          },
        ],
        scale_mm_per_unit: 1.0,
        filename: "curve_export",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "curve_export.dxf";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error(e);
      alert(e instanceof Error ? e.message : "DXF export failed.");
    }
  }

  return {
    pts,
    stack,
    pushHistory,
    undo,
    clearAll,
    exportJSON,
    exportDXF,
  };
}
