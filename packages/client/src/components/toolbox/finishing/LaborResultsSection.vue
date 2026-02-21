<template>
  <div :class="styles.resultsSection">
    <h3>Labor Cost Breakdown</h3>
    <div :class="styles.costBreakdown">
      <div :class="styles.costRow">
        <span>Surface Preparation</span>
        <span :class="styles.costHours">{{ prepHours }} hrs</span>
        <span :class="styles.costValue">${{ (prepHours * hourlyRate).toFixed(2) }}</span>
      </div>
      <div :class="styles.costRow">
        <span>Finish Application</span>
        <span :class="styles.costHours">{{ applicationHours }} hrs</span>
        <span :class="styles.costValue">${{ (applicationHours * hourlyRate).toFixed(2) }}</span>
      </div>
      <div :class="styles.costRow">
        <span>Sanding Between Coats</span>
        <span :class="styles.costHours">{{ sandingHours }} hrs</span>
        <span :class="styles.costValue">${{ (sandingHours * hourlyRate).toFixed(2) }}</span>
      </div>
      <div :class="styles.costRow">
        <span>Final Buffing/Polishing</span>
        <span :class="styles.costHours">{{ buffingHours }} hrs</span>
        <span :class="styles.costValue">${{ (buffingHours * hourlyRate).toFixed(2) }}</span>
      </div>
      <div :class="styles.costRowTotal">
        <span><strong>Total Labor</strong></span>
        <span :class="styles.costHours"><strong>{{ totalHours }} hrs</strong></span>
        <span :class="styles.costValue"><strong>${{ totalLaborCost.toFixed(2) }}</strong></span>
      </div>
    </div>

    <div :class="styles.insightBox">
      <h4>Pricing Insight</h4>
      <p>
        At ${{ hourlyRate }}/hr, your finishing labor adds <strong>${{ totalLaborCost.toFixed(2) }}</strong>
        to the instrument cost. This doesn't include materials (~$30-150) or overhead.
      </p>
      <p>
        Many builders undercharge by 30-50% by not tracking finishing time accurately.
        This calculator helps you price realistically.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
  hourlyRate: number
  prepHours: number
  applicationHours: number
  sandingHours: number
  buffingHours: number
  totalHours: number
  totalLaborCost: number
}>()
</script>
