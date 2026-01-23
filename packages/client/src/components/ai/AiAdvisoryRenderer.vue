<template>
  <section class="advisory">
    <header class="hdr">
      <div class="title">
        <h3>AI Advisory (Draft)</h3>
        <div class="meta">
          <span class="pill">informational only</span>
          <span v-if="artifact?.advisory_id" class="mono">{{ artifact.advisory_id.slice(0, 8) }}…</span>
          <span v-if="artifact?.created_at_utc" class="mono">{{ artifact.created_at_utc }}</span>
        </div>
      </div>

      <details class="engine" v-if="artifact?.engine || artifact?.governance">
        <summary>Details</summary>
        <pre class="mono">{{ detailsJson }}</pre>
      </details>
    </header>

    <div v-if="!blocks.length" class="empty">
      No advisory content.
    </div>

    <div v-else class="body">
      <template v-for="(b, idx) in blocks" :key="idx">
        <h4 v-if="b.type === 'heading'" class="h" :data-level="b.level">{{ b.text }}</h4>

        <p v-else-if="b.type === 'paragraph'" class="p">{{ b.text }}</p>

        <ul v-else-if="b.type === 'bullet_list'" class="ul">
          <li v-for="(it, i) in b.items" :key="i">{{ it }}</li>
        </ul>

        <blockquote v-else-if="b.type === 'quote'" class="q">{{ b.text }}</blockquote>

        <pre v-else-if="b.type === 'code_block'" class="code"><code>{{ b.code }}</code></pre>

        <div v-else-if="b.type === 'evidence_refs'" class="refs">
          <div class="refs-title">{{ b.title || "Evidence references" }}</div>
          <table class="tbl">
            <thead>
              <tr><th>relpath</th><th>kind</th><th>sha256</th><th>bytes</th></tr>
            </thead>
            <tbody>
              <tr v-for="(r, i) in b.refs" :key="i">
                <td class="mono">{{ r.relpath }}</td>
                <td class="mono">{{ r.kind || '—' }}</td>
                <td class="mono">{{ (r.sha256 || '—').slice(0, 12) }}…</td>
                <td class="mono">{{ r.bytes ?? '—' }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { AdvisoryArtifact, AdvisoryDraftV1 } from "./advisoryTypes";
import { normalizeBlocks } from "./advisoryRenderers";

const props = defineProps<{
  artifact: AdvisoryArtifact | null;
  draftOverride?: AdvisoryDraftV1 | null;
}>();

const draft = computed<any>(() => props.draftOverride ?? props.artifact?.draft ?? null);
const blocks = computed(() => normalizeBlocks(draft.value));

const detailsJson = computed(() => {
  const d: any = {
    engine: props.artifact?.engine ?? null,
    governance: props.artifact?.governance ?? null,
  };
  return JSON.stringify(d, null, 2);
});
</script>

<style scoped>
.advisory { border: 1px solid rgba(255,255,255,0.10); border-radius: 14px; padding: 12px; background: rgba(255,255,255,0.03); }
.hdr { display: flex; gap: 10px; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; }
.title h3 { margin: 0; }
.meta { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 4px; opacity: 0.85; font-size: 0.85rem; }
.pill { padding: 0.15rem 0.45rem; border-radius: 999px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.06); }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.engine summary { cursor: pointer; opacity: 0.85; }
.engine pre { margin-top: 6px; max-width: 520px; max-height: 200px; overflow: auto; background: rgba(0,0,0,0.25); padding: 8px; border-radius: 10px; }
.empty { opacity: 0.75; padding: 10px 0; }
.body { margin-top: 10px; display: grid; gap: 10px; }
.h[data-level="2"] { font-size: 1.05rem; margin: 0; }
.h[data-level="3"] { font-size: 0.95rem; margin: 0; opacity: 0.95; }
.h[data-level="4"] { font-size: 0.9rem; margin: 0; opacity: 0.9; }
.p { margin: 0; line-height: 1.4; }
.ul { margin: 0; padding-left: 18px; }
.q { margin: 0; padding: 8px 10px; border-left: 3px solid rgba(255,255,255,0.20); background: rgba(255,255,255,0.04); border-radius: 10px; }
.code { margin: 0; padding: 10px; background: rgba(0,0,0,0.28); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; overflow: auto; }
.refs-title { font-weight: 600; margin-bottom: 6px; opacity: 0.9; }
.tbl { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
.tbl th, .tbl td { border-bottom: 1px solid rgba(255,255,255,0.08); padding: 6px 8px; text-align: left; }
.tbl th { opacity: 0.65; font-weight: 500; }
</style>
