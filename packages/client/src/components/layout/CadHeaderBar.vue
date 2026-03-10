<script setup lang="ts">
/**
 * CadHeaderBar.vue
 *
 * Top header bar for CAD layout with breadcrumb, title, and actions.
 */

import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";

const props = withDefaults(
  defineProps<{
    title?: string;
    showBreadcrumb?: boolean;
    showUserMenu?: boolean;
  }>(),
  {
    title: "",
    showBreadcrumb: true,
    showUserMenu: true,
  }
);

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

// Build breadcrumb from route
const breadcrumbs = computed(() => {
  const crumbs: { label: string; path: string }[] = [
    { label: "Home", path: "/" },
  ];

  if (route.path !== "/") {
    const segments = route.path.split("/").filter(Boolean);
    let path = "";
    for (const segment of segments) {
      path += `/${segment}`;
      crumbs.push({
        label: segment.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        path,
      });
    }
  }

  return crumbs;
});

const displayTitle = computed(() => {
  if (props.title) return props.title;
  if (route.meta?.title) return route.meta.title as string;
  return breadcrumbs.value[breadcrumbs.value.length - 1]?.label || "Untitled";
});

function navigateTo(path: string) {
  router.push(path);
}

function handleLogout() {
  auth.signOut();
  router.push("/auth/login");
}
</script>

<template>
  <div class="cad-header-bar">
    <!-- Left: Breadcrumb -->
    <div class="header-left">
      <nav v-if="showBreadcrumb" class="breadcrumb">
        <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
          <span
            class="crumb"
            :class="{ active: index === breadcrumbs.length - 1 }"
            @click="index < breadcrumbs.length - 1 && navigateTo(crumb.path)"
          >
            {{ crumb.label }}
          </span>
          <span v-if="index < breadcrumbs.length - 1" class="separator">/</span>
        </template>
      </nav>
      <h1 v-else class="header-title">{{ displayTitle }}</h1>
    </div>

    <!-- Center: Actions Slot -->
    <div class="header-center">
      <slot name="actions">
        <!-- View-specific actions go here -->
      </slot>
    </div>

    <!-- Right: User Menu -->
    <div class="header-right">
      <slot name="right">
        <template v-if="showUserMenu && auth.isAuthenticated">
          <span class="user-name">{{ auth.displayName }}</span>
          <button class="btn-icon" title="Settings">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3"/>
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
          </button>
          <button class="btn-icon" title="Logout" @click="handleLogout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/>
            </svg>
          </button>
        </template>
        <template v-else-if="showUserMenu">
          <button class="btn-text" @click="navigateTo('/auth/login')">Sign In</button>
        </template>
      </slot>
    </div>
  </div>
</template>

<style scoped>
.cad-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 16px;
  gap: 16px;
}

.header-left {
  flex: 1;
  min-width: 0;
}

.header-center {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}

.crumb {
  color: var(--color-text-secondary, #a0a0a0);
  cursor: pointer;
  transition: color 0.15s;
}

.crumb:hover:not(.active) {
  color: var(--color-accent, #4a9eff);
}

.crumb.active {
  color: var(--color-text-primary, #e0e0e0);
  cursor: default;
  font-weight: 500;
}

.separator {
  color: var(--color-text-muted, #707070);
}

.header-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary, #e0e0e0);
}

.user-name {
  font-size: 13px;
  color: var(--color-text-secondary, #a0a0a0);
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-secondary, #a0a0a0);
  cursor: pointer;
  transition: all 0.15s;
}

.btn-icon:hover {
  background: var(--color-bg-panel-elevated, #2d2d2d);
  color: var(--color-text-primary, #e0e0e0);
}

.btn-text {
  padding: 6px 12px;
  border: 1px solid var(--color-border-panel, #3a3a3a);
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-primary, #e0e0e0);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-text:hover {
  background: var(--color-accent, #4a9eff);
  border-color: var(--color-accent, #4a9eff);
}
</style>
