<template>
  <div :class="styles.burstPreview">
    <h3>Preview</h3>
    <div :class="styles.previewCanvas">
      <svg
        width="300"
        height="400"
        viewBox="0 0 300 400"
      >
        <!-- Body outline -->
        <ellipse
          cx="150"
          cy="200"
          rx="140"
          ry="180"
          fill="none"
          stroke="#333"
          stroke-width="2"
        />

        <!-- Burst gradient (simplified visual) -->
        <defs>
          <radialGradient
            id="burst-gradient"
            cx="50%"
            cy="40%"
          >
            <stop
              offset="0%"
              :stop-color="centerColor"
            />
            <stop
              v-if="midColor && burstType !== 'solid'"
              offset="50%"
              :stop-color="midColor"
            />
            <stop
              offset="100%"
              :stop-color="edgeColor"
            />
          </radialGradient>
        </defs>
        <ellipse
          cx="150"
          cy="160"
          rx="140"
          ry="180"
          fill="url(#burst-gradient)"
          opacity="0.8"
        />
      </svg>
    </div>
    <p :class="styles.previewNote">
      Simplified preview - actual burst will blend more smoothly
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  centerColor: string
  midColor: string
  edgeColor: string
  burstType: string
}>()
</script>
