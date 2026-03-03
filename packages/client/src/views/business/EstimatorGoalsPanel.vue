<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import type { InstrumentType } from "@/types/businessEstimator";

interface Goal { id: string; name: string; instrument_type: string; target_cost: number; target_hours: number; progress_pct: number; status: "active" | "achieved" | "archived"; }
const goals = ref<Goal[]>([]);
const showCreateForm = ref(false);
const newGoal = ref({ name: "", instrument_type: "acoustic_dreadnought" as InstrumentType, target_cost: 1500, target_hours: 100 });
const STORAGE_KEY = "ltb:estimator:goals:v1";
const activeGoals = computed(() => goals.value.filter((g) => g.status === "active"));

function loadGoals(): void { try { const s = localStorage.getItem(STORAGE_KEY); if (s) goals.value = JSON.parse(s); } catch (e) { console.warn(e); } }
function saveGoals(): void { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(goals.value)); } catch (e) { console.warn(e); } }
function createGoal(): void {
  if (!newGoal.value.name.trim()) return;
  goals.value.unshift({ id: crypto.randomUUID(), name: newGoal.value.name, instrument_type: newGoal.value.instrument_type, target_cost: newGoal.value.target_cost, target_hours: newGoal.value.target_hours, progress_pct: 0, status: "active" });
  saveGoals(); showCreateForm.value = false; newGoal.value = { name: "", instrument_type: "acoustic_dreadnought" as InstrumentType, target_cost: 1500, target_hours: 100 };
}
function deleteGoal(id: string): void { goals.value = goals.value.filter((g) => g.id !== id); saveGoals(); }
function formatType(t: string): string { return t.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()); }
onMounted(() => loadGoals());
</script>

<template>
  <div class="goals-panel">
    <header class="panel-header">
      <h3>Pricing Goals</h3><button
        v-if="!showCreateForm"
        type="button"
        class="btn-add"
        @click="showCreateForm = true"
      >
        + New Goal
      </button>
    </header>
    <div
      v-if="showCreateForm"
      class="create-form"
    >
      <div class="form-row">
        <label>Goal Name</label><input
          v-model="newGoal.name"
          type="text"
          placeholder="e.g., Master Build"
        >
      </div>
      <div class="form-row">
        <label>Instrument</label><select v-model="newGoal.instrument_type">
          <option value="acoustic_dreadnought">
            Acoustic Dreadnought
          </option><option value="electric_solid">
            Electric Solid
          </option><option value="bass_4">
            Bass 4-String
          </option>
        </select>
      </div>
      <div class="form-row-group">
        <div class="form-row">
          <label>Target Cost</label><input
            v-model.number="newGoal.target_cost"
            type="number"
            min="0"
          >
        </div><div class="form-row">
          <label>Target Hours</label><input
            v-model.number="newGoal.target_hours"
            type="number"
            min="0"
          >
        </div>
      </div>
      <div class="form-actions">
        <button
          type="button"
          class="btn-secondary"
          @click="showCreateForm = false"
        >
          Cancel
        </button><button
          type="button"
          class="btn-primary"
          @click="createGoal"
        >
          Create
        </button>
      </div>
    </div>
    <div
      v-if="activeGoals.length > 0"
      class="goals-section"
    >
      <h4>Active Goals</h4><div
        v-for="goal in activeGoals"
        :key="goal.id"
        class="goal-card"
      >
        <div class="goal-header">
          <div class="goal-name">
            {{ goal.name }}
          </div><button
            type="button"
            class="btn-icon"
            @click="deleteGoal(goal.id)"
          >
            &times;
          </button>
        </div><div class="goal-meta">
          {{ formatType(goal.instrument_type) }} | Target: ${{ goal.target_cost }} | {{ goal.target_hours }}h
        </div><div class="progress-bar">
          <div
            class="progress-fill"
            :style="{ width: goal.progress_pct + '%' }"
          />
        </div>
      </div>
    </div>
    <div
      v-if="goals.length === 0 && !showCreateForm"
      class="empty-state"
    >
      <p>No goals yet.</p>
    </div>
  </div>
</template>

<style scoped>
.goals-panel { background: #0d1020; border: 1px solid #1e2438; border-radius: 4px; padding: 16px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.panel-header h3 { font-size: 10px; letter-spacing: 2px; color: #4060c0; text-transform: uppercase; margin: 0; }
.btn-add { padding: 4px 10px; font-size: 9px; background: #2050a0; border: 1px solid #3060c0; color: #e0e8ff; border-radius: 3px; cursor: pointer; }
.create-form { background: #14192a; border: 1px solid #1e2438; border-radius: 4px; padding: 16px; margin-bottom: 16px; }
.form-row { margin-bottom: 12px; }
.form-row label { display: block; font-size: 9px; color: #6080b0; text-transform: uppercase; margin-bottom: 4px; }
.form-row input, .form-row select { width: 100%; padding: 8px; font-size: 12px; background: #0d1020; border: 1px solid #2a3040; color: #c0c8e0; border-radius: 3px; }
.form-row-group { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 16px; }
.btn-secondary, .btn-primary { padding: 8px 16px; font-size: 10px; text-transform: uppercase; border-radius: 3px; cursor: pointer; }
.btn-secondary { background: #14192a; border: 1px solid #2a3040; color: #8090b0; }
.btn-primary { background: #2050a0; border: 1px solid #3060c0; color: #e0e8ff; }
.goals-section { margin-bottom: 16px; }
.goals-section h4 { font-size: 9px; color: #6080b0; text-transform: uppercase; margin: 0 0 10px; }
.goal-card { background: #14192a; border: 1px solid #1e2438; border-radius: 4px; padding: 12px; margin-bottom: 8px; }
.goal-header { display: flex; justify-content: space-between; margin-bottom: 4px; }
.goal-name { font-size: 12px; font-weight: 600; color: #c0c8e0; }
.btn-icon { width: 20px; height: 20px; background: transparent; border: 1px solid #2a3040; color: #6080b0; border-radius: 3px; cursor: pointer; }
.goal-meta { font-size: 10px; color: #506090; margin-bottom: 8px; }
.progress-bar { height: 6px; background: #1a2030; border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: #4080f0; }
.empty-state { text-align: center; padding: 24px; color: #506090; font-size: 12px; }
</style>
