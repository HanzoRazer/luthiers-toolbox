<script setup lang="ts">
/**
 * QuickActionsPanel.vue
 *
 * Streamlined single-panel workflow for variant actions.
 * Combines Review + Promote + Reject into checkboxes with one Apply button.
 */
import { computed, ref, watch } from "vue";
import StarRating from "@/components/rmos/StarRating.vue";

const props = defineProps<{
  runId: string;
  advisoryId: string;
  variantStatus?: string;
  riskLevel?: string;
}>();

const emit = defineEmits<{
  done: [];
  close: [];
}>();

const apiBase = "/api/rmos";

// Form state
const doReview = ref(true);
const doPromote = ref(false);
const doReject = ref(false);
const rating = ref<number | null>(null);
const notes = ref("");
const rejectReason = ref("Aesthetic");
const rejectDetail = ref("");

// UI state
const saving = ref(false);
const error = ref<string | null>(null);
const success = ref<string | null>(null);
const stepsDone = ref<string[]>([]);

// Mutual exclusion: can't promote AND reject
watch(doPromote, (v) => { if (v) doReject.value = false; });
watch(doReject, (v) => { if (v) doPromote.value = false; });

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("LTB_JWT") || "";
  const role = localStorage.getItem("LTB_USER_ROLE") || "";
  const uid = localStorage.getItem("LTB_USER_ID") || "";

  const h: Record<string, string> = { "Content-Type": "application/json" };
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  } else {
    // Dev fallback: use header-based auth
    h["x-user-role"] = role || "operator";
    h["x-user-id"] = uid || "dev-user";
  }
  return h;
}

async function apply() {
  saving.value = true;
  error.value = null;
  success.value = null;
  stepsDone.value = [];

  const runId = encodeURIComponent(props.runId);
  const advisoryId = encodeURIComponent(props.advisoryId);

  try {
    // Step 1: Review (if checked)
    if (doReview.value) {
      const res = await fetch(
        `${apiBase}/runs/${runId}/advisory/${advisoryId}/review`,
        {
          method: "POST",
          headers: authHeaders(),
          credentials: "include",
          body: JSON.stringify({
            rating: rating.value,
            notes: notes.value || null,
            status: "REVIEWED",
          }),
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Review failed (${res.status})`);
      }
      stepsDone.value.push("Reviewed");
    }

    // Step 2: Promote OR Reject
    if (doPromote.value) {
      const res = await fetch(
        `${apiBase}/runs/${runId}/advisory/${advisoryId}/promote`,
        {
          method: "POST",
          headers: authHeaders(),
          credentials: "include",
          body: JSON.stringify({ label: null, note: null }),
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Promote failed (${res.status})`);
      }
      stepsDone.value.push("Promoted");
    } else if (doReject.value) {
      const res = await fetch(
        `${apiBase}/runs/${runId}/advisory/${advisoryId}/review`,
        {
          method: "POST",
          headers: authHeaders(),
          credentials: "include",
          body: JSON.stringify({
            rejected: true,
            status: "REJECTED",
            rejection_reason_code: rejectReason.value,
            rejection_reason_detail: rejectDetail.value || null,
          }),
        }
      );
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Reject failed (${res.status})`);
      }
      stepsDone.value.push("Rejected");
    }

    success.value = stepsDone.value.join(" → ") + " ✓";

    // Auto-close after success
    setTimeout(() => {
      emit("done");
      emit("close");
    }, 800);

  } catch (e: any) {
    error.value = e?.message ?? String(e);
  } finally {
    saving.value = false;
  }
}

const canApply = computed(() => {
  return doReview.value || doPromote.value || doReject.value;
});

const riskClass = computed(() => {
  const r = props.riskLevel?.toUpperCase();
  if (r === "GREEN") return "risk-green";
  if (r === "YELLOW") return "risk-yellow";
  if (r === "RED") return "risk-red";
  return "";
});
</script>

<template>
  <div class="quick-panel">
    <div class="header">
      <span class="title">Quick Actions</span>
      <span v-if="riskLevel" :class="['risk-badge', riskClass]">{{ riskLevel }}</span>
      <button class="close-btn" @click="$emit('close')">&times;</button>
    </div>

    <div class="variant-id">{{ advisoryId.slice(0, 12) }}...</div>

    <div class="actions-list">
      <!-- Review checkbox -->
      <label class="action-item">
        <input type="checkbox" v-model="doReview" :disabled="saving" />
        <span>Mark as Reviewed</span>
      </label>

      <!-- Rating (optional, shows when review checked) -->
      <div v-if="doReview" class="sub-field">
        <label>Rating:</label>
        <StarRating v-model="rating" />
      </div>

      <!-- Notes (optional) -->
      <div v-if="doReview" class="sub-field">
        <textarea
          v-model="notes"
          placeholder="Notes (optional)..."
          rows="2"
          :disabled="saving"
        />
      </div>

      <!-- Promote checkbox -->
      <label class="action-item">
        <input type="checkbox" v-model="doPromote" :disabled="saving || doReject" />
        <span>Promote to Manufacturing</span>
      </label>

      <!-- Reject checkbox -->
      <label class="action-item">
        <input type="checkbox" v-model="doReject" :disabled="saving || doPromote" />
        <span>Reject</span>
      </label>

      <!-- Reject reason (shows when reject checked) -->
      <div v-if="doReject" class="sub-field">
        <select v-model="rejectReason" :disabled="saving">
          <option>Aesthetic</option>
          <option>Technical</option>
          <option>Safety</option>
          <option>Quality</option>
          <option>Other</option>
        </select>
        <input
          v-model="rejectDetail"
          placeholder="Detail (optional)"
          :disabled="saving"
        />
      </div>
    </div>

    <!-- Feedback -->
    <div v-if="error" class="feedback error">{{ error }}</div>
    <div v-if="success" class="feedback success">{{ success }}</div>

    <!-- Apply button -->
    <div class="footer">
      <button
        class="apply-btn"
        :disabled="saving || !canApply"
        @click="apply"
      >
        {{ saving ? "Applying..." : "Apply & Close" }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.quick-panel {
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 16px;
  width: 320px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.title {
  font-weight: 700;
  font-size: 1rem;
  flex: 1;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.4rem;
  cursor: pointer;
  color: #666;
  line-height: 1;
}

.close-btn:hover {
  color: #000;
}

.variant-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #666;
  margin-bottom: 12px;
}

.risk-badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}

.risk-green { background: #d4edda; color: #155724; }
.risk-yellow { background: #fff3cd; color: #856404; }
.risk-red { background: #f8d7da; color: #721c24; }

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
}

.action-item input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.sub-field {
  margin-left: 26px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sub-field label {
  font-size: 0.85rem;
  color: #555;
}

.sub-field textarea,
.sub-field input,
.sub-field select {
  padding: 6px 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 0.85rem;
}

.sub-field textarea {
  resize: vertical;
  min-height: 50px;
}

.feedback {
  margin-top: 12px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 0.85rem;
}

.feedback.error {
  background: #f8d7da;
  color: #721c24;
}

.feedback.success {
  background: #d4edda;
  color: #155724;
}

.footer {
  margin-top: 16px;
}

.apply-btn {
  width: 100%;
  padding: 10px;
  background: #0066cc;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.apply-btn:hover:not(:disabled) {
  background: #0052a3;
}

.apply-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
