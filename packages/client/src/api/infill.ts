// src/api/infill.ts
async function postJson(url: string, body: any) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(await res.text() || ('HTTP ' + res.status));
  return res.json();
}
export async function previewInfill(body: any){
  const base = (import.meta as any).env?.VITE_API_BASE || '/api';
  return postJson(`${base}/cam_vcarve/preview_infill`, body);
}
