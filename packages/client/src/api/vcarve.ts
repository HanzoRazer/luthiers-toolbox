// src/api/vcarve.ts
async function postJson(url: string, body: any) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(await res.text() || ('HTTP ' + res.status));
  return res.json();
}
export async function sendToProject(payload: any) {
  const base = (import.meta as any).env?.VITE_API_BASE || '/api';
  return postJson(`${base}/projects/${encodeURIComponent(payload.projectId)}/cam/preview`, payload);
}
