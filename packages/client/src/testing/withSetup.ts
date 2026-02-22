/**
 * withSetup - Test utility for composables that need Vue context.
 *
 * Solves the "inject() can only be used inside setup()" warning by
 * wrapping composables in a minimal Vue component context.
 *
 * Usage:
 *   import { withSetup } from '@/testing/withSetup'
 *
 *   it('computes correctly', async () => {
 *     const { result, app } = withSetup(() => useMyComposable(config, deps))
 *
 *     expect(result.someRef.value).toBe(expected)
 *
 *     // Trigger reactive updates
 *     result.someRef.value = 'new value'
 *     await nextTick()
 *
 *     // Cleanup (important for onMounted/onUnmounted hooks)
 *     app.unmount()
 *   })
 *
 * With router mocking:
 *   const { result } = withSetup(
 *     () => useMyComposable(),
 *     {
 *       route: { query: { preset: 'ai-extracted' } }
 *     }
 *   )
 */

import { createApp, defineComponent, h, type App } from 'vue'

export interface SetupOptions {
  /**
   * Mock route object for composables that use useRoute()
   */
  route?: {
    query?: Record<string, string | string[]>
    params?: Record<string, string>
    path?: string
    name?: string
    meta?: Record<string, unknown>
  }

  /**
   * Additional provide/inject values
   */
  provide?: Record<string | symbol, unknown>
}

export interface SetupResult<T> {
  /**
   * The return value from the composable
   */
  result: T

  /**
   * The Vue app instance (call app.unmount() in cleanup)
   */
  app: App<Element>
}

/**
 * Wrap a composable in Vue component context for testing.
 *
 * @param composable - Factory function that returns the composable result
 * @param options - Optional mocks for route, provide/inject
 * @returns The composable result and app instance
 */
export function withSetup<T>(
  composable: () => T,
  options: SetupOptions = {}
): SetupResult<T> {
  let result: T | undefined

  // Create a minimal component that runs the composable in setup()
  const TestComponent = defineComponent({
    setup() {
      result = composable()
      // Return empty render function
      return () => h('div')
    }
  })

  // Create the app
  const app = createApp(TestComponent)

  // Mock vue-router if route options provided
  if (options.route) {
    const mockRoute = {
      query: options.route.query || {},
      params: options.route.params || {},
      path: options.route.path || '/',
      name: options.route.name || 'test',
      meta: options.route.meta || {},
      // Common route properties
      fullPath: options.route.path || '/',
      hash: '',
      matched: [],
      redirectedFrom: undefined
    }

    // Minimal mock router - cast to any to avoid strict type checking
    // For full router testing, use @vue/test-utils with createRouter()
    const mockRouter = {
      currentRoute: { value: mockRoute },
      push: () => Promise.resolve(),
      replace: () => Promise.resolve(),
      go: () => {},
      back: () => {},
      forward: () => {},
      beforeEach: () => () => {},
      afterEach: () => () => {},
      onError: () => () => {},
      isReady: () => Promise.resolve(),
      install: () => {},
      resolve: () => mockRoute,
      options: { history: {}, routes: [] },
      addRoute: () => () => {},
      removeRoute: () => {},
      clearRoutes: () => {},
      hasRoute: () => false,
      getRoutes: () => [],
      listening: true
    } as any // eslint-disable-line @typescript-eslint/no-explicit-any

    // Provide router symbols that vue-router uses
    app.provide('router', mockRouter)
    app.provide('route', mockRoute)

    // Also set global properties for legacy access
    app.config.globalProperties.$router = mockRouter
    app.config.globalProperties.$route = mockRoute
  }

  // Add custom provide values
  if (options.provide) {
    for (const [key, value] of Object.entries(options.provide)) {
      app.provide(key, value)
    }
  }

  // Mount to a detached element (doesn't need to be in DOM)
  const root = document.createElement('div')
  app.mount(root)

  if (result === undefined) {
    throw new Error('Composable did not return a value')
  }

  return { result, app }
}

/**
 * Async version of withSetup for composables with async setup.
 */
export async function withSetupAsync<T>(
  composable: () => Promise<T>,
  options: SetupOptions = {}
): Promise<SetupResult<T>> {
  let result: T | undefined
  let error: Error | undefined

  const TestComponent = defineComponent({
    async setup() {
      try {
        result = await composable()
      } catch (e) {
        error = e as Error
      }
      return () => h('div')
    }
  })

  const app = createApp(TestComponent)

  if (options.route) {
    const mockRoute = {
      query: options.route.query || {},
      params: options.route.params || {},
      path: options.route.path || '/',
      name: options.route.name || 'test',
      meta: options.route.meta || {},
      fullPath: options.route.path || '/',
      hash: '',
      matched: [],
      redirectedFrom: undefined
    }

    app.provide('router', { currentRoute: { value: mockRoute } })
    app.provide('route', mockRoute)
  }

  if (options.provide) {
    for (const [key, value] of Object.entries(options.provide)) {
      app.provide(key, value)
    }
  }

  const root = document.createElement('div')
  app.mount(root)

  // Wait for async setup to complete
  await new Promise(resolve => setTimeout(resolve, 0))

  if (error) {
    app.unmount()
    throw error
  }

  if (result === undefined) {
    app.unmount()
    throw new Error('Composable did not return a value')
  }

  return { result, app }
}

/**
 * Helper to create a mock ref for testing.
 * Useful for config/deps parameters.
 */
export function mockRef<T>(value: T) {
  return { value }
}

/**
 * Helper to create mock deps with jest/vitest functions.
 */
export function mockFn<T extends (...args: unknown[]) => unknown>(
  implementation?: T
): T & { calls: Parameters<T>[] } {
  const calls: Parameters<T>[] = []
  const fn = ((...args: Parameters<T>) => {
    calls.push(args)
    return implementation?.(...args)
  }) as T & { calls: Parameters<T>[] }
  fn.calls = calls
  return fn
}
