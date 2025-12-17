<template>
  <div class="p-4 space-y-4">
    <div class="flex items-center gap-3">
      <h2 class="text-xl font-semibold">Run Artifacts</h2>

      <select v-model="filters.kind" class="border rounded px-2 py-1">
        <option value="">All kinds</option>
        <option value="feasibility">feasibility</option>
        <option value="toolpaths">toolpaths</option>
      </select>

      <select v-model="filters.status" class="border rounded px-2 py-1">
        <option value="">All statuses</option>
        <option value="OK">OK</option>
        <option value="BLOCKED">BLOCKED</option>
        <option value="ERROR">ERROR</option>
      </select>

      <input v-model="filters.tool_id" class="border rounded px-2 py-1 w-60" placeholder="tool_id (optional)" />
      <button class="border rounded px-3 py-1" @click="refresh()">Refresh</button>
    </div>

    <div class="grid grid-cols-12 gap-4">
      <!-- List -->
      <div class="col-span-5 border rounded p-2">
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm text-gray-600">Latest runs</div>
          <button class="text-sm underline" @click="loadMore()" :disabled="!nextCursor">Load more</button>
        </div>

        <div v-if="loadingList" class="text-sm">Loading…</div>
        <div v-else class="space-y-2">
          <div
            v-for="r in runs"
            :key="r.artifact_id"
            class="border rounded p-2 cursor-pointer"
            :class="selectedId === r.artifact_id ? 'bg-gray-50' : ''"
            @click="selectRun(r.artifact_id)"
          >
            <div class="flex items-center justify-between">
              <div class="font-mono text-xs">{{ r.artifact_id }}</div>
              <span class="text-xs px-2 py-0.5 rounded border">{{ r.status }}</span>
            </div>

            <div class="text-sm mt-1">
              <span class="font-semibold">{{ r.kind }}</span>
              <span class="text-gray-600">•</span>
              <span class="text-gray-600">{{ r.created_utc }}</span>
            </div>

            <div class="text-xs text-gray-700 mt-1">
              tool_id: <span class="font-mono">{{ r.index_meta?.tool_id || "-" }}</span>
              • material: <span class="font-mono">{{ r.index_meta?.material_id || "-" }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detail -->
      <div class="col-span-7 border rounded p-2">
        <div class="flex items-center justify-between mb-2">
          <div class="text-sm text-gray-600">Detail</div>
          <div class="flex items-center gap-2">
            <button class="text-sm underline" @click="copySelectedId()" :disabled="!selectedId">Copy ID</button>
            <button class="text-sm underline" @click="openDiff()" :disabled="!selectedId">Diff…</button>
          </div>
        </div>

        <div v-if="loadingDetail" class="text-sm">Loading…</div>
        <div v-else-if="!detail" class="text-sm text-gray-600">Select a run artifact.</div>
        <div v-else>
          <div class="text-sm mb-2">
            <span class="font-semibold">{{ detail.kind }}</span>
            <span class="text-gray-600">•</span>
            <span class="font-mono text-xs">{{ detail.artifact_id }}</span>
          </div>

          <pre class="text-xs bg-gray-50 border rounded p-2 overflow-auto max-h-[520px]">{{ pretty(detail) }}</pre>
        </div>
      </div>
    </div>

    <!-- Diff modal-ish -->
    <div v-if="showDiff" class="border rounded p-3 bg-white">
      <RunDiffViewer :base-id="selectedId!" @close="showDiff=false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from "vue";
import RunDiffViewer from "./RunDiffViewer.vue";

type RunIndexRow = {
  artifact_id: string;
  kind: string;
  status: string;
  created_utc: string;
  session_id: string;
  index_meta: Record<string, any>;
};

const runs = ref<RunIndexRow[]>([]);
const nextCursor = ref<string | null>(null);
const selectedId = ref<string | null>(null);
const detail = ref<any>(null);

const loadingList = ref(false);
const loadingDetail = ref(false);
const showDiff = ref(false);

const filters = reactive({
  kind: "",
  status: "",
  tool_id: "",
});

function pretty(obj: any) {
  return JSON.stringify(obj, null, 2);
}

async function fetchRuns(cursor?: string | null) {
  loadingList.value = true;
  try {
    const params = new URLSearchParams();
    params.set("limit", "50");
    if (cursor) params.set("cursor", cursor);
    if (filters.kind) params.set("kind", filters.kind);
    if (filters.status) params.set("status", filters.status);
    if (filters.tool_id) params.set("tool_id", filters.tool_id);

    const res = await fetch(`/api/runs?${params.toString()}`);
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return data as { items: RunIndexRow[]; next_cursor: string | null };
  } finally {
    loadingList.value = false;
  }
}

async function refresh() {
  selectedId.value = null;
  detail.value = null;
  const data = await fetchRuns(null);
  runs.value = data.items;
  nextCursor.value = data.next_cursor;
}

async function loadMore() {
  if (!nextCursor.value) return;
  const data = await fetchRuns(nextCursor.value);
  runs.value = runs.value.concat(data.items);
  nextCursor.value = data.next_cursor;
}

async function selectRun(id: string) {
  selectedId.value = id;
  loadingDetail.value = true;
  try {
    const res = await fetch(`/api/runs/${id}`);
    if (!res.ok) throw new Error(await res.text());
    detail.value = await res.json();
  } finally {
    loadingDetail.value = false;
  }
}

async function copySelectedId() {
  if (!selectedId.value) return;
  await navigator.clipboard.writeText(selectedId.value);
}