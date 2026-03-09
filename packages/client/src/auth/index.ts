/**
 * Auth Module Index
 *
 * Export all auth-related utilities and types.
 */

export { supabase, isSupabaseConfigured, getAccessToken } from "./supabase";
export type {
  UserTier,
  UserProfile,
  FeatureInfo,
  TierInfo,
  AuthState,
  SignInCredentials,
  SignUpCredentials,
  ProfileUpdate,
} from "./types";
