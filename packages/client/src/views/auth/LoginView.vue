<script setup lang="ts">
/**
 * Login View
 *
 * Full-page login layout with branding.
 */
import LoginForm from "@/components/auth/LoginForm.vue";
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <h1>The Production Shop</h1>
        <p>Sign in to access your workshop</p>
      </div>

      <LoginForm />
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
</style>
