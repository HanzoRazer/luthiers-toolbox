<script setup lang="ts">
/**
 * User Menu Component
 *
 * Dropdown menu showing user info, tier badge, and logout.
 */

import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";

const auth = useAuthStore();
const router = useRouter();

const isOpen = ref(false);

const initials = computed(() => {
  const name = auth.displayName;
  if (!name) return "?";
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
});

function toggle() {
  isOpen.value = !isOpen.value;
}

function close() {
  isOpen.value = false;
}

async function handleSignOut() {
  close();
  await auth.signOut();
  router.push("/");
}

function goToProfile() {
  close();
  router.push("/settings/profile");
}

function goToUpgrade() {
  close();
  router.push("/upgrade");
}
</script>

<template>
  <div class="user-menu" v-if="auth.isAuthenticated">
    <button class="user-button" @click="toggle" :title="auth.displayName">
      <img
        v-if="auth.avatarUrl"
        :src="auth.avatarUrl"
        :alt="auth.displayName"
        class="avatar"
      />
      <span v-else class="avatar-initials">{{ initials }}</span>
      <span class="tier-badge" :class="auth.currentTier">
        {{ auth.currentTier }}
      </span>
    </button>

    <div v-if="isOpen" class="dropdown" @click.stop>
      <div class="dropdown-header">
        <strong>{{ auth.displayName }}</strong>
        <span class="email">{{ auth.user?.email }}</span>
      </div>

      <div class="dropdown-divider" />

      <button class="dropdown-item" @click="goToProfile">
        Profile Settings
      </button>

      <button v-if="!auth.isPro" class="dropdown-item upgrade" @click="goToUpgrade">
        Upgrade to Pro
      </button>

      <div class="dropdown-divider" />

      <button class="dropdown-item signout" @click="handleSignOut">
        Sign Out
      </button>
    </div>

    <!-- Backdrop to close menu when clicking outside -->
    <div v-if="isOpen" class="backdrop" @click="close" />
  </div>

  <!-- Login button when not authenticated -->
  <router-link v-else to="/auth/login" class="login-button">
    Sign In
  </router-link>
</template>

<style scoped>
.user-menu {
  position: relative;
}

.user-button {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
}

.user-button:hover {
  background: var(--color-bg-secondary, #f5f5f5);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.avatar-initials {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary, #3b82f6);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
}

.tier-badge {
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
}

.tier-badge.free {
  background: var(--color-bg-secondary, #e5e7eb);
  color: var(--color-text-muted, #6b7280);
}

.tier-badge.pro {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  min-width: 200px;
  background: white;
  border: 1px solid var(--color-border, #ddd);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

.dropdown-header {
  padding: 0.75rem 1rem;
}

.dropdown-header strong {
  display: block;
  color: var(--color-text, #333);
}

.dropdown-header .email {
  font-size: 0.75rem;
  color: var(--color-text-muted, #666);
}

.dropdown-divider {
  height: 1px;
  background: var(--color-border, #ddd);
}

.dropdown-item {
  display: block;
  width: 100%;
  padding: 0.625rem 1rem;
  border: none;
  background: transparent;
  text-align: left;
  cursor: pointer;
  font-size: 0.875rem;
  color: var(--color-text, #333);
}

.dropdown-item:hover {
  background: var(--color-bg-secondary, #f5f5f5);
}

.dropdown-item.upgrade {
  color: var(--color-warning, #d97706);
  font-weight: 500;
}

.dropdown-item.signout {
  color: var(--color-danger, #dc2626);
}

.backdrop {
  position: fixed;
  inset: 0;
  z-index: 50;
}

.login-button {
  padding: 0.5rem 1rem;
  background: var(--color-primary, #3b82f6);
  color: white;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
}

.login-button:hover {
  background: var(--color-primary-dark, #2563eb);
}
</style>
