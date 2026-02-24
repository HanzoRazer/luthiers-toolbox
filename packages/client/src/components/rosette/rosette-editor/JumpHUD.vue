<script setup lang="ts">
/**
 * JumpHUD - Problem jump filter status and ring counts display
 * Extracted from RosetteEditorView.vue (Bundle 32.3.8)
 */
import { useRosetteStore } from '@/stores/rosetteStore'

defineProps<{
  styles: Record<string, string>
  hudPulse: boolean
}>()

const store = useRosetteStore()
</script>

<template>
  <div
    v-if="store.totalRingCount > 0"
    :class="[styles.jumpHud, { [styles.jumpHudPulse]: hudPulse }]"
  >
    <span :class="styles.pill">
      {{ store.jumpSeverity === "RED_ONLY" ? "Filter: RED only" : "Filter: RED+YELLOW" }}
    </span>
    <span :class="styles.pill">
      RED rings: {{ store.redRingCount }} / {{ store.totalRingCount }}
    </span>
    <span
      v-if="store.jumpRingPosition.total > 0"
      :class="styles.pill"
    >
      Focus: {{ store.jumpRingPosition.pos || "—" }} / {{ store.jumpRingPosition.total }}
    </span>
    <!-- Bundle 32.3.8: HUD help tooltip -->
    <span
      :class="styles.hudHelp"
      tabindex="0"
      aria-label="Jump hotkeys help"
    >
      ?
      <span
        :class="styles.hudTooltip"
        role="tooltip"
      >
        <div :class="styles.ttTitle">Jump hotkeys</div>
        <div :class="styles.ttRow"><kbd :class="styles.kbd">[</kbd> Prev problem</div>
        <div :class="styles.ttRow"><kbd :class="styles.kbd">]</kbd> Next problem</div>
        <div :class="styles.ttRow"><kbd :class="styles.kbd">w</kbd> Jump to worst</div>
        <div :class="styles.ttRow"><kbd :class="styles.kbd">Shift</kbd> + <kbd :class="styles.kbd">R</kbd> Toggle filter</div>
      </span>
    </span>
  </div>
</template>
