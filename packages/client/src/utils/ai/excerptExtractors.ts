export function decodeUtf8(bytes: Uint8Array): string {
  return new TextDecoder("utf-8").decode(bytes);
}

export function parseCsvRows(bytes: Uint8Array, maxRows = 10000): Array<Record<string, string>> {
  const text = decodeUtf8(bytes).trim();
  const lines = text.split(/\r?\n/);
  if (lines.length < 2) return [];
  const header = lines[0].split(",").map((h) => h.trim());
  const rows: Array<Record<string, string>> = [];
  for (let i = 1; i < lines.length && rows.length < maxRows; i++) {
    const cells = lines[i].split(",");
    const row: Record<string, string> = {};
    for (let c = 0; c < header.length; c++) row[header[c]] = (cells[c] ?? "").trim();
    rows.push(row);
  }
  return rows;
}

function toNum(v: unknown): number | null {
  const n = typeof v === "number" ? v : typeof v === "string" ? parseFloat(v) : NaN;
  return Number.isFinite(n) ? n : null;
}

export function nearestRowByFreq(
  rows: Array<Record<string, any>>,
  freqHz: number,
  freqKeyCandidates = ["freq_hz", "frequency_hz"]
): Record<string, any> | null {
  if (!rows.length) return null;
  let best: Record<string, any> | null = null;
  let bestErr = Infinity;
  for (const r of rows) {
    let f: number | null = null;
    for (const k of freqKeyCandidates) {
      if (r[k] != null) {
        f = toNum(r[k]);
        if (f != null) break;
      }
    }
    if (f == null) continue;
    const err = Math.abs(f - freqHz);
    if (err < bestErr) {
      bestErr = err;
      best = r;
    }
  }
  return best;
}

export function extractWsiRow(wsiCurveCsvBytes: Uint8Array, freqHz: number): Record<string, any> | null {
  const rows = parseCsvRows(wsiCurveCsvBytes, 20000);
  const coerced = rows.map((r) => ({
    ...r,
    freq_hz: toNum(r["freq_hz"]),
    wsi: toNum(r["wsi"]),
    phase_disorder: toNum(r["phase_disorder"]),
    coh_mean: toNum(r["coh_mean"]),
    admissible: r["admissible"],
  }));
  return nearestRowByFreq(coerced as any, freqHz, ["freq_hz"]);
}

export function extractSpectrumRow(spectrumCsvBytes: Uint8Array, freqHz: number): Record<string, any> | null {
  const rows = parseCsvRows(spectrumCsvBytes, 20000);
  const coerced = rows.map((r) => ({
    ...r,
    freq_hz: toNum(r["freq_hz"] ?? r["frequency_hz"]),
    H_mag: toNum(r["H_mag"] ?? r["h_mag"] ?? r["mag"]),
    coherence: toNum(r["coherence"] ?? r["coh"]),
    phase_deg: toNum(r["phase_deg"] ?? r["phase"]),
  }));
  return nearestRowByFreq(coerced as any, freqHz, ["freq_hz"]);
}

export function extractPeaks(peaksJsonBytes: Uint8Array, maxPeaks = 24): Array<Record<string, any>> | null {
  try {
    const text = decodeUtf8(peaksJsonBytes);
    const j = JSON.parse(text);
    const arr = Array.isArray(j) ? j : (j.peaks ?? []);
    if (!Array.isArray(arr)) return null;
    return arr.slice(0, maxPeaks);
  } catch {
    return null;
  }
}
