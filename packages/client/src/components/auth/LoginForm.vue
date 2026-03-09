<script setup lang="ts">
/**
 * Login Form Component
 *
 * Email/password login with OAuth options.
 */

import { ref, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";
import { isSupabaseConfigured } from "@/auth/supabase";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();

const email = ref("");
const password = ref("");
const showPassword = ref(false);

const isConfigured = computed(() => isSupabaseConfigured());
const canSubmit = computed(
  () => email.value.trim() && password.value && !auth.loading
);

async function handleSubmit() {
  if (!canSubmit.value) return;

  const success = await auth.signIn({
    email: email.value.trim(),
    password: password.value,
  });

  if (success) {
    const redirect = (route.query.redirect as string) || "/";
    router.push(redirect);
  }
}

async function handleOAuth(provider: "google" | "github") {
  await auth.signInWithOAuth(provider);
}
</script>

<template>
  <div class="login-form">
    <h2>Sign In</h2>

    <!-- Not configured warning -->
    <div v-if="!isConfigured" class="warning-banner">
      Authentication is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.
    </div>

    <!-- Error message -->
    <div v-if="auth.error" class="error-banner">
      {{ auth.error }}
    </div>

    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="email"
          type="email"
          placeholder="you@example.com"
          autocomplete="email"
          required
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <div class="password-input">
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="Your password"
            autocomplete="current-password"
            required
          />
          <button
            type="button"
            class="toggle-password"
            @click="showPassword = !showPassword"
          >
            {{ showPassword ? "Hide" : "Show" }}
          </button>
        </div>
      </div>

      <button type="submit" class="btn-primary" :disabled="!canSubmit">
        <span v-if="auth.loading">Signing in...</span>
        <span v-else>Sign In</span>
      </button>
    </form>

    <div class="divider">
      <span>or continue with</span>
    </div>

    <div class="oauth-buttons">
      <button
        type="button"
        class="btn-oauth"
        @click="handleOAuth('google')"
        :disabled="auth.loading"
      >
        Google
      </button>
      <button
        type="button"
        class="btn-oauth"
        @click="handleOAuth('github')"
        :disabled="auth.loading"
      >
        GitHub
      </button>
    </div>

    <p class="signup-link">
      Don't have an account?
      <router-link to="/auth/signup">Sign up</router-link>
    </p>
  </div>
</template>

<style scoped>
.login-form {
  max-width: 400px;
  margin: 0 auto;
  padding: 2rem;
}

h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: var(--color-text, #333);
}

.warning-banner,
.error-banner {
  padding: 0.75rem 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-size: 0.875rem;
}

.warning-banner {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffc107;
}

.error-banner {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
  color: var(--color-text, #333);
}

.form-group input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  font-size: 1rem;
}

.password-input {
  display: flex;
  gap: 0.5rem;
}

.password-input input {
  flex: 1;
}

.toggle-password {
  padding: 0.5rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  background: var(--color-bg-secondary, #f5f5f5);
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-primary {
  width: 100%;
  padding: 0.75rem;
  background: var(--color-primary, #3b82f6);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 0.5rem;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark, #2563eb);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
  color: var(--color-text-muted, #666);
  font-size: 0.875rem;
}

.divider::before,
.divider::after {
  content: "";
  flex: 1;
  height: 1px;
  background: var(--color-border, #ddd);
}

.divider span {
  padding: 0 1rem;
}

.oauth-buttons {
  display: flex;
  gap: 0.75rem;
}

.btn-oauth {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 4px;
  background: white;
  font-size: 0.875rem;
  cursor: pointer;
}

.btn-oauth:hover:not(:disabled) {
  background: var(--color-bg-secondary, #f5f5f5);
}

.btn-oauth:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.signup-link {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--color-text-muted, #666);
  font-size: 0.875rem;
}

.signup-link a {
  color: var(--color-primary, #3b82f6);
  text-decoration: none;
}

.signup-link a:hover {
  text-decoration: underline;
}
</style>
