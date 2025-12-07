// compareReportBuilder.ts
// B22.12: UI exportable diff reports

export type CompareMode =
  | "side-by-side"
  | "overlay"
  | "delta"
  | "blink"
  | "xray";

export interface CompareBBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

export interface CompareResultJson {
  fullBBox?: CompareBBox;
  diffBBox?: CompareBBox | null;
  [key: string]: any;
}

export interface CompareLayerInfo {
  id: string;
  label?: string;
  inLeft?: boolean;
  inRight?: boolean;
  hasDiff?: boolean;
  enabled?: boolean;
  visibleLeft?: boolean;
  visibleRight?: boolean;
}

export interface DiffReportPayload {
  generatedAt: string;
  mode: CompareMode;
  diffDisabledReason: string | null;
  warnings: string[];
  layers: {
    id: string;
    label: string;
    inLeft: boolean;
    inRight: boolean;
    hasDiff: boolean;
    enabled: boolean;
  }[];
  bbox: CompareBBox | null;
  screenshotDataUrl?: string;
}

/**
 * Build a JSON-friendly payload from the current compare state.
 *
 * @param opts - Current compare state options
 * @returns Structured diff report payload
 */
export function buildDiffReportPayload(opts: {
  mode: CompareMode;
  diffDisabledReason: string | null;
  warnings?: string[];
  result: CompareResultJson | null;
  layers: CompareLayerInfo[];
  screenshotDataUrl?: string;
}): DiffReportPayload {
  const { mode, diffDisabledReason, result, layers, screenshotDataUrl } = opts;

  return {
    generatedAt: new Date().toISOString(),
    mode,
    diffDisabledReason,
    warnings: opts.warnings ?? [],
    layers: layers.map((l) => ({
      id: l.id,
      label: l.label || l.id,
      inLeft: !!l.inLeft,
      inRight: !!l.inRight,
      hasDiff: !!l.hasDiff,
      enabled: !!(l.enabled ?? l.visibleLeft ?? l.visibleRight),
    })),
    bbox: result ? result.diffBBox ?? result.fullBBox ?? null : null,
    screenshotDataUrl,
  };
}

/**
 * Turn a DiffReportPayload into a standalone HTML document.
 *
 * @param payload - Diff report data
 * @returns HTML string ready for download
 */
export function buildDiffReportHtml(payload: DiffReportPayload): string {
  const {
    generatedAt,
    mode,
    diffDisabledReason,
    warnings,
    layers,
    bbox,
    screenshotDataUrl,
  } = payload;

  const layersRows = layers
    .map(
      (l) => `
        <tr>
          <td>${escapeHtml(l.label)}</td>
          <td>${l.enabled ? "✓" : "✗"}</td>
          <td>${l.inLeft ? "✓" : "–"}</td>
          <td>${l.inRight ? "✓" : "–"}</td>
          <td>${l.hasDiff ? "✓" : "–"}</td>
        </tr>
      `
    )
    .join("");

  const warningsBlock =
    warnings.length > 0
      ? `<ul>${warnings.map((w) => `<li>${escapeHtml(w)}</li>`).join("")}</ul>`
      : "<p>None</p>";

  const bboxBlock = bbox
    ? `<p>minX: ${bbox.minX.toFixed(2)}, minY: ${bbox.minY.toFixed(
        2
      )}, maxX: ${bbox.maxX.toFixed(2)}, maxY: ${bbox.maxY.toFixed(2)}</p>`
    : "<p>(no bbox available)</p>";

  const screenshotBlock = screenshotDataUrl
    ? `<img src="${screenshotDataUrl}" alt="Compare screenshot" style="max-width:100%;border:1px solid #ccc;border-radius:4px;" />`
    : "<p>(no screenshot captured)</p>";

  const readableDate = new Date(generatedAt).toLocaleString();

  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>CompareLab Diff Report - ${escapeHtml(mode)}</title>
  <style>
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      margin: 1.5rem;
      color: #222;
      background: #fafafa;
    }
    .container {
      max-width: 1000px;
      margin: 0 auto;
      background: #fff;
      padding: 2rem;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
      margin-top: 1.2rem;
      margin-bottom: 0.4rem;
    }
    h1 {
      color: #007acc;
      border-bottom: 2px solid #007acc;
      padding-bottom: 0.5rem;
    }
    .meta {
      font-size: 0.9rem;
      color: #666;
      margin-bottom: 1rem;
    }
    table {
      border-collapse: collapse;
      width: 100%;
      margin-top: 0.5rem;
    }
    th, td {
      border: 1px solid #ddd;
      padding: 0.5rem 0.75rem;
      font-size: 0.85rem;
      text-align: left;
    }
    th {
      background: #f7f7f7;
      font-weight: 600;
    }
    tbody tr:nth-child(even) {
      background: #fafafa;
    }
    tbody tr:hover {
      background: #f0f8ff;
    }
    .badge {
      display: inline-block;
      padding: 0.2rem 0.6rem;
      border-radius: 999px;
      font-size: 0.75rem;
      margin-left: 0.25rem;
      font-weight: 600;
    }
    .badge-mode {
      background: #007acc;
      color: #fff;
    }
    .warning {
      background: #fff3cd;
      border: 1px solid #ffeeba;
      color: #856404;
      padding: 0.75rem 1rem;
      border-radius: 4px;
      margin-top: 0.5rem;
    }
    .success {
      background: #d4edda;
      border: 1px solid #c3e6cb;
      color: #155724;
      padding: 0.75rem 1rem;
      border-radius: 4px;
      margin-top: 0.5rem;
    }
    .section {
      margin-top: 1.5rem;
    }
    .screenshot-container {
      margin-top: 1rem;
      text-align: center;
    }
    .screenshot-container img {
      max-width: 100%;
      height: auto;
      border: 1px solid #ccc;
      border-radius: 4px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .footer {
      margin-top: 2rem;
      padding-top: 1rem;
      border-top: 1px solid #ddd;
      font-size: 0.8rem;
      color: #999;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>CompareLab Diff Report <span class="badge badge-mode">${escapeHtml(
      mode
    )}</span></h1>
    <div class="meta">Generated: ${escapeHtml(readableDate)}</div>

    <div class="section">
      <h2>Status</h2>
      ${
        diffDisabledReason
          ? `<div class="warning"><strong>⚠️ Diff Disabled:</strong> ${escapeHtml(
              diffDisabledReason
            )}</div>`
          : '<div class="success">✓ Diff active and computed successfully</div>'
      }
    </div>

    <div class="section">
      <h2>Bounding Box</h2>
      ${bboxBlock}
    </div>

    <div class="section">
      <h2>Warnings</h2>
      ${warningsBlock}
    </div>

    <div class="section">
      <h2>Layer Analysis</h2>
      ${
        layers.length > 0
          ? `
      <table>
        <thead>
          <tr>
            <th>Layer</th>
            <th>Enabled</th>
            <th>In Left</th>
            <th>In Right</th>
            <th>Has Diff</th>
          </tr>
        </thead>
        <tbody>
          ${layersRows}
        </tbody>
      </table>
      `
          : "<p>No layer data available</p>"
      }
    </div>

    <div class="section">
      <h2>Screenshot (Active Mode)</h2>
      <div class="screenshot-container">
        ${screenshotBlock}
      </div>
    </div>

    <div class="footer">
      Generated by Luthier's Tool Box CompareLab • B22.12
    </div>
  </div>
</body>
</html>`;
}

/**
 * Escape HTML special characters to prevent XSS.
 *
 * @param input - Raw string
 * @returns HTML-safe string
 */
function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
