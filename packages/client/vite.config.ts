import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  // Pre-bundle heavy deps that are only reached through lazy route chunks
  // (e.g. chart.js via the Calculators hub). Without this, the dev server
  // discovers them mid-session, re-runs optimizeDeps, and serves a transient
  // 504 "Outdated Optimize Dep" that breaks the first navigation to those
  // routes. Listing them here bundles them at startup instead.
  optimizeDeps: {
    include: ['chart.js', 'chart.js/auto'],
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8010',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8010',
        ws: true,
      }
    }
  }
})
