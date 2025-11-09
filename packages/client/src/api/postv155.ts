// Art Studio v15.5 API helpers
async function postJson(url: string, body: any) {
  const res = await fetch(url, { 
    method: 'POST', 
    headers: { 'Content-Type': 'application/json' }, 
    body: JSON.stringify(body) 
  });
  if(!res.ok) throw new Error(await res.text() || ('HTTP '+res.status));
  return res.json();
}

export async function fetchPosts(){
  const base = (import.meta as any).env?.VITE_API_BASE || '/api';
  const res = await fetch(`${base}/cam_gcode/posts_v155`);
  if(!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function postV155(body:any){
  const base = (import.meta as any).env?.VITE_API_BASE || '/api';
  return postJson(`${base}/cam_gcode/post_v155`, body);
}
