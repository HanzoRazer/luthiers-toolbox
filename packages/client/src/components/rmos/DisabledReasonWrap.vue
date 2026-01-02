<template>
  <span class="disabled-reason-wrap" :title="reason">
    <slot />
  </span>
</template>

<script setup lang="ts">
/**
 * DisabledReasonWrap.vue
 * Bundle 10: Wrapper for disabled controls that shows hover tooltip
 *
 * Native title attribute won't fire reliably on disabled buttons,
 * so this wrapper provides hover capability via the parent container.
 */
defineProps<{
  reason: string;
}>();
</script>

<style scoped>
.disabled-reason-wrap {
  display: inline-flex;
  align-items: center;
}
</style>
