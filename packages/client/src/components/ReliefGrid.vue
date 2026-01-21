<template>
  <div>
    <div class="mb-2 text-xs text-gray-500">
      Relief Z grid (preview)
    </div>
    <table class="text-xs border-collapse">
      <tr
        v-for="(row, j) in verts"
        :key="j"
      >
        <td
          v-for="(pt, i) in row"
          :key="i"
          class="border px-1"
        >
          {{ pt[2].toFixed(2) }}
        </td>
      </tr>
    </table>
  </div>
</template>

<script setup lang="ts">
defineProps<{ verts: number[][][] }>()
</script>
