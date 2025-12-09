<!-- Patch N11.2 - ColumnStripEditor scaffolding -->

<template>
  <div class="column-editor">
    <h2>Column Strip Editor (Stub)</h2>
    <p>
      This is a placeholder. In N12/N13, this will edit strip widths, colors,
      and families.
    </p>
    <ul>
      <li v-for="n in 3" :key="n">Strip {{ n }} (stub)</li>
    </ul>
  </div>
</template>

<script setup lang="ts">
// no-op for scaffolding
</script>

<style scoped>
.column-editor {
  font-size: 0.9rem;
}
</style>
