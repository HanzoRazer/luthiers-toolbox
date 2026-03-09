<script setup lang="ts">
/**
 * Upgrade View
 *
 * Page showing Pro tier benefits and upgrade options.
 */

import { computed } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";
import TierBadge from "@/components/auth/TierBadge.vue";

const auth = useAuthStore();
const route = useRoute();

const requestedFeature = computed(() => route.query.feature as string | undefined);

const proFeatures = [
  {
    icon: "🤖",
    title: "AI Vision Analysis",
    description: "AI-powered wood grading and defect detection",
  },
  {
    icon: "⚡",
    title: "Batch Processing",
    description: "Process multiple files simultaneously",
  },
  {
    icon: "🔧",
    title: "Advanced CAM",
    description: "Advanced toolpath strategies and optimization",
  },
  {
    icon: "📐",
    title: "Custom Post Processors",
    description: "Create and customize post processors",
  },
  {
    icon: "📊",
    title: "Advanced Analytics",
    description: "Deep insights into your production data",
  },
  {
    icon: "💾",
    title: "Cloud Storage",
    description: "Secure cloud backup for all your projects",
  },
];
</script>

<template>
  <div class="upgrade-page">
    <div class="upgrade-container">
      <!-- Header -->
      <div class="upgrade-header">
        <h1>Upgrade to Pro</h1>
        <p v-if="requestedFeature">
          The feature you requested requires a Pro subscription.
        </p>
        <p v-else>
          Unlock the full power of The Production Shop
        </p>
      </div>

      <!-- Current tier -->
      <div v-if="auth.isAuthenticated" class="current-tier">
        <span>Current tier:</span>
        <TierBadge :tier="auth.currentTier" size="md" />
      </div>

      <!-- Features grid -->
      <div class="features-grid">
        <div
          v-for="feature in proFeatures"
          :key="feature.title"
          class="feature-card"
        >
          <span class="feature-icon">{{ feature.icon }}</span>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </div>
      </div>

      <!-- Pricing -->
      <div class="pricing-section">
        <div class="price-card">
          <div class="price-header">
            <TierBadge tier="pro" size="lg" />
            <div class="price">
              <span class="amount">$19</span>
              <span class="period">/month</span>
            </div>
          </div>
          <ul class="price-features">
            <li>All Free tier features</li>
            <li>AI Vision Analysis</li>
            <li>Batch Processing</li>
            <li>Advanced CAM Features</li>
            <li>Custom Post Processors</li>
            <li>Priority Support</li>
          </ul>
          <button class="btn-upgrade">
            Upgrade Now
          </button>
          <p class="price-note">
            14-day free trial. Cancel anytime.
          </p>
        </div>
      </div>

      <!-- Back link -->
      <div class="back-link">
        <router-link to="/">Back to Dashboard</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upgrade-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  padding: 2rem 1rem;
}

.upgrade-container {
  max-width: 800px;
  margin: 0 auto;
}

.upgrade-header {
  text-align: center;
  margin-bottom: 2rem;
}

.upgrade-header h1 {
  margin: 0;
  font-size: 2rem;
  color: var(--color-text, #333);
}

.upgrade-header p {
  margin: 0.5rem 0 0;
  color: var(--color-text-muted, #666);
}

.current-tier {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 2rem;
  color: var(--color-text-muted, #666);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.feature-card {
  background: white;
  padding: 1.25rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.feature-card h3 {
  margin: 0 0 0.25rem;
  font-size: 1rem;
  color: var(--color-text, #333);
}

.feature-card p {
  margin: 0;
  font-size: 0.875rem;
  color: var(--color-text-muted, #666);
}

.pricing-section {
  display: flex;
  justify-content: center;
}

.price-card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  text-align: center;
  max-width: 320px;
  width: 100%;
}

.price-header {
  margin-bottom: 1.5rem;
}

.price {
  margin-top: 1rem;
}

.price .amount {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-text, #333);
}

.price .period {
  font-size: 1rem;
  color: var(--color-text-muted, #666);
}

.price-features {
  list-style: none;
  padding: 0;
  margin: 0 0 1.5rem;
  text-align: left;
}

.price-features li {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--color-border, #eee);
  color: var(--color-text, #333);
}

.price-features li::before {
  content: "✓ ";
  color: #059669;
}

.btn-upgrade {
  width: 100%;
  padding: 1rem;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-upgrade:hover {
  background: linear-gradient(135deg, #d97706, #b45309);
}

.price-note {
  margin: 1rem 0 0;
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
}

.back-link {
  text-align: center;
  margin-top: 2rem;
}

.back-link a {
  color: var(--color-primary, #3b82f6);
  text-decoration: none;
}

.back-link a:hover {
  text-decoration: underline;
}
</style>
