/**
 * useCurveOperations - API curve operations for CurveLab
 */
import { ref, type Ref } from "vue";
import { offsetPolycurve, autoFillet, fairCurve, blendClothoid } from "@/utils/curvemath";
import type { Point } from "./useCurveHistory";

export interface ClothoidPick {
  p0?: Point;
  t0?: Point;
  p1?: Point;
  t1?: Point;
}

export function useCurveOperations(
  pts: Ref<Point[]>,
  pushHistory: () => void,
  redraw: () => void
) {
  // Clothoid picking state
  const cPick = ref<ClothoidPick>({});

  async function doOffset(offsetDist: number, join: "round" | "miter" | "bevel") {
    if (pts.value.length < 2) {
      alert("Need at least 2 points for offset");
      return;
    }
    pushHistory();
    try {
      const body = await offsetPolycurve(
        pts.value.map(p => [p.x, p.y]),
        offsetDist,
        join
      );
      pts.value = body.polyline.points.map(([x, y]: [number, number]) => ({ x, y }));
      redraw();
    } catch (err) {
      alert(`Offset failed: ${err}`);
    }
  }

  async function doFillet(filletR: number) {
    if (pts.value.length < 3) {
      alert("Need at least 3 points for fillet");
      return;
    }
    pushHistory();
    try {
      const body = await autoFillet(
        pts.value.map(p => [p.x, p.y]),
        filletR,
        10
      );
      pts.value = body.polyline.points.map(([x, y]: [number, number]) => ({ x, y }));
      redraw();
    } catch (err) {
      alert(`Fillet failed: ${err}`);
    }
  }

  async function doFair(lam: number, preserve: boolean) {
    if (pts.value.length < 3) {
      alert("Need at least 3 points for fairing");
      return;
    }
    pushHistory();
    try {
      const body = await fairCurve(
        pts.value.map(p => [p.x, p.y]),
        lam,
        preserve
      );
      pts.value = body.polyline.points.map(([x, y]: [number, number]) => ({ x, y }));
      redraw();
    } catch (err) {
      alert(`Fairing failed: ${err}`);
    }
  }

  function resetClothoid() {
    cPick.value = {};
    redraw();
  }

  async function doClothoid() {
    const c = cPick.value;
    if (!c.p0 || !c.t0 || !c.p1 || !c.t1) {
      alert("Pick all 4 points: p0, t0, p1, t1");
      return;
    }

    pushHistory();
    try {
      const p0: [number, number] = [c.p0.x, c.p0.y];
      const p1: [number, number] = [c.p1.x, c.p1.y];
      const t0: [number, number] = [c.t0.x - c.p0.x, c.t0.y - c.p0.y];
      const t1: [number, number] = [c.t1.x - c.p1.x, c.t1.y - c.p1.y];

      const body = await blendClothoid(p0, t0, p1, t1, 1.0);
      pts.value = body.polyline.points.map(([x, y]: [number, number]) => ({ x, y }));
      cPick.value = {};
      redraw();
    } catch (err) {
      alert(`Clothoid blend failed: ${err}`);
    }
  }

  function pickClothoidPoint(p: Point) {
    const c = cPick.value;
    if (!c.p0) {
      c.p0 = p;
    } else if (!c.t0) {
      c.t0 = p;
    } else if (!c.p1) {
      c.p1 = p;
    } else if (!c.t1) {
      c.t1 = p;
    }
  }

  return {
    cPick,
    doOffset,
    doFillet,
    doFair,
    resetClothoid,
    doClothoid,
    pickClothoidPoint,
  };
}
