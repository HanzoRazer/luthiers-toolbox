<template>
  <div class="border rounded-lg bg-white shadow-sm p-3 text-[11px] text-gray-800">
    <h2 class="text-[12px] font-semibold text-gray-900 mb-1">
      Diff Summary
    </h2>
    <div class="grid grid-cols-1 md:grid-cols-3 gap-2">
      <div>
        <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
          Pattern & Segments
        </h3>
        <p class="text-[10px] text-gray-700">
          A: {{ diffSummary.pattern_type_a }} ·
          {{ diffSummary.segments_a }} seg
        </p>
        <p class="text-[10px] text-gray-700">
          B: {{ diffSummary.pattern_type_b }} ·
          {{ diffSummary.segments_b }} seg
        </p>
        <p
          class="text-[10px]"
          :class="deltaClass(diffSummary.segments_delta)"
        >
          Δ segments: {{ signed(diffSummary.segments_delta) }}
        </p>
      </div>
      <div>
        <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
          Radii
        </h3>
        <p class="text-[10px] text-gray-700">
          Inner A: {{ diffSummary.inner_radius_a }} ·
          B: {{ diffSummary.inner_radius_b }}
        </p>
        <p
          class="text-[10px]"
          :class="deltaClass(diffSummary.inner_radius_delta)"
        >
          Δ inner: {{ signedFloat(diffSummary.inner_radius_delta) }}
        </p>
        <p class="text-[10px] text-gray-700 mt-1">
          Outer A: {{ diffSummary.outer_radius_a }} ·
          B: {{ diffSummary.outer_radius_b }}
        </p>
        <p
          class="text-[10px]"
          :class="deltaClass(diffSummary.outer_radius_delta)"
        >
          Δ outer: {{ signedFloat(diffSummary.outer_radius_delta) }}
        </p>
      </div>
      <div>
        <h3 class="font-semibold text-[11px] text-gray-900 mb-0.5">
          Units & BBox
        </h3>
        <p class="text-[10px] text-gray-700">
          Units A: {{ diffSummary.units_a }} ·
          B: {{ diffSummary.units_b }}
        </p>
        <p
          class="text-[10px]"
          :class="diffSummary.units_same ? 'text-emerald-700' : 'text-amber-700'"
        >
          Units {{ diffSummary.units_same ? 'match' : 'differ' }}
        </p>
        <p class="text-[10px] text-gray-700 mt-1">
          BBox union:
          [{{ diffSummary.bbox_union.join(', ') }}]
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface RosetteDiffSummary {
  pattern_type_a: string
  pattern_type_b: string
  segments_a: number
  segments_b: number
  segments_delta: number
  inner_radius_a: number
  inner_radius_b: number
  inner_radius_delta: number
  outer_radius_a: number
  outer_radius_b: number
  outer_radius_delta: number
  units_a: string
  units_b: string
  units_same: boolean
  bbox_union: [number, number, number, number]
}

defineProps<{
  diffSummary: RosetteDiffSummary
}>()

function signed(n: number): string {
  if (n > 0) return `+${n}`;
  return `${n}`;
}

function signedFloat(n: number): string {
  const fixed = n.toFixed(2);
  if (n > 0) return `+${fixed}`;
  return fixed;
}

function deltaClass(delta: number): string {
  if (delta === 0) return "text-[10px] text-gray-600";
  if (delta > 0) return "text-[10px] text-indigo-700";
  return "text-[10px] text-amber-700";
}
</script>
