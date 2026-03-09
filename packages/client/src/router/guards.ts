/**
 * Router Navigation Guards
 *
 * Provides route guards for authentication and tier-based access control.
 */

import type { NavigationGuardNext, RouteLocationNormalized } from "vue-router";
import { useAuthStore } from "@/stores/useAuthStore";
import type { UserTier } from "@/auth/types";

/**
 * Guard that requires authentication.
 * Redirects to /auth/login if not authenticated.
 */
export async function requireAuth(
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const auth = useAuthStore();

  // Wait for auth to initialize
  if (!auth.initialized) {
    await auth.initialize();
  }

  if (!auth.isAuthenticated) {
    // Store intended destination for redirect after login
    const redirectTo = to.fullPath !== "/" ? to.fullPath : undefined;
    next({
      path: "/auth/login",
      query: redirectTo ? { redirect: redirectTo } : undefined,
    });
  } else {
    next();
  }
}

/**
 * Guard that requires guest (not authenticated).
 * Redirects to home if already authenticated.
 */
export async function requireGuest(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const auth = useAuthStore();

  if (!auth.initialized) {
    await auth.initialize();
  }

  if (auth.isAuthenticated) {
    next("/");
  } else {
    next();
  }
}

/**
 * Factory for tier-based guards.
 * Creates a guard that requires a minimum tier.
 *
 * @param minTier - Minimum tier required (e.g., "pro")
 */
export function requireTier(minTier: UserTier) {
  return async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ): Promise<void> => {
    const auth = useAuthStore();

    if (!auth.initialized) {
      await auth.initialize();
    }

    // First check authentication
    if (!auth.isAuthenticated) {
      next({
        path: "/auth/login",
        query: { redirect: to.fullPath },
      });
      return;
    }

    // Then check tier
    if (!auth.hasMinTier(minTier)) {
      // Redirect to upgrade page or show upgrade modal
      next({
        path: "/upgrade",
        query: {
          required: minTier,
          feature: to.meta.featureName as string | undefined,
        },
      });
      return;
    }

    next();
  };
}

/**
 * Factory for feature-based guards.
 * Creates a guard that requires access to a specific feature.
 *
 * @param featureKey - Feature key to check (e.g., "ai_vision")
 */
export function requireFeature(featureKey: string) {
  return async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ): Promise<void> => {
    const auth = useAuthStore();

    if (!auth.initialized) {
      await auth.initialize();
    }

    // First check authentication
    if (!auth.isAuthenticated) {
      next({
        path: "/auth/login",
        query: { redirect: to.fullPath },
      });
      return;
    }

    // Then check feature access
    if (!auth.canAccessFeature(featureKey)) {
      next({
        path: "/upgrade",
        query: { feature: featureKey },
      });
      return;
    }

    next();
  };
}

/**
 * Global before guard to initialize auth.
 * Use as router.beforeEach(initAuthGuard)
 */
export async function initAuthGuard(
  _to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext
): Promise<void> {
  const auth = useAuthStore();

  if (!auth.initialized) {
    await auth.initialize();
  }

  next();
}
