<script setup lang="ts">
/**
 * Auth Callback View
 *
 * Handles OAuth callback redirects from Supabase.
 * Extracts tokens from URL and redirects to intended destination.
 */

import { onMounted, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { supabase } from "@/auth/supabase";
import { useAuthStore } from "@/stores/useAuthStore";

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const status = ref<"processing" | "success" | "error">("processing");
const errorMessage = ref("");

onMounted(async () => {
  try {
    // Supabase handles the token extraction from URL hash automatically
    const { data, error } = await supabase.auth.getSession();

    if (error) {
      status.value = "error";
      errorMessage.value = error.message;
      return;
    }

    if (data.session) {
      // Session established, fetch profile
      await auth.fetchProfile();
      await auth.fetchTierInfo();

      status.value = "success";

      // Redirect to intended destination or home
      const redirect = (route.query.redirect as string) || "/";
      setTimeout(() => {
        router.push(redirect);
      }, 1000);
    } else {
      // No session found
      status.value = "error";
      errorMessage.value = "Authentication failed. Please try again.";
    }
  } catch (e) {
    status.value = "error";
    errorMessage.value = e instanceof Error ? e.message : "An error occurred";
  }
});
</script>

<template>
  <div class="callback-page">
    <div class="callback-card">
      <!-- Processing -->
      <template v-if="status === 'processing'">
        <div class="spinner" />
        <h2>Completing sign in...</h2>
        <p>Please wait while we verify your authentication.</p>
      </template>

      <!-- Success -->
      <template v-else-if="status === 'success'">
        <div class="success-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 6L9 17l-5-5" />
          </svg>
        </div>
        <h2>Welcome!</h2>
        <p>You've been signed in successfully. Redirecting...</p>
      </template>

      <!-- Error -->
      <template v-else>
        <div class="error-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="15" y1="9" x2="9" y2="15" />
            <line x1="9" y1="9" x2="15" y2="15" />
          </svg>
        </div>
        <h2>Sign In Failed</h2>
        <p>{{ errorMessage }}</p>
        <router-link to="/auth/login" class="btn-retry">
          Try Again
        </router-link>
      </template>
    </div>
  </div>
</template>

<style scoped>
.callback-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  padding: 1rem;
}

.callback-card {
  text-align: center;
  background: white;
  padding: 3rem;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  max-width: 400px;
  width: 100%;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-border, #ddd);
  border-top-color: var(--color-primary, #3b82f6);
  border-radius: 50%;
  margin: 0 auto 1.5rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.success-icon,
.error-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 1.5rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.success-icon {
  background: #d1fae5;
  color: #059669;
}

.error-icon {
  background: #fee2e2;
  color: #dc2626;
}

.success-icon svg,
.error-icon svg {
  width: 32px;
  height: 32px;
}

h2 {
  margin: 0 0 0.5rem;
  color: var(--color-text, #333);
}

p {
  margin: 0;
  color: var(--color-text-muted, #666);
}

.btn-retry {
  display: inline-block;
  margin-top: 1.5rem;
  padding: 0.75rem 1.5rem;
  background: var(--color-primary, #3b82f6);
  color: white;
  border-radius: 4px;
  text-decoration: none;
  font-weight: 500;
}

.btn-retry:hover {
  background: var(--color-primary-dark, #2563eb);
}
</style>
