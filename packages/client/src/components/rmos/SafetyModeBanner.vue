<template>
  <div
    class="w-full text-[11px] px-3 py-2 flex items-center justify-between relative"
    :class="bannerClass"
  >
    <div class="flex items-center gap-2">
      <span class="font-semibold">Safety mode: {{ modeLabel }}</span>
      <span
        v-if="state?.set_by"
        class="text-gray-800"
      >
        (set by {{ state.set_by }} at {{ state.set_at }})
      </span>
    </div>
    <div class="flex items-center gap-2">
      <span
        v-if="hint"
        class="text-gray-700"
      >
        {{ hint }}
      </span>
      <button
        class="px-2 py-[2px] rounded border text-[10px] bg-white hover:bg-gray-50"
        @click="showMentorPanel = !showMentorPanel"
      >
        Mentor overrides
      </button>
    </div>

    <div
      v-if="showMentorPanel"
      class="absolute right-2 top-10 z-30 w-80"
    >
      <MentorOverridePanel @close="showMentorPanel = false" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRmosSafetyStore } from "@/stores/useRmosSafetyStore";
import MentorOverridePanel from "@/components/rmos/MentorOverridePanel.vue";
import { safeModeClass, safeModeLabel as getModeLabel } from "@/models/rmos_safety";

const store = useRmosSafetyStore();
const showMentorPanel = ref(false);

const state = computed(() => store.modeState);
const mode = computed(() => store.currentMode);

const modeLabel = computed(() => getModeLabel(mode.value));

const modeIcon = computed(() => {
  switch (mode.value) {
    case "unrestricted":
      return "✅";
    case "apprentice":
      return "⚠️";
    case "mentor_review":
      return "👁️";
    default:
      return "🔒";
  }
});

const bannerClass = computed(() => safeModeClass(mode.value));

const hint = computed(() => {
  switch (mode.value) {
    case "unrestricted":
      return "Full capabilities enabled; high-risk actions still logged.";
    case "apprentice":
      return "Some high-risk actions are blocked until mentor approval.";
    case "mentor_review":
      return "Mentor supervision mode; risky actions may require override.";
    default:
      return "";
  }
});

function formatTime(ts?: string | null): string {
  if (!ts) return "";
  try {
    const date = new Date(ts);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {
    return ts;
  }
}

onMounted(() => {
  if (!state.value) {
    store.fetchMode();
  }
});
</script>

<style scoped>
/* Banner styling handled by dynamic class binding */
</style>
