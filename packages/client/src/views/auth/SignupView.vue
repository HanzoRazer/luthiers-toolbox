<script setup lang="ts">
/**
 * Signup View
 *
 * Full-page signup layout.
 */

import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";
import { isSupabaseConfigured } from "@/auth/supabase";

const auth = useAuthStore();
const router = useRouter();

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const displayName = ref("");
const showPassword = ref(false);

const isConfigured = computed(() => isSupabaseConfigured());
const passwordsMatch = computed(() => password.value === confirmPassword.value);
const canSubmit = computed(
  () =>
    email.value.trim() &&
    password.value &&
    passwordsMatch.value &&
    password.value.length >= 6 &&
    !auth.loading
);

const successMessage = ref("");

async function handleSubmit() {
  if (!canSubmit.value) return;

  const success = await auth.signUp({
    email: email.value.trim(),
    password: password.value,
    display_name: displayName.value.trim() || undefined,
  });

  if (success) {
    successMessage.value =
      "Account created! Please check your email to confirm your account.";
    // Clear form
    email.value = "";
    password.value = "";
    confirmPassword.value = "";
    displayName.value = "";
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <h1>The Production Shop</h1>
        <p>Create your account</p>
      </div>

      <div class="signup-form">
        <!-- Not configured warning -->
        <div v-if="!isConfigured" class="warning-banner">
          Authentication is not configured. Set VITE_SUPABASE_URL and
          VITE_SUPABASE_ANON_KEY.
        </div>

        <!-- Success message -->
        <div v-if="successMessage" class="success-banner">
          {{ successMessage }}
          <router-link to="/auth/login">Go to login</router-link>
        </div>

        <!-- Error message -->
        <div v-if="auth.error" class="error-banner">
          {{ auth.error }}
        </div>

        <form v-if="!successMessage" @submit.prevent="handleSubmit">
          <div class="form-group">
            <label for="displayName">Display Name (optional)</label>
            <input
              id="displayName"
              v-model="displayName"
              type="text"
              placeholder="Your name"
              autocomplete="name"
            />
          </div>

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
                placeholder="At least 6 characters"
                autocomplete="new-password"
                required
                minlength="6"
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

          <div class="form-group">
            <label for="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              v-model="confirmPassword"
              :type="showPassword ? 'text' : 'password'"
              placeholder="Confirm your password"
              autocomplete="new-password"
              required
            />
            <span v-if="confirmPassword && !passwordsMatch" class="error-hint">
              Passwords do not match
            </span>
          </div>

          <button type="submit" class="btn-primary" :disabled="!canSubmit">
            <span v-if="auth.loading">Creating account...</span>
            <span v-else>Create Account</span>
          </button>
        </form>

        <p class="login-link">
          Already have an account?
          <router-link to="/auth/login">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f3f4f6, #e5e7eb);
  padding: 1rem;
}

.auth-container {
  width: 100%;
  max-width: 440px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.auth-header {
  text-align: center;
  padding: 2rem 2rem 1rem;
  background: linear-gradient(135deg, #1e3a5f, #2d4a6f);
  color: white;
}

.auth-header h1 {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
}

.auth-header p {
  margin: 0.5rem 0 0;
  opacity: 0.8;
  font-size: 0.875rem;
}

.signup-form {
  padding: 2rem;
}

.warning-banner,
.error-banner,
.success-banner {
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

.success-banner {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.success-banner a {
  color: #155724;
  font-weight: 500;
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

.error-hint {
  display: block;
  margin-top: 0.25rem;
  color: var(--color-danger, #dc2626);
  font-size: 0.75rem;
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

.login-link {
  text-align: center;
  margin-top: 1.5rem;
  color: var(--color-text-muted, #666);
  font-size: 0.875rem;
}

.login-link a {
  color: var(--color-primary, #3b82f6);
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
