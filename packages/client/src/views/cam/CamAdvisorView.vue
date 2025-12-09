<script setup lang="ts">
/**
 * CAM Advisor View (Wave 12)
 *
 * Combined view hosting:
 * - CamAdvisorPanel (left/top)
 * - GCodeExplainerPanel (right/bottom)
 *
 * Route: /cam/advisor
 */
import CamAdvisorPanel from "@/components/cam/CamAdvisorPanel.vue";
import GCodeExplainerPanel from "@/components/cam/GCodeExplainerPanel.vue";
</script>

<template>
  <div class="flex min-h-screen flex-col gap-6 bg-slate-950 p-4 md:p-6">
    <!-- Header -->
    <header>
      <h1 class="text-2xl font-semibold text-slate-50">
        CAM Advisor &amp; G-Code Explainer
      </h1>
      <p class="mt-1 text-sm text-slate-300">
        Physics-aware CAM assistant powered by RMOS 2.0 and the Calculator
        Spine.
      </p>
    </header>

    <!-- Main Content -->
    <div class="grid gap-6 lg:grid-cols-2">
      <CamAdvisorPanel />
      <GCodeExplainerPanel />
    </div>

    <!-- Footer -->
    <footer
      class="mt-auto border-t border-slate-800 pt-4 text-center text-xs text-slate-500"
    >
      Wave 11 + 12 — AI-CAM Module
    </footer>
  </div>
</template>
