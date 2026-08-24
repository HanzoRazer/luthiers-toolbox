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
  // Pre-bundle deps that are only reached through lazy route chunks. Vite's
  // optimizer discovers an import when the module graph first reaches it, so
  // chart.js is found mid-session, optimizeDeps re-runs, and the dev server
  // serves a transient 504 "Outdated Optimize Dep" that blanks the first
  // navigation to a chart-bearing route (reported on /calculators). Listing it
  // here bundles it at startup instead.
  //
  // chart.js is reached from three places, not just the calculators hub:
  // src/tools/audio_analyzer/renderers/**, src/views/calculators/acoustics/
  // SoundholeCalculator.vue, and src/views/multi_run_comparison/**. Keep this
  // entry as long as any of them import it lazily.
  //
  // Only the bare specifier is listed: every chart.js import in src/ resolves
  // 'chart.js'. Nothing imports the 'chart.js/auto' subpath, so including it
  // would pre-bundle a module the app never loads.
  optimizeDeps: {
    include: ['chart.js'],
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
