/**
 * Auth Store (Pinia)
 *
 * Manages authentication state, user profile, and tier information.
 *
 * Features:
 * - Supabase auth integration
 * - Auto session refresh
 * - Tier-based feature checking
 * - Profile management
 */

import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { supabase, isSupabaseConfigured, getAccessToken } from "@/auth/supabase";
import type {
  UserProfile,
  TierInfo,
  UserTier,
  SignInCredentials,
  SignUpCredentials,
  ProfileUpdate,
} from "@/auth/types";

export const useAuthStore = defineStore("auth", () => {
  // ==========================================================================
  // State
  // ==========================================================================

  const user = ref<UserProfile | null>(null);
  const tierInfo = ref<TierInfo | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  const initialized = ref(false);

  // ==========================================================================
  // Getters
  // ==========================================================================

  const isAuthenticated = computed(() => user.value !== null);

  const currentTier = computed<UserTier>(() => user.value?.tier ?? "free");

  const isPro = computed(() => currentTier.value === "pro");

  const accessToken = computed(() => getAccessToken());

  const displayName = computed(
    () => user.value?.display_name ?? user.value?.email ?? "Guest"
  );

  const avatarUrl = computed(() => user.value?.avatar_url ?? null);

  // ==========================================================================
  // Actions
  // ==========================================================================

  /**
   * Initialize auth state from Supabase session.
   * Call this on app mount.
   */
  async function initialize(): Promise<void> {
    if (initialized.value) return;
    if (!isSupabaseConfigured()) {
      initialized.value = true;
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      // Get current session
      const { data: sessionData } = await supabase.auth.getSession();

      if (sessionData.session) {
        // Fetch user profile from backend
        await fetchProfile();
        await fetchTierInfo();
      }

      // Listen for auth state changes
      supabase.auth.onAuthStateChange(async (event, session) => {
        if (event === "SIGNED_IN" && session) {
          await fetchProfile();
          await fetchTierInfo();
        } else if (event === "SIGNED_OUT") {
          user.value = null;
          tierInfo.value = null;
        } else if (event === "TOKEN_REFRESHED" && session) {
          // Token refreshed, profile stays the same
        }
      });
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Failed to initialize auth";
      console.error("[auth] Initialize failed:", e);
    } finally {
      loading.value = false;
      initialized.value = true;
    }
  }

  /**
   * Sign in with email and password.
   */
  async function signIn(credentials: SignInCredentials): Promise<boolean> {
    loading.value = true;
    error.value = null;

    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email: credentials.email,
        password: credentials.password,
      });

      if (authError) {
        error.value = authError.message;
        return false;
      }

      await fetchProfile();
      await fetchTierInfo();
      return true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Sign in failed";
      return false;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Sign up with email and password.
   */
  async function signUp(credentials: SignUpCredentials): Promise<boolean> {
    loading.value = true;
    error.value = null;

    try {
      const { error: authError } = await supabase.auth.signUp({
        email: credentials.email,
        password: credentials.password,
        options: {
          data: {
            display_name: credentials.display_name,
          },
        },
      });

      if (authError) {
        error.value = authError.message;
        return false;
      }

      // Note: User may need to confirm email before signing in
      return true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Sign up failed";
      return false;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Sign out current user.
   */
  async function signOut(): Promise<void> {
    loading.value = true;

    try {
      await supabase.auth.signOut();
      user.value = null;
      tierInfo.value = null;
    } catch (e) {
      console.error("[auth] Sign out failed:", e);
    } finally {
      loading.value = false;
    }
  }

  /**
   * Sign in with OAuth provider.
   */
  async function signInWithOAuth(
    provider: "google" | "github"
  ): Promise<boolean> {
    loading.value = true;
    error.value = null;

    try {
      const { error: authError } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });

      if (authError) {
        error.value = authError.message;
        return false;
      }

      return true;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "OAuth sign in failed";
      return false;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Fetch user profile from backend.
   */
  async function fetchProfile(): Promise<void> {
    const token = await getAccessToken();
    if (!token) return;

    try {
      const res = await fetch("/api/auth/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        user.value = await res.json();
      }
    } catch (e) {
      console.error("[auth] Failed to fetch profile:", e);
    }
  }

  /**
   * Fetch tier info from backend.
   */
  async function fetchTierInfo(): Promise<void> {
    const token = await getAccessToken();
    if (!token) return;

    try {
      const res = await fetch("/api/auth/tier", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (res.ok) {
        tierInfo.value = await res.json();
      }
    } catch (e) {
      console.error("[auth] Failed to fetch tier info:", e);
    }
  }

  /**
   * Update user profile.
   */
  async function updateProfile(updates: ProfileUpdate): Promise<boolean> {
    const token = await getAccessToken();
    if (!token) return false;

    loading.value = true;
    error.value = null;

    try {
      const res = await fetch("/api/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });

      if (res.ok) {
        user.value = await res.json();
        return true;
      }

      const data = await res.json();
      error.value = data.detail ?? "Failed to update profile";
      return false;
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Update failed";
      return false;
    } finally {
      loading.value = false;
    }
  }

  /**
   * Check if a feature is available for current user.
   */
  function canAccessFeature(featureKey: string): boolean {
    if (!tierInfo.value) return false;

    const feature = tierInfo.value.features.find(
      (f) => f.feature_key === featureKey
    );

    return feature?.available ?? false;
  }

  /**
   * Check if user has at least the specified tier.
   */
  function hasMinTier(minTier: UserTier): boolean {
    const tierLevels: Record<UserTier, number> = { free: 0, pro: 1 };
    return tierLevels[currentTier.value] >= tierLevels[minTier];
  }

  // ==========================================================================
  // Return
  // ==========================================================================

  return {
    // State
    user,
    tierInfo,
    loading,
    error,
    initialized,

    // Getters
    isAuthenticated,
    currentTier,
    isPro,
    accessToken,
    displayName,
    avatarUrl,

    // Actions
    initialize,
    signIn,
    signUp,
    signOut,
    signInWithOAuth,
    fetchProfile,
    fetchTierInfo,
    updateProfile,
    canAccessFeature,
    hasMinTier,
  };
});
