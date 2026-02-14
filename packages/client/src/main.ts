// packages/client/src/main.ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

// =============================================================================
// GLOBAL FETCH INTERCEPTOR
// Automatically prepends VITE_API_BASE to all /api/* requests
// This fixes cross-origin deployment (client + API on separate domains)
// =============================================================================
const API_BASE = import.meta.env.VITE_API_BASE || '';

if (API_BASE) {
  const originalFetch = window.fetch;
  window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    // Convert input to string URL
    let url: string;
    if (typeof input === 'string') {
      url = input;
    } else if (input instanceof URL) {
      url = input.href;
    } else if (input instanceof Request) {
      url = input.url;
    } else {
      url = String(input);
    }

    // Rewrite /api/* URLs to use API_BASE
    if (url.startsWith('/api/') || url.startsWith('/api?')) {
      const newUrl = `${API_BASE}${url}`;
      // console.debug('[fetch-interceptor]', url, '→', newUrl);
      if (typeof input === 'string') {
        return originalFetch.call(this, newUrl, init);
      } else if (input instanceof Request) {
        return originalFetch.call(this, new Request(newUrl, input), init);
      } else {
        return originalFetch.call(this, newUrl, init);
      }
    }

    return originalFetch.call(this, input, init);
  };
  console.info('[fetch-interceptor] Active: API calls will be routed to', API_BASE);
}

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.mount('#app')
