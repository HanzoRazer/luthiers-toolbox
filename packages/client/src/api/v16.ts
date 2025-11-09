// src/api/v16.ts
const base = (import.meta as any).env?.VITE_API_BASE || '/api';

async function getJson(url: string) {
  const res = await fetch(url);
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}
async function postJson(url: string, body: any) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}

export const svgHealth = () => getJson(`${base}/art/svg/health`);
export const svgNormalize = (svg_text: string) => postJson(`${base}/art/svg/normalize`, { svg_text });
export const svgOutline = (svg_text: string, stroke_width_mm=0.4) =>
  postJson(`${base}/art/svg/outline`, { svg_text, stroke_width_mm });
export const svgSave = (svg_text: string, name: string) =>
  postJson(`${base}/art/svg/save`, { svg_text, name });

export const reliefHealth = () => getJson(`${base}/art/relief/health`);
export const reliefPreview = (grayscale: number[][], z_min_mm=0, z_max_mm=1.2, scale_xy_mm=1.0) =>
  postJson(`${base}/art/relief/heightmap_preview`, { grayscale, z_min_mm, z_max_mm, scale_xy_mm });
