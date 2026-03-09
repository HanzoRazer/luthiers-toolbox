/**
 * Auth Types
 *
 * Type definitions for authentication and user management.
 */

/**
 * User subscription tier.
 */
export type UserTier = "free" | "pro";

/**
 * User profile from backend.
 */
export interface UserProfile {
  id: string;
  email: string | null;
  display_name: string | null;
  avatar_url: string | null;
  tier: UserTier;
  tier_expires_at: string | null;
  preferences: Record<string, unknown>;
}

/**
 * Feature information from tier endpoint.
 */
export interface FeatureInfo {
  feature_key: string;
  display_name: string;
  description: string | null;
  available: boolean;
}

/**
 * Tier info response from /api/auth/tier.
 */
export interface TierInfo {
  current_tier: UserTier;
  tier_expires_at: string | null;
  features: FeatureInfo[];
}

/**
 * Auth store state.
 */
export interface AuthState {
  user: UserProfile | null;
  tierInfo: TierInfo | null;
  loading: boolean;
  error: string | null;
  initialized: boolean;
}

/**
 * Sign in credentials.
 */
export interface SignInCredentials {
  email: string;
  password: string;
}

/**
 * Sign up credentials.
 */
export interface SignUpCredentials {
  email: string;
  password: string;
  display_name?: string;
}

/**
 * Profile update request.
 */
export interface ProfileUpdate {
  display_name?: string;
  avatar_url?: string;
  preferences?: Record<string, unknown>;
}
