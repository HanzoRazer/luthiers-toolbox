<script setup lang="ts">
/**
 * PromoteToManufacturingButton.vue
 *
 * Button to promote an advisory variant to manufacturing candidate.
 * Handles RBAC and displays status feedback.
 */
import { computed, ref } from "vue";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const promoting = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("LTB_JWT") || "";
  const role = localStorage.getItem("LTB_USER_ROLE") || "";
  const uid = localStorage.getItem("LTB_USER_ID") || "";

  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  } else {
    if (role) h["x-user-role"] = role;
    if (uid) h["x-user-id"] = uid;
  }
  return h;
}

async function promote() {
  promoting.value = true;
  error.value = null;
  success.value = null;

  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(
        props.advisoryId
      )}/promote`,
      {
        method: "POST",
        headers: authHeaders(),
        credentials: "include",
        body: JSON.stringify({ label: null, note: null }),
      }
    );

    if (res.status === 401) throw new Error("Not authenticated");
    if (res.status === 403) throw new Error("Forbidden: requires role admin/operator/engineer");
    if (res.status === 409) throw new Error("Already promoted");
    if (!res.ok) throw new Error(`Promotion failed (${res.status})`);

    const data = await res.json();
    if (data.decision === "BLOCK") {
      error.value = `Blocked: ${data.reason || "policy"}`;
    } else {
      success.value = `Promoted! Candidate: ${data.manufactured_candidate_id || "created"}`;
    }
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    promoting.value = false;
  }
}
</script>

<template>
  <div class="promote-box">
    <button class="btn promote" :disabled="promoting" @click="promote">
      {{ promoting ? "Promoting..." : "Promote to Manufacturing" }}
    </button>
    <div v-if="error" class="feedback error">{{ error }}</div>
    <div v-if="success" class="feedback success">{{ success }}</div>
  </div>
</template>

<style scoped>
.promote-box {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.btn {
  padding: 10px 16px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  font-weight: 600;
}

.btn.promote {
  background: #0066cc;
  border-color: #0066cc;
  color: #fff;
}

.btn.promote:hover:not(:disabled) {
  background: #0052a3;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.feedback {
  font-size: 0.85rem;
  padding: 6px 10px;
  border-radius: 6px;
}

.feedback.error {
  background: #f8d7da;
  color: #721c24;
}

.feedback.success {
  background: #d4edda;
  color: #155724;
}
</style>
