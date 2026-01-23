import type { AdvisoryBlock, EvidenceRef } from "./advisoryTypes";

export function normalizeBlocks(draft: any): AdvisoryBlock[] {
  const blocks: any[] = Array.isArray(draft?.content) ? draft.content : [];
  const out: AdvisoryBlock[] = [];

  for (const b of blocks) {
    if (!b || typeof b !== "object") continue;
    const t = (b as any).type;

    if (t === "heading" && typeof (b as any).text === "string") {
      out.push({ type: "heading", level: (b as any).level ?? 2, text: (b as any).text });
    } else if (t === "paragraph" && typeof (b as any).text === "string") {
      out.push({ type: "paragraph", text: (b as any).text });
    } else if (t === "bullet_list" && Array.isArray((b as any).items)) {
      out.push({ type: "bullet_list", items: (b as any).items.map(String) });
    } else if (t === "code_block" && typeof (b as any).code === "string") {
      out.push({ type: "code_block", language: (b as any).language, code: (b as any).code });
    } else if (t === "quote" && typeof (b as any).text === "string") {
      out.push({ type: "quote", text: (b as any).text });
    } else if (t === "evidence_refs" && Array.isArray((b as any).refs)) {
      out.push({ type: "evidence_refs", refs: (b as any).refs as EvidenceRef[], title: (b as any).title });
    } else {
      // Unknown block: degrade gracefully into JSON
      out.push({ type: "code_block", language: "json", code: JSON.stringify(b, null, 2) });
    }
  }

  // If there are no blocks but there are citations, show them.
  const citations = Array.isArray(draft?.citations) ? (draft.citations as EvidenceRef[]) : null;
  if (out.length === 0 && citations) {
    out.push({ type: "evidence_refs", refs: citations, title: "Evidence references" });
  }

  return out;
}

export function normalizeEvidenceRefs(refs: any): EvidenceRef[] {
  if (!Array.isArray(refs)) return [];
  return refs
    .filter((r) => r && typeof r.relpath === "string")
    .map((r) => ({ relpath: r.relpath, kind: r.kind, sha256: r.sha256, bytes: r.bytes }));
}
