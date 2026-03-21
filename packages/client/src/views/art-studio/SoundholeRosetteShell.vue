<script setup lang="ts">
/**
 * SoundholeRosetteShell — Unified soundhole/rosette workspace (CU-A1)
 *
 * Four stages:
 *   Stage 1: Rosette Designer (RosetteWheelView)
 *   Stage 2: Soundhole (SoundholeDesignerView)
 *   Stage 3: Purfling (PurflingDesignerView)
 *   Stage 4: Binding (BindingDesignerView)
 *
 * TODO: SoundholeDesignerView, PurflingDesignerView, BindingDesignerView have
 * planned but unbuilt API endpoints. Stage 1 (Rosette Designer) is fully
 * functional. Others render UI only until backend endpoints are implemented.
 */
import { ref, defineAsyncComponent, onMounted } from "vue";
import { useAgenticEvents } from '@/composables/useAgenticEvents'

// E-1: Agentic Spine event emission
const { emitViewRendered, emitAnalysisCompleted } = useAgenticEvents()

// E-1: Emit view_rendered on mount
onMounted(() => {
  emitViewRendered('soundhole_rosette_shell')
})

type StageId = "rosette" | "soundhole" | "purfling" | "binding";

const stages: { id: StageId; label: string; icon: string }[] = [
  { id: "rosette", label: "Rosette Designer", icon: "🌹" },
  { id: "soundhole", label: "Soundhole", icon: "⭕" },
  { id: "purfling", label: "Purfling", icon: "〰️" },
  { id: "binding", label: "Binding", icon: "🔲" },
];

const activeStage = ref<StageId>("rosette");

function setStage(id: StageId) {
  activeStage.value = id;
}

// Lazy-loaded stage content to avoid pulling all views at once
const RosetteStage = defineAsyncComponent(() =>
  import("@/views/art-studio/RosetteWheelView.vue")
);
const SoundholeStage = defineAsyncComponent(() =>
  import("@/views/art-studio/SoundholeDesignerView.vue")
);
const PurflingStage = defineAsyncComponent(() =>
  import("@/views/art-studio/PurflingDesignerView.vue")
);
const BindingStage = defineAsyncComponent(() =>
  import("@/views/art-studio/BindingDesignerView.vue")
);
</script>

<template>
  <div class="soundhole-rosette-shell">
    <header class="shell-header">
      <h1 class="shell-title">Soundhole & Rosette Workspace</h1>
      <p class="shell-subtitle">
        Rosette designer · Soundhole · Purfling · Binding
      </p>
    </header>

    <nav class="stage-tabs" role="tablist">
      <button
        v-for="stage in stages"
        :key="stage.id"
        type="button"
        role="tab"
        :aria-selected="activeStage === stage.id"
        :aria-controls="`stage-${stage.id}`"
        :id="`tab-${stage.id}`"
        class="stage-tab"
        :class="{ active: activeStage === stage.id }"
        @click="setStage(stage.id)"
      >
        <span class="stage-icon">{{ stage.icon }}</span>
        <span class="stage-label">{{ stage.label }}</span>
      </button>
    </nav>

    <div class="stage-content" role="tabpanel" :id="`stage-${activeStage}`" :aria-labelledby="`tab-${activeStage}`">
      <!-- Stage 1: Rosette Designer (fully functional) -->
      <div v-show="activeStage === 'rosette'" class="stage-panel" data-stage="rosette">
        <Suspense>
          <component :is="RosetteStage" />
          <template #fallback>
            <div class="stage-loading">Loading rosette designer…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 2: Soundhole (TODO: planned but unbuilt API endpoints; UI only until backend) -->
      <div v-show="activeStage === 'soundhole'" class="stage-panel" data-stage="soundhole">
        <Suspense>
          <component :is="SoundholeStage" />
          <template #fallback>
            <div class="stage-loading">Loading soundhole designer…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 3: Purfling (TODO: planned but unbuilt API endpoints; UI only until backend) -->
      <div v-show="activeStage === 'purfling'" class="stage-panel" data-stage="purfling">
        <Suspense>
          <component :is="PurflingStage" />
          <template #fallback>
            <div class="stage-loading">Loading purfling designer…</div>
          </template>
        </Suspense>
      </div>

      <!-- Stage 4: Binding (TODO: planned but unbuilt API endpoints; UI only until backend) -->
      <div v-show="activeStage === 'binding'" class="stage-panel" data-stage="binding">
        <Suspense>
          <component :is="BindingStage" />
          <template #fallback>
            <div class="stage-loading">Loading binding designer…</div>
          </template>
        </Suspense>
      </div>
    </div>
  </div>
</template>

<style scoped>
.soundhole-rosette-shell {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  padding: 1rem;
  max-width: 1600px;
  margin: 0 auto;
}

.shell-header {
  margin-bottom: 1rem;
}

.shell-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.25rem;
  color: var(--color-text-primary, #1e293b);
}

.shell-subtitle {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-secondary, #64748b);
}

.stage-tabs {
  display: flex;
  gap: 0.25rem;
  padding: 0.25rem;
  background: var(--color-bg-secondary, #f1f5f9);
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  flex-shrink: 0;
}

.stage-tab {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1rem;
  border: none;
  border-radius: 0.375rem;
  background: transparent;
  color: var(--color-text-secondary, #64748b);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.stage-tab:hover {
  background: var(--color-bg-tertiary, #e2e8f0);
  color: var(--color-text-primary, #334155);
}

.stage-tab.active {
  background: var(--color-accent-bg, #2563eb);
  color: white;
}

.stage-icon {
  font-size: 1.1rem;
}

.stage-content {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.stage-panel {
  flex: 1;
  min-height: 400px;
  display: flex;
  flex-direction: column;
  overflow: auto;
}

.stage-loading {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-secondary, #64748b);
  font-size: 0.9rem;
}
</style>
