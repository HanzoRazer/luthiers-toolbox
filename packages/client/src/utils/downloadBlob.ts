// downloadBlob.ts
// B22.12: Browser-side file download utilities
import { REVOKE_URL_DELAY_MS } from '@/constants/timing'

/**
 * Download HTML content as a file in the browser.
 *
 * @param html - HTML content string
 * @param filename - Desired filename (e.g., "report.html")
 */
export function downloadHtmlFile(html: string, filename: string): void {
  const blob = new Blob([html], { type: "text/html;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Cleanup: revoke object URL after brief delay
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_URL_DELAY_MS);
}

/**
 * Download JSON content as a file in the browser.
 *
 * @param data - JavaScript object to serialize
 * @param filename - Desired filename (e.g., "report.json")
 */
export function downloadJsonFile(data: any, filename: string): void {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: "application/json;charset=utf-8" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  setTimeout(() => URL.revokeObjectURL(url), REVOKE_URL_DELAY_MS);
}

/**
 * Download arbitrary blob as a file.
 *
 * @param blob - Blob to download
 * @param filename - Desired filename
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  setTimeout(() => URL.revokeObjectURL(url), REVOKE_URL_DELAY_MS);
}

/**
 * Download a plain-text string as a file (CSV, G-code, etc.).
 *
 * @param content - Text content to download
 * @param filename - Desired filename
 * @param mimeType - MIME type (default: "text/plain")
 */
export function downloadTextFile(
  content: string,
  filename: string,
  mimeType = "text/plain",
): void {
  downloadBlob(new Blob([content], { type: mimeType }), filename);
}

/**
 * Download a string as a CSV file.
 *
 * @param content - CSV content string
 * @param filename - Desired filename (e.g., "export.csv")
 */
export function downloadCsvFile(content: string, filename: string): void {
  downloadTextFile(content, filename, "text/csv;charset=utf-8;");
}

/**
 * Escape a value for safe CSV output.
 * Wraps in double-quotes if the value contains comma, quote, or newline.
 *
 * @param val - Value to escape
 */
export function csvEscape(val: unknown): string {
  if (val === null || val === undefined) return "";
  const s = String(val);
  if (s.includes(",") || s.includes('"') || s.includes("\n")) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

/**
 * ISO timestamp safe for filenames: 2026-02-25T14-30-00-000Z
 */
export function filenameTimestamp(): string {
  return new Date().toISOString().replace(/[:.]/g, "-");
}
