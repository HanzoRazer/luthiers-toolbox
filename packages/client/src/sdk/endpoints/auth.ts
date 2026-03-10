/**
 * Auth SDK Endpoints
 *
 * SDK wrappers for authentication API calls.
 * Replaces raw fetch() in useAuthStore.
 */

import { sdkRequest } from "../http";
import type { UserProfile, TierInfo, ProfileUpdate } from "@/auth/types";

/**
 * Fetch current user profile.
 *
 * @param token - Bearer token from Supabase
 * @returns User profile or null if not authenticated
 */
export async function getProfile(token: string): Promise<UserProfile | null> {
  const resp = await sdkRequest("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return resp.json();
}

/**
 * Fetch tier info for current user.
 *
 * @param token - Bearer token from Supabase
 * @returns Tier info or null if not authenticated
 */
export async function getTierInfo(token: string): Promise<TierInfo | null> {
  const resp = await sdkRequest("/api/auth/tier", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  return resp.json();
}

/**
 * Update user profile.
 *
 * @param token - Bearer token from Supabase
 * @param updates - Profile fields to update
 * @returns Updated user profile
 */
export async function updateProfile(
  token: string,
  updates: ProfileUpdate
): Promise<UserProfile> {
  const resp = await sdkRequest("/api/auth/me", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(updates),
  });

  return resp.json();
}
