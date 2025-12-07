<template>
  <div class="border rounded-md p-3 bg-white text-[11px] space-y-2 shadow-lg">
    <div class="flex items-center justify-between">
      <div class="font-semibold text-xs">Mentor Override Panel</div>
      <button
        class="text-[10px] text-gray-500 hover:text-gray-800"
        @click="$emit('close')"
      >
        ✕
      </button>
    </div>

    <p class="text-gray-600">
      Generate one-time override tokens for apprentices. Share the token verbally or
      on paper; they'll paste it when prompted.
    </p>

    <div class="grid grid-cols-1 gap-2">
      <!-- Action selector -->
      <label class="flex flex-col gap-1">
        <span class="text-gray-700">Action</span>
        <select
          v-model="action"
          class="border rounded px-2 py-1 text-[11px]"
        >
          <option value="start_job">Start job (normal lane)</option>
          <option value="run_experimental_lane">Run experimental lane</option>
          <option value="promote_preset">Promote preset</option>
        </select>
      </label>

      <!-- Mentor name -->
      <label class="flex flex-col gap-1">
        <span class="text-gray-700">Mentor (optional)</span>
        <input
          v-model="createdBy"
          type="text"
          placeholder="e.g. Ross, Mentor1"
          class="border rounded px-2 py-1 text-[11px]"
        />
      </label>

      <!-- TTL -->
      <label class="flex flex-col gap-1">
        <span class="text-gray-700">TTL (minutes)</span>
        <input
          v-model.number="ttl"
          type="number"
          min="1"
          max="120"
          class="border rounded px-2 py-1 text-[11px] w-20"
        />
      </label>

      <!-- Generate button -->
      <div>
        <button
          class="px-3 py-1 rounded bg-blue-600 text-white text-[11px] disabled:opacity-50"
          :disabled="creating"
          @click="onGenerate"
        >
          {{ creating ? "Generating…" : "Generate override token" }}
        </button>
      </div>

      <p v-if="error" class="text-[11px] text-red-600">
        {{ error }}
      </p>
    </div>

    <!-- Recent tokens -->
    <div v-if="tokens.length" class="mt-2 border-t pt-2 space-y-1">
      <div class="font-semibold text-xs">Recent tokens (this session)</div>
      <table class="w-full text-[10px] border-collapse">
        <thead>
          <tr class="border-b">
            <th class="text-left p-1">Token</th>
            <th class="text-left p-1">Action</th>
            <th class="text-left p-1">Created by</th>
            <th class="text-left p-1">Expires</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tokens" :key="t.token" class="border-b last:border-0">
            <td class="p-1 font-mono">
              {{ t.token }}
            </td>
            <td class="p-1">
              {{ t.action }}
            </td>
            <td class="p-1">
              {{ t.created_by || "—" }}
            </td>
            <td class="p-1">
              {{ t.expires_at || "—" }}
            </td>
          </tr>
        </tbody>
      </table>
      <p class="text-[10px] text-gray-500">
        Share the token exactly as shown. Each token is single-use and short-lived.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { OverrideToken } from "@/models/rmos_safety";
import { useRmosSafetyStore } from "@/stores/useRmosSafetyStore";

const safety = useRmosSafetyStore();

const action = ref<string>("start_job");
const createdBy = ref<string>("");
const ttl = ref<number>(15);

const creating = ref(false);
const error = ref<string | null>(null);
const tokens = ref<OverrideToken[]>([]);

async function onGenerate() {
  error.value = null;
  creating.value = true;
  try {
    const token = await safety.createOverride(action.value, createdBy.value || undefined, ttl.value);
    tokens.value.unshift(token);
    // Limit list length
    if (tokens.value.length > 10) tokens.value.pop();
  } catch (e: any) {
    error.value = String(e.message || e);
  } finally {
    creating.value = false;
  }
}
</script>
