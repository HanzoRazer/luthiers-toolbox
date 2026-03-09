<script setup lang="ts">
/**
 * Upgrade Prompt Component
 *
 * Modal/banner prompting users to upgrade to Pro tier.
 */

import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";

const props = defineProps<{
  feature?: string;
  featureName?: string;
  inline?: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
}>();

const auth = useAuthStore();
const router = useRouter();

const displayFeature = computed(() => {
  if (props.featureName) return props.featureName;
  if (!props.feature) return "this feature";

  // Try to find the feature in tier info
  const feat = auth.tierInfo?.features.find(
    (f) => f.feature_key === props.feature
  );
  return feat?.display_name ?? props.feature.replace(/_/g, " ");
});

function goToUpgrade() {
  emit("close");
  router.push({
    path: "/upgrade",
    query: props.feature ? { feature: props.feature } : undefined,
  });
}

function handleClose() {
  emit("close");
}
</script>

<template>
  <div class="upgrade-prompt" :class="{ inline }">
    <div class="prompt-content">
      <div class="prompt-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z" />
        </svg>
      </div>

      <div class="prompt-text">
        <h3>Upgrade to Pro</h3>
        <p>
          <strong>{{ displayFeature }}</strong> requires a Pro subscription.
          Unlock all premium features today!
        </p>
      </div>

      <div class="prompt-actions">
        <button class="btn-upgrade" @click="goToUpgrade">
          Upgrade Now
        </button>
        <button v-if="!inline" class="btn-close" @click="handleClose">
          Maybe Later
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upgrade-prompt {
  background: linear-gradient(135deg, #fef3c7, #fde68a);
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 1.5rem;
}

.upgrade-prompt.inline {
  padding: 1rem;
}

.prompt-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.prompt-icon {
  width: 48px;
  height: 48px;
  color: #d97706;
}

.prompt-icon svg {
  width: 100%;
  height: 100%;
}

.prompt-text h3 {
  margin: 0;
  color: #92400e;
  font-size: 1.25rem;
}

.prompt-text p {
  margin: 0.5rem 0 0;
  color: #78350f;
  font-size: 0.875rem;
}

.prompt-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.btn-upgrade {
  padding: 0.625rem 1.25rem;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  cursor: pointer;
}

.btn-upgrade:hover {
  background: linear-gradient(135deg, #d97706, #b45309);
}

.btn-close {
  padding: 0.625rem 1.25rem;
  background: transparent;
  color: #92400e;
  border: 1px solid #d97706;
  border-radius: 4px;
  cursor: pointer;
}

.btn-close:hover {
  background: rgba(217, 119, 6, 0.1);
}
</style>
