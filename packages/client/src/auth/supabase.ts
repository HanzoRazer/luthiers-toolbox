/**
 * Supabase Client Singleton
 *
 * Creates and exports a single Supabase client instance for the entire app.
 * Handles authentication, session management, and real-time subscriptions.
 *
 * Environment Variables:
 * - VITE_SUPABASE_URL: Supabase project URL
 * - VITE_SUPABASE_ANON_KEY: Supabase anonymous key (public)
 */

import { createClient, SupabaseClient } from "@supabase/supabase-js";

// Environment variables
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY as string;

// Validate configuration
if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
  console.warn(
    "[auth] Supabase not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY."
  );
}

/**
 * Supabase client singleton.
 *
 * Features:
 * - Auto token refresh
 * - Persistent sessions (localStorage)
 * - Real-time subscriptions ready
 */
export const supabase: SupabaseClient = createClient(
  SUPABASE_URL || "https://placeholder.supabase.co",
  SUPABASE_ANON_KEY || "placeholder-key",
  {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true, // Handle OAuth callbacks
    },
  }
);

/**
 * Check if Supabase is properly configured.
 */
export function isSupabaseConfigured(): boolean {
  return Boolean(SUPABASE_URL && SUPABASE_ANON_KEY);
}

/**
 * Get the current access token (for API calls).
 * Returns null if not authenticated.
 */
export async function getAccessToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export default supabase;
