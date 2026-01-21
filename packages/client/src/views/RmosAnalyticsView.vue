<template>
  <div class="min-h-screen bg-gray-50">
    <div class="max-w-7xl mx-auto py-6 px-4">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-gray-900">
          RMOS Material Analytics
        </h1>
        <p class="text-sm text-gray-600 mt-1">
          Lane-based risk analytics with material fragility awareness (MM-4)
        </p>
      </div>

      <RmosAnalyticsDashboard />
    </div>
  </div>
</template>

<script setup lang="ts">
import RmosAnalyticsDashboard from '@/components/rmos/RmosAnalyticsDashboard.vue';
</script>
