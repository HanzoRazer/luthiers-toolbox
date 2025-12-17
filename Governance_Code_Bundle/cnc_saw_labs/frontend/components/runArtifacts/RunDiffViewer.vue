<template>
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <div class="font-semibold">Diff Viewer</div>
      <button class="text-sm underline" @click="$emit('close')">Close</button>
    </div>

    <div class="text-sm text-gray-700">
      Base ID: <span class="font-mono text-xs">{{ baseId }}</span>
    </div>

    <div class="flex items-center gap-2">
      <input v-model="otherId" class="border rounded px-2 py-1 w-full" placeholder="Other artifact_id to compare" />
      <button class="border rounded px-3 py-1" @click="runDiff()" :disabled="!otherId">Compare</button>
    </div>

    <div v-if="loading" class="text-sm">Comparing…</div>

    <div v-else-if="diff">
      <div class="text-sm text-gray-700">
        Changed fields: <span class="font-semibold">{{ diff.summary.changed_count }}</span>
      </div>

      <pre class="text-xs bg-gray-50 border rounded p-2 overflow-auto max-h-[320px]">{{ pretty(diff.summary) }}</pre>

      <div class="border rounded p-2">
        <div class="text-sm font-semibold mb-2">Field changes</div>

        <div v-if="diff.changed_fields.length === 0" class="text-sm text-gray-600">
          No changes in governance fields.
        </div>

        <div v-else class="space-y-2">
          <div v-for="c in diff.changed_fields" :key="c.field" class="border rounded p-2">
            <div class="text-sm">
              <span class="font-semibold">{{ c.field }}</span>
              <span class="text-gray-600">•</span>
              <span class="font-mono text-xs">{{ c.path }}</span>
            </div>
            <div class="grid grid-cols-2 gap-2 mt-2">
              <pre class="text-xs bg-white border rounded p-2 overflow-auto">{{ pretty(c.a) }}</pre>
              <pre class="text-xs bg-white border rounded p-2 overflow-auto">{{ pretty(c.b) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-sm text-gray-600">
      Enter an artifact ID and click Compare.
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";

const props = defineProps<{ baseId: string }>();
defineEmits<{ (e: "close"): void }>();

const otherId = ref("");
const diff = ref<any>(null);
const loading = ref(false);

function pretty(obj: any) {
  return JSON.stringify(obj, null, 2);
}

async function runDiff() {
  loading.value = true;
  diff.value = null;
  try {