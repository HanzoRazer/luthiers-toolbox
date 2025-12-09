<template>
  <section class="saw-lab-shell">
    <header>
      <h2>CNC Saw Lab</h2>
      <p>Placeholder shell until Saw Lab is fully implemented.</p>
    </header>
    <div class="panels">
      <slot />
    </div>
  </section>
</template>

<script setup lang="ts">
</script>

<style scoped>
.saw-lab-shell {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>
