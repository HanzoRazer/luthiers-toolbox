<script setup lang="ts">
/**
 * Tier Badge Component
 *
 * Displays the user's subscription tier with appropriate styling.
 */

import { computed } from "vue";
import type { UserTier } from "@/auth/types";

const props = withDefaults(
  defineProps<{
    tier: UserTier;
    size?: "sm" | "md" | "lg";
  }>(),
  {
    size: "md",
  }
);

const label = computed(() => {
  return props.tier === "pro" ? "Pro" : "Free";
});
</script>

<template>
  <span class="tier-badge" :class="[tier, size]">
    {{ label }}
  </span>
</template>

<style scoped>
.tier-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  text-transform: uppercase;
  border-radius: 4px;
}

/* Sizes */
.tier-badge.sm {
  padding: 0.125rem 0.375rem;
  font-size: 0.625rem;
}

.tier-badge.md {
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
}

.tier-badge.lg {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

/* Tier colors */
.tier-badge.free {
  background: var(--color-bg-secondary, #e5e7eb);
  color: var(--color-text-muted, #6b7280);
}

.tier-badge.pro {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}
</style>
