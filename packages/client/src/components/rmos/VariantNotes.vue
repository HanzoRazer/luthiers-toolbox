<script setup lang="ts">
/**
 * VariantNotes.vue
 *
 * Rating and notes editor for a variant.
 * Uses the advisory review API.
 */
import { computed, ref, watch } from "vue";
import StarRating from "@/components/rmos/StarRating.vue";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  apiBase?: string;
}>();

const apiBase = computed(() => props.apiBase ?? "/api");
const rating = ref<number | null>(null);
const notes = ref("");
const saving = ref(false);
const error = ref<string | null>(null);
const saved = ref(false);

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

async function save() {
  saving.value = true;
  error.value = null;
  saved.value = false;

  try {
    const res = await fetch(
      `${apiBase.value}/rmos/runs/${encodeURIComponent(props.runId)}/advisory/${encodeURIComponent(
        props.advisoryId
      )}/review`,
      {
        method: "POST",
        headers: authHeaders(),
        credentials: "include",
        body: JSON.stringify({
          rating: rating.value,
          notes: notes.value || null,
        }),
      }
    );

    if (!res.ok) throw new Error(`Save failed (${res.status})`);
    saved.value = true;
  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

// Reset when advisory changes
watch(
  () => props.advisoryId,
  () => {
    rating.value = null;
    notes.value = "";
    error.value = null;
    saved.value = false;
  }
);
</script>

<template>
  <div class="notes-box">
    <div class="title">
      Rating + Notes
    </div>

    <div class="rating-row">
      <label>Rating:</label>
      <StarRating v-model="rating" />
    </div>

    <textarea
      v-model="notes"
      placeholder="Operator notes for this variant..."
      rows="3"
      class="notes-input"
    />

    <div class="action-row">
      <button
        class="btn"
        :disabled="saving"
        @click="save"
      >
        {{ saving ? "Saving..." : "Save Review" }}
      </button>
      <span
        v-if="error"
        class="feedback error"
      >{{ error }}</span>
      <span
        v-if="saved"
        class="feedback success"
      >Saved!</span>
    </div>
  </div>
</template>

<style scoped>
.notes-box {
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 12px;
  padding: 12px;
}

.title {
  font-weight: 700;
  margin-bottom: 10px;
}

.rating-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.rating-row label {
  font-size: 0.9rem;
  font-weight: 500;
}

.notes-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ced4da;
  border-radius: 8px;
  font-size: 0.9rem;
  resize: vertical;
  min-height: 80px;
}

.notes-input:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.15);
}

.action-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
}

.btn {
  padding: 8px 14px;
  border: 1px solid rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  font-weight: 500;
}

.btn:hover:not(:disabled) {
  background: #f0f0f0;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.feedback {
  font-size: 0.85rem;
}

.feedback.error {
  color: #b00020;
}

.feedback.success {
  color: #155724;
}
</style>
