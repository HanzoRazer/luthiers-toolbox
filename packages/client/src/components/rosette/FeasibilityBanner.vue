<template>
  <div class="card">
    <div class="row">
      <h3>Feasibility</h3>
      <div class="tog">
        <label class="small">
          <input type="checkbox" v-model="store.autoRefreshEnabled" />
          Auto-refresh
        </label>
        <button class="btn" @click="manualRefresh" :disabled="store.previewLoading || store.feasibilityLoading">
          Refresh Now
        </button>
      </div>
    </div>
    <div v-if="store.feasibilityError" class="err">{{ store.feasibilityError }}</div>
    <div class="pill" :data-risk="risk">
      <strong>{{ store.feasibilityLabel }}</strong>
      <span v-if="store.feasibilityLoading" class="spin">- updating...</span>
    </div>
    <div v-if="risk === 'RED'" class="block">
      <strong>BLOCKED:</strong> This design is currently <strong>RED</strong>.
      Fix warnings before saving snapshots or applying the design in downstream flows.
    </div>
    <div v-if="store.lastFeasibility?.warnings?.length" class="warn">
      <div><strong>Warnings:</strong></div>
      <ul>
        <li v-for="(w, i) in store.lastFeasibility.warnings" :key="i">{{ w }}</li>
      </ul>
    </div>
    <div class="mini" v-if="store.lastFeasibility">
      <div>Material Efficiency: {{ (store.lastFeasibility.material_efficiency * 100).toFixed(0) }}%</div>
      <div>Estimated Cut Time: {{ store.lastFeasibility.estimated_cut_time_min.toFixed(1) }} min</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRosetteStore } from "@/stores/rosetteStore";
import { useToastStore } from "@/stores/toastStore";

const store = useRosetteStore();
const toast = useToastStore();

const risk = computed(() => store.feasibilityRisk || "UNKNOWN");

async function manualRefresh() {
  await store.refreshPreviewAndFeasibility();
  toast.push("info", "Preview + feasibility refreshed.");
}
</script>

<style scoped>
.card {
  border: 1px solid #ddd;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}
.row {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.tog {
  display: flex;
  gap: 10px;
  align-items: center;
}
.small {
  font-size: 12px;
  color: #333;
  display: flex;
  gap: 6px;
  align-items: center;
}
.btn {
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #ccc;
  background: #f7f7f7;
  cursor: pointer;
}
.err {
  color: #a00;
  margin: 8px 0;
}
.pill {
  padding: 10px;
  border-radius: 12px;
  border: 1px solid #eee;
  background: #fafafa;
}
.pill[data-risk="GREEN"] {
  border-color: rgba(80, 200, 120, 0.55);
}
.pill[data-risk="YELLOW"] {
  border-color: rgba(240, 200, 80, 0.65);
}
.pill[data-risk="RED"] {
  border-color: rgba(240, 80, 80, 0.75);
  background: #fff4f4;
}
.spin {
  color: #666;
  font-size: 12px;
  margin-left: 6px;
}
.warn {
  margin-top: 10px;
  padding: 10px;
  border-radius: 10px;
  background: #fff7e6;
  border: 1px solid #f1d199;
}
.block {
  margin-top: 10px;
  padding: 10px;
  border-radius: 10px;
  background: #ffecec;
  border: 1px solid #f2aaaa;
}
.mini {
  margin-top: 8px;
  font-size: 12px;
  color: #333;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
