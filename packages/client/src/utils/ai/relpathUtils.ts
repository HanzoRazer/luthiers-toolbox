export function pointIdFromRelpath(relpath: string): string | null {
  const m = relpath.match(/^spectra\/points\/([^\/]+)\//);
  if (m?.[1]) return m[1];
  const m2 = relpath.match(/^audio\/points\/([^\/]+)\.(wav|flac)$/i);
  if (m2?.[1]) return m2[1];
  return null;
}

export function isWsiCurve(relpath: string): boolean {
  return relpath === "wolf/wsi_curve.csv";
}

export function pickDefaultRefs(
  files: Array<{ relpath: string; kind?: string; sha256?: string; bytes?: number }>,
  activeRelpath: string | null
) {
  const out: typeof files = [];
  if (activeRelpath) {
    const active = files.find((f) => f.relpath === activeRelpath);
    if (active) out.push(active);
  }

  const wsi = files.find((f) => f.relpath === "wolf/wsi_curve.csv");
  if (wsi && !out.some((x) => x.relpath === wsi.relpath)) out.push(wsi);

  if (activeRelpath?.endsWith("/spectrum.csv")) {
    const sib = activeRelpath.replace(/\/spectrum\.csv$/, "/analysis.json");
    const peaks = files.find((f) => f.relpath === sib);
    if (peaks && !out.some((x) => x.relpath === peaks.relpath)) out.push(peaks);
  }

  return out.slice(0, 12);
}
