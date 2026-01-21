<template>
  <div class="card">
    <div class="head">
      <div>
        <div class="title">
          Plan Attachments Inspector
        </div>
        <div class="sub">
          Bundle 16: View plan.json and normalized_intent.json
        </div>
      </div>
      <div class="actions">
        <button
          :disabled="busy || !planRunId"
          @click="refresh"
        >
          Refresh
        </button>
      </div>
    </div>

    <div
      v-if="error"
      class="error"
    >
      {{ error }}
    </div>

    <div
      v-if="!planRunId"
      class="empty"
    >
      No plan run ID provided. Execute a plan first.
    </div>

    <div
      v-else
      class="grid"
    >
      <div class="left">
        <div class="section">
          <div class="sectionTitle">
            Attachments
          </div>

          <div
            v-if="busy"
            class="empty"
          >
            Loading...
          </div>

          <div
            v-else-if="attachments.length === 0"
            class="empty"
          >
            No attachments found for this run.
          </div>

          <div
            v-else
            class="list"
          >
            <button
              v-for="a in attachments"
              :key="idOf(a)"
              class="att"
              :class="{ active: selectedId === idOf(a) }"
              @click="selectAttachment(a)"
            >
              <div class="p">
                {{ pathOf(a) }}
              </div>
              <div class="m">
                {{ a.content_type || "unknown" }}
              </div>
            </button>
          </div>

          <div class="sectionTitle">
            Quick Picks
          </div>
          <div class="qp">
            <button
              :disabled="busy || !planRunId"
              @click="openPlanJson"
            >
              Open meta/plan.json
            </button>
            <button
              :disabled="busy || !planRunId"
              @click="openNormalizedIntent"
            >
              Open inputs/normalized_intent.json
            </button>
          </div>

          <div class="hint">
            If exact paths don't exist, quick picks will fall back to fuzzy matches.
          </div>
        </div>
      </div>

      <div class="right">
        <div class="section">
          <div class="sectionTitle">
            Viewer
            <span
              v-if="selectedPath"
              class="pill"
            ><code>{{ selectedPath }}</code></span>
            <span
              v-if="selectedSource"
              class="pill"
            >{{ selectedSource }}</span>
          </div>

          <div
            v-if="viewerBusy"
            class="empty"
          >
            Fetching attachment...
          </div>

          <div
            v-else-if="viewerError"
            class="error"
          >
            {{ viewerError }}
          </div>

          <pre
            v-else
            class="pre"
          >{{ renderedText }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { ApiError } from "@/sdk/core/errors";
import { rmosRunAttachments, type RunAttachmentRow } from "@/sdk/rmos/runs_attachments";

const props = defineProps<{
  planRunId: string | null;
  requestId?: string;
}>();

const busy = ref(false);
const error = ref("");
const attachments = ref<RunAttachmentRow[]>([]);

const selectedId = ref<string>("");
const selectedPath = ref<string>("");
const selectedSource = ref<string>("");

const viewerBusy = ref(false);
const viewerError = ref("");
const viewerText = ref<string>("");

function baseUrl(): string {
  return "";
}

function setError(e: unknown, target: "main" | "viewer" = "main") {
  const msg =
    e instanceof ApiError
      ? `${e.message} (status ${e.status}) request-id=${e.requestId ?? "unknown"}`
      : (e as any)?.message ?? String(e);

  if (target === "main") error.value = msg;
  else viewerError.value = msg;
}

function idOf(a: RunAttachmentRow): string {
  return rmosRunAttachments._getAttachmentId(a);
}

function pathOf(a: RunAttachmentRow): string {
  return rmosRunAttachments._getAttachmentPath(a);
}

function normalizePath(p: string): string {
  return (p || "").split("\\").join("/").trim().toLowerCase();
}

function findExact(path: string): RunAttachmentRow | null {
  const want = normalizePath(path);
  for (const a of attachments.value) {
    if (normalizePath(pathOf(a)) === want) return a;
  }
  return null;
}

function findFuzzy(tokens: string[]): RunAttachmentRow | null {
  const ts = tokens.map(t => t.toLowerCase());
  const scored: { a: RunAttachmentRow; score: number }[] = [];

  for (const a of attachments.value) {
    const p = normalizePath(pathOf(a));
    if (!p) continue;

    let s = 0;
    for (const t of ts) {
      if (p.includes(t)) s += 1;
    }
    if (s > 0) scored.push({ a, score: s });
  }

  scored.sort((x, y) => y.score - x.score);
  return scored.length ? scored[0].a : null;
}

async function refresh() {
  if (!props.planRunId) return;

  busy.value = true;
  error.value = "";
  attachments.value = [];
  selectedId.value = "";
  selectedPath.value = "";
  selectedSource.value = "";
  viewerText.value = "";
  viewerError.value = "";

  try {
    const { data } = await rmosRunAttachments.list(baseUrl(), props.planRunId, props.requestId);
    attachments.value = data.attachments ?? [];
  } catch (e) {
    setError(e, "main");
  } finally {
    busy.value = false;
  }
}

async function selectAttachment(a: RunAttachmentRow) {
  if (!props.planRunId) return;

  selectedId.value = idOf(a);
  selectedPath.value = pathOf(a);
  selectedSource.value = "";

  viewerBusy.value = true;
  viewerError.value = "";
  viewerText.value = "";

  try {
    const { text, source } = await rmosRunAttachments.fetchText(baseUrl(), props.planRunId, a, props.requestId);
    selectedSource.value = source;
    viewerText.value = text;
  } catch (e) {
    setError(e, "viewer");
  } finally {
    viewerBusy.value = false;
  }
}

async function openPlanJson() {
  const exact = findExact("meta/plan.json");
  const pick = exact ?? findFuzzy(["plan.json", "meta", "plan"]);
  if (pick) await selectAttachment(pick);
  else viewerError.value = "Could not find meta/plan.json (or fuzzy match) in attachments list.";
}

async function openNormalizedIntent() {
  const exact = findExact("inputs/normalized_intent.json");
  const pick = exact ?? findFuzzy(["normalized_intent", "intent", "inputs"]);
  if (pick) await selectAttachment(pick);
  else viewerError.value = "Could not find inputs/normalized_intent.json (or fuzzy match) in attachments list.";
}

const renderedText = computed(() => {
  const t = viewerText.value ?? "";
  // Pretty-print JSON if it parses
  try {
    const obj = JSON.parse(t);
    return JSON.stringify(obj, null, 2);
  } catch {
    return t;
  }
});

watch(
  () => props.planRunId,
  async (v) => {
    if (!v) return;
    await refresh();
    // Auto-open both quick picks if possible (best effort)
    await openPlanJson();
  }
);
</script>

<style scoped>
.card { border: 1px solid #ddd; border-radius: 12px; padding: 12px; display: grid; gap: 12px; }
.head { display: flex; justify-content: space-between; align-items: start; gap: 10px; }
.title { font-weight: 900; }
.sub { opacity: 0.85; font-size: 12px; margin-top: 4px; }
.actions { display: flex; gap: 10px; }
button { border: 1px solid #ddd; border-radius: 8px; padding: 7px 10px; cursor: pointer; }
button:disabled { opacity: 0.6; cursor: not-allowed; }
.error { border: 1px solid #f1b3b3; border-radius: 8px; padding: 10px; }
.empty { opacity: 0.8; font-size: 12px; }
.grid { display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 12px; align-items: start; }
@media (max-width: 1100px) { .grid { grid-template-columns: 1fr; } }

.section { border: 1px solid #eee; border-radius: 12px; padding: 10px; display: grid; gap: 10px; }
.sectionTitle { font-weight: 800; display: flex; align-items: center; gap: 8px; }
.pill { border: 1px solid #ddd; border-radius: 999px; padding: 3px 8px; font-size: 12px; opacity: 0.9; }
.list { display: grid; gap: 8px; max-height: 320px; overflow: auto; padding-right: 4px; }
.att {
  text-align: left;
  border: 1px solid #eee;
  border-radius: 10px;
  padding: 8px 10px;
  background: transparent;
}
.att.active { border-color: #ccc; }
.p { font-size: 12px; }
.m { opacity: 0.75; font-size: 11px; margin-top: 4px; }
.qp { display: flex; gap: 10px; flex-wrap: wrap; }
.hint { opacity: 0.75; font-size: 12px; }

.pre {
  margin: 0;
  border: 1px solid #eee;
  border-radius: 12px;
  padding: 10px;
  overflow: auto;
  max-height: 520px;
  font-size: 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
code { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 12px; }
</style>
