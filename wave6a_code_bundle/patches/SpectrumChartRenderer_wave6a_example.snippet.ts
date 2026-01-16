// SpectrumChartRenderer.vue (Wave 6A additions)
// This is a *snippet* showing the exact patterns to add.

import type { EvidenceSelection } from "../selection";

const props = defineProps<RendererProps>();
const emit = defineEmits<{
  (e: "select", sel: EvidenceSelection): void;
}>();

function pointIdFromSpectrumRelpath(relpath: string): string | null {
  // spectra/points/A1/spectrum.csv
  const m = relpath.match(/^spectra\/points\/([^/]+)\/spectrum\.csv$/);
  return m?.[1] ?? null;
}

// 1) Add invisible peaks dataset
const peaksDataset = {
  label: "__peaks__",
  showLine: false,
  data: peaks.map((p) => ({ x: p.freq_hz, y: p.H_mag ?? p.mag ?? p.amplitude ?? 0 })),
  pointRadius: 6,
  pointHitRadius: 10,
  pointHoverRadius: 8,
  // Transparent points; keep interaction active
  pointBackgroundColor: "rgba(0,0,0,0)",
  pointBorderColor: "rgba(0,0,0,0)",
};

// 2) Cursor plugin (draw at exact freqHz)
function makeCursorPlugin(selection: EvidenceSelection | null | undefined) {
  return {
    id: "wave6a_cursor",
    afterDraw(chart: any) {
      const f = selection?.freqHz;
      if (typeof f !== "number") return;
      const xScale = chart.scales.x;
      if (!xScale) return;
      const x = xScale.getPixelForValue(f);
      const { top, bottom } = chart.chartArea;
      const ctx = chart.ctx;
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.lineWidth = 1;
      ctx.strokeStyle = "rgba(255,255,255,0.6)";
      ctx.stroke();
      ctx.restore();
    },
  };
}

// 3) onClick hit-test
const chartOptions = {
  onClick: (_e: any, active: any[], chart: any) => {
    const hit = active?.[0];
    if (!hit) return;
    const ds = chart.data.datasets?.[hit.datasetIndex];
    if (ds?.label !== "__peaks__") return;
    const peak = peaks[hit.index];
    if (!peak) return;

    emit("select", {
      pointId: pointIdFromSpectrumRelpath(props.entry.relpath),
      freqHz: Number(peak.freq_hz),
      source: "spectrum",
    });
  },
};
