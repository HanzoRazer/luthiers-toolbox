// src/api/v161.ts
const base = (import.meta as any).env?.VITE_API_BASE || '/api';

async function postJson(url: string, body: any) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export type HelicalReq = {
  cx: number; cy: number; radius_mm: number; direction: 'CW'|'CCW';
  plane_z_mm: number; start_z_mm: number; z_target_mm: number;
  pitch_mm_per_rev: number; feed_xy_mm_min: number; feed_z_mm_min?: number|null;
  ij_mode: boolean; absolute: boolean; units_mm: boolean; safe_rapid: boolean;
  dwell_ms: number; max_arc_degrees: number;
  /** Optional controller preset: GRBL | Mach3 | Haas | Marlin */
  post_preset?: string;
};

export const helicalEntry = (req: HelicalReq) => postJson(`${base}/cam/toolpath/helical_entry`, req);
