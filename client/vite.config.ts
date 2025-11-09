/**
 * Vite Build Configuration - Luthier's Tool Box Client
 * 
 * CRITICAL SAFETY RULES:
 * 1. API proxy MUST point to correct backend port (8000)
 * 2. Sourcemaps MUST be enabled for debugging production issues
 * 3. Path aliases MUST be consistent with tsconfig.json
 * 4. Port MUST match documentation (5173 for dev)
 * 5. Build output MUST be 'dist' for Docker integration
 * 
 * This configuration sets up:
 * - Vue 3 plugin with SFC support
 * - TypeScript path aliasing (@/...)
 * - Dev server with API proxy to FastAPI backend
 * - Production build with sourcemaps
 * 
 * Development: npm run dev → http://localhost:5173
 * Production: npm run build → dist/
 */

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// =============================================================================
// CONFIGURATION CONSTANTS
// =============================================================================

/** Development server port (MUST match documentation) */
const DEV_PORT = 5173

/** FastAPI backend URL for API proxying */
const API_TARGET = 'http://localhost:8000'

/** Build output directory (MUST match Docker COPY path) */
const BUILD_DIR = 'dist'

// =============================================================================
// VITE CONFIGURATION
// =============================================================================

/**
 * Vite configuration for Vue 3 + TypeScript client.
 * 
 * Features:
 * - Vue 3 SFC support with <script setup>
 * - TypeScript path aliasing (@/ → ./src/)
 * - Dev server with hot module replacement
 * - API proxy to FastAPI backend (/api → :8000)
 * - Production build with sourcemaps enabled
 * 
 * Documentation:
 * - https://vitejs.dev/config/
 * - https://github.com/vitejs/vite-plugin-vue
 */
export default defineConfig({
  /**
   * Plugins array (order matters for certain plugins).
   * 
   * - vue(): Enables Vue 3 SFC support with <script setup> syntax
   */
  plugins: [vue()],

  /**
   * Module resolution configuration.
   * 
   * Alias Mapping:
   * - '@' → './src/' (TypeScript imports like @/components/...)
   * 
   * Notes:
   * - MUST match tsconfig.json paths for IDE support
   * - Resolves to absolute path using __dirname
   */
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  /**
   * Development server configuration.
   * 
   * Server Settings:
   * - port: 5173 (standard Vite dev port)
   * - proxy: /api → http://localhost:8000 (FastAPI backend)
   * 
   * Proxy Behavior:
   * - changeOrigin: true (rewrites Host header for backend)
   * - All /api/* requests forwarded to FastAPI
   * - WebSocket support for hot module replacement
   * 
   * Example Requests:
   * - http://localhost:5173/api/health → http://localhost:8000/api/health
   * - http://localhost:5173/api/cam/pocket/adaptive/plan → http://localhost:8000/api/cam/pocket/adaptive/plan
   */
  server: {
    port: DEV_PORT,
    proxy: {
      '/api': {
        target: API_TARGET,
        changeOrigin: true,  // CRITICAL: Rewrites Host header
      },
    },
  },

  /**
   * Production build configuration.
   * 
   * Build Settings:
   * - outDir: 'dist' (output directory for static files)
   * - sourcemap: true (CRITICAL for debugging production issues)
   * 
   * Output Structure:
   * - dist/index.html (entry point)
   * - dist/assets/*.js (chunked JS with hashes)
   * - dist/assets/*.css (extracted CSS)
   * - dist/assets/*.js.map (sourcemaps)
   * 
   * Docker Integration:
   * - Nginx serves static files from dist/
   * - COPY --from=client-builder /app/dist /usr/share/nginx/html
   */
  build: {
    outDir: BUILD_DIR,
    sourcemap: true,  // CRITICAL: Enable for production debugging
  },
})
