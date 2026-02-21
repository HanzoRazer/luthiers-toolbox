<template>
  <div class="border rounded p-3">
    <h2 class="text-lg font-bold mb-2">
      Preset Comparison Results
    </h2>
    <table class="w-full text-xs border-collapse">
      <thead>
        <tr class="bg-gray-100">
          <th class="border px-2 py-1">
            Preset
          </th>
          <th class="border px-2 py-1">
            Time (s)
          </th>
          <th class="border px-2 py-1">
            Risk
          </th>
          <th class="border px-2 py-1">
            Thin Floor
          </th>
          <th class="border px-2 py-1">
            High Load
          </th>
          <th class="border px-2 py-1">
            Avg Floor (mm)
          </th>
          <th class="border px-2 py-1">
            Min Floor (mm)
          </th>
          <th class="border px-2 py-1">
            Max Load
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in comparisons"
          :key="row.name"
          :class="{
            'bg-blue-50 cursor-pointer hover:bg-blue-100': selectedName === row.name,
            'hover:bg-gray-50 cursor-pointer': selectedName !== row.name
          }"
          @click="$emit('select', row.name)"
        >
          <td class="border px-2 py-1 font-medium">
            {{ row.name }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.est_time_s.toFixed(1) }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.risk_score.toFixed(2) }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.thin_floor_count }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.high_load_count }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.avg_floor_thickness.toFixed(2) }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.min_floor_thickness.toFixed(2) }}
          </td>
          <td class="border px-2 py-1 text-right">
            {{ row.max_load_index.toFixed(2) }}
          </td>
        </tr>
      </tbody>
    </table>
    <p
      v-if="selectedName"
      class="text-xs text-gray-600 mt-2"
    >
      Selected: <strong>{{ selectedName }}</strong>
    </p>
  </div>
</template>

<script setup lang="ts">
interface ComparisonRow {
  name: string
  est_time_s: number
  risk_score: number
  thin_floor_count: number
  high_load_count: number
  avg_floor_thickness: number
  min_floor_thickness: number
  max_load_index: number
}

defineProps<{
  comparisons: ComparisonRow[]
  selectedName: string | null
}>()

defineEmits<{
  select: [name: string]
}>()
</script>
