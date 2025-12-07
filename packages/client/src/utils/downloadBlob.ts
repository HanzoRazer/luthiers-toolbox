// downloadBlob.ts
// B22.12: Browser-side file download utilities

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
  setTimeout(() => URL.revokeObjectURL(url), 100);
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

  setTimeout(() => URL.revokeObjectURL(url), 100);
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

  setTimeout(() => URL.revokeObjectURL(url), 100);
}
