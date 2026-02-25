<script setup lang="ts">
/**
 * RadiusDishDocs.vue - Documentation tab content
 * Extracted from RadiusDishDesigner.vue
 */
</script>

<template>
  <div class="space-y-4">
    <h3 class="font-semibold text-lg">
      Documentation & Theory
    </h3>

    <div class="grid md:grid-cols-2 gap-4">
      <div class="p-4 border rounded">
        <h4 class="font-medium mb-2">
          Acoustic Guitar Radius Explained
        </h4>
        <p class="text-sm opacity-80 mb-3">
          Comprehensive guide to radius arches in acoustic guitar construction.
          Covers theory, measurements, and acoustic impact.
        </p>
        <a
          href="/radius_dish/Acoustic_Guitar_Radius_Explained.pdf"
          target="_blank"
          class="text-blue-600 underline text-sm"
        >
          Open PDF
        </a>
      </div>

      <div class="p-4 border rounded">
        <h4 class="font-medium mb-2">
          Router Trammel Guide
        </h4>
        <p class="text-sm opacity-80 mb-3">
          Step-by-step instructions for building and using a router trammel
          to create radius dishes by hand (alternative to CNC).
        </p>
        <a
          href="/radius_dish/Router_Trammel_Radius_Dish_Guide.pdf"
          target="_blank"
          class="text-blue-600 underline text-sm"
        >
          Open PDF
        </a>
      </div>
    </div>

    <div class="mt-4 p-4 bg-gray-50 rounded">
      <h4 class="font-medium mb-2">
        Quick Reference
      </h4>
      <div class="text-sm space-y-2 opacity-80">
        <p><strong>15 ft radius:</strong> Traditional carved archtop guitars (Gibson L-5, Super 400)</p>
        <p><strong>25 ft radius:</strong> Flatter arch, easier for beginners, modern jazz guitars</p>
        <p><strong>Common widths:</strong> 14-17 inches for guitar tops, 15-18 inches for backs</p>
        <p><strong>Typical depth:</strong> 0.5-0.75 inches for 15ft, 0.3-0.5 inches for 25ft</p>
      </div>
    </div>
  </div>
</template>
