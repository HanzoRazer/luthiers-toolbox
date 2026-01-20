
// ==========================================================================
// Bundle 32.8.4.10: Copy Node fetch snippet (Node 18+ / JS CI runners)
// ==========================================================================

function _jsEscape(s: string): string {
  // Escape for JS template literal (backticks)
  return String(s).replace(/\/g, "\\\\").replace(/`/g, "\`");
}

function buildExportNodeFetch(url: string, session_id: string): string {
  const out = _safeFilenameFromSession(session_id);
  const u = _jsEscape(url);

  return [
    "// Promotion intent export (Node fetch, Node 18+)",
    "import fs from 'node:fs';",
    "",
    "const url = `" + u + "`;",
    "const out = " + JSON.stringify(out) + ";",
    "",
    "const res = await fetch(url, {",
    "  method: 'GET',",
    "  headers: { 'Accept': 'application/json' },",
    "});",
    "",
    "if (!res.ok) {",
    "  const ct = res.headers.get('content-type') || '';",
    "  let body = '';",
    "  try { body = ct.includes('application/json') ? JSON.stringify(await res.json()) : await res.text(); } catch {}",
    "  throw new Error(`HTTP ${res.status} ${res.statusText} :: ${body}`);",
    "}",
    "",
    "const buf = Buffer.from(await res.arrayBuffer());",
    "fs.writeFileSync(out, buf);",
    "",
    "// Optional: sanity parse",
    "try {",
    "  const json = JSON.parse(buf.toString('utf8'));",
    "  console.log('Downloaded intent:', json.intent_version, 'session_id=', json.session_id);",
    "} catch (e) {",
    "  console.warn('Saved file but JSON parse failed:', e?.message || e);",
    "}",
    "",
    "console.log('Saved:', out);",
    "",
  ].join("\n");
}

async function copyExportNode() {
  const sid = wf.sessionId;
  const url = exportUrlPreview.value;
  if (!sid || !url) return;

  const snippet = buildExportNodeFetch(url, sid);

  try {
    await navigator.clipboard.writeText(snippet);
    toast.success("Copied Node fetch snippet.");
  } catch {
    toast.error("Copy failed.");
  }
}
