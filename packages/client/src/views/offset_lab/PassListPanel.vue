<template>
  <div class="border rounded-lg p-3 bg-white space-y-2">
    <div class="flex items-center justify-between">
      <h3 class="text-xs font-semibold text-gray-700">
        Passes
      </h3>
      <span class="text-[10px] text-gray-500">{{ passStats.length }} total</span>
    </div>
    <div class="max-h-40 overflow-auto text-[11px]">
      <table class="w-full">
        <thead>
          <tr class="text-left text-gray-500">
            <th class="px-1 py-1">
              #
            </th>
            <th class="px-1 py-1">
              Pts
            </th>
            <th class="px-1 py-1">
              Len ({{ units }})
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(p, i) in passStats"
            :key="i"
            class="hover:bg-gray-50 cursor-pointer"
            @mouseenter="emit('hover', i)"
            @mouseleave="emit('hover', null)"
            @click="emit('select', i)"
          >
            <td class="px-1 py-1">
              {{ p.idx }}
            </td>
            <td class="px-1 py-1">
              {{ p.pts }}
            </td>
            <td class="px-1 py-1">
              {{ p.length.toFixed(2) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
export interface PassStat {
  idx: number
  pts: number
  length: number
}

defineProps<{
  passStats: PassStat[]
  units: 'mm' | 'inch'
}>()

const emit = defineEmits<{
  hover: [index: number | null]
  select: [index: number]
}>()
</script>
