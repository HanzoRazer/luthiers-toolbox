/**
 * useCurveHistory - History management and export for CurveLab
 */
import { ref, type Ref } from "vue";

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

  function exportDXF() {
    // TODO: Implement DXF export via API
    alert("DXF export coming soon! Use Export JSON for now.");
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
