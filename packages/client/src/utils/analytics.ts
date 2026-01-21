/**
 * Analytics Utility for Luthier's Tool Box
 * Integrates Google Analytics 4 and PostHog for user tracking
 */

// ============================================================================
// PostHog Integration (DISABLED - Development Mode)
// ============================================================================

/* COMMENTED OUT - Uncomment after installing posthog-js package
interface PostHogConfig {
  apiKey: string
  apiHost: string
  autocapture: boolean
  capture_pageview: boolean
  session_recording?: {
    recordCrossOriginIframes: boolean
    maskAllInputs: boolean
    maskTextSelector: string
  }
}
*/

const posthogInstance: any = null

export function initPostHog() {
  // PostHog disabled in development mode
  // To enable: npm install posthog-js, set VITE_POSTHOG_API_KEY env var
  console.log('PostHog analytics disabled (development mode)')
  
  /* COMMENTED OUT - Uncomment after installing posthog-js package
  const apiKey = import.meta.env.VITE_POSTHOG_API_KEY
  
  if (!apiKey) {
    console.warn('PostHog API key not found. Analytics disabled.')
    return
  }

  import('posthog-js').then(({ default: posthog }) => {
    posthog.init(apiKey, {
      api_host: import.meta.env.VITE_POSTHOG_HOST || 'https://app.posthog.com',
      autocapture: true,
      capture_pageview: true,
      session_recording: {
        recordCrossOriginIframes: true,
        maskAllInputs: false,
        maskTextSelector: '.sensitive-data',
      },
      enable_recording_console_log: false,
      disable_session_recording: false,
    } as PostHogConfig)

    posthogInstance = posthog
    console.log('PostHog initialized')
  }).catch((err) => {
    console.warn('PostHog package not installed. Analytics disabled.', err)
  })
  */
}

// ============================================================================
// Google Analytics 4 Integration (DISABLED - Development Mode)
// ============================================================================

/* COMMENTED OUT - Uncomment when enabling GA4
interface GAEvent {
  event_category?: string
  event_label?: string
  value?: number
  [key: string]: any
}
*/

function gtag(...args: any[]) {
  if (typeof window !== 'undefined' && (window as any).gtag) {
    (window as any).gtag(...args)
  }
}

export function initGA4() {
  const measurementId = import.meta.env.VITE_GA4_MEASUREMENT_ID
  
  if (!measurementId) {
    console.warn('GA4 Measurement ID not found. Google Analytics disabled.')
    return
  }

  // Load GA4 script
  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`
  document.head.appendChild(script)

  // Initialize GA4
  ;(window as any).dataLayer = (window as any).dataLayer || []
  gtag('js', new Date())
  gtag('config', measurementId, {
    send_page_view: true,
    anonymize_ip: true, // GDPR compliance
  })

  console.log('Google Analytics 4 initialized')
}

// ============================================================================
// Unified Analytics API
// ============================================================================

export interface AnalyticsEvent {
  name: string
  properties?: Record<string, any>
}

export interface UserMetrics {
  adoption: {
    signups: number
    activeUsers: number
    featureUsage: Record<string, number>
    timeToFirstValue: number // minutes
  }
  engagement: {
    sessionDuration: number
    calculatorsPerSession: number
    exportCount: number
    returnRate: number // % users who return within 7 days
  }
  technical: {
    loadTime: number
    errorRate: number
    crashReports: number
    browserCompatibility: Record<string, number>
  }
  churn: {
    dropOffPoints: string[]
    reasonsGiven: string[]
  }
}

/**
 * Track custom event in both PostHog and GA4
 */
export function trackEvent(eventName: string, properties?: Record<string, any>) {
  // PostHog
  if (posthogInstance) {
    posthogInstance.capture(eventName, properties)
  }

  // Google Analytics 4
  gtag('event', eventName, properties)

  // Console log in development
  if (import.meta.env.DEV) {
    console.log(`[Analytics] ${eventName}`, properties)
  }
}

/**
 * Track page view (automatically handled by both platforms, but can be manually called)
 */
export function trackPageView(pagePath: string, pageTitle?: string) {
  // PostHog
  if (posthogInstance) {
    posthogInstance.capture('$pageview', {
      $current_url: pagePath,
      page_title: pageTitle,
    })
  }

  // GA4
  gtag('event', 'page_view', {
    page_path: pagePath,
    page_title: pageTitle,
  })
}

/**
 * Identify user (for logged-in users)
 */
export function identifyUser(userId: string, traits?: Record<string, any>) {
  // PostHog
  if (posthogInstance) {
    posthogInstance.identify(userId, traits)
  }

  // GA4
  gtag('set', 'user_properties', {
    user_id: userId,
    ...traits,
  })
}

/**
 * Track feature usage (calculator, tool, export)
 */
export function trackFeatureUsage(featureName: string, additionalProps?: Record<string, any>) {
  trackEvent('feature_used', {
    feature: featureName,
    timestamp: new Date().toISOString(),
    ...additionalProps,
  })
}

/**
 * Track DXF export (critical conversion metric)
 */
export function trackDXFExport(exportType: string, fileSize?: number, duration?: number) {
  trackEvent('dxf_export', {
    export_type: exportType,
    file_size_kb: fileSize ? Math.round(fileSize / 1024) : undefined,
    duration_ms: duration,
    success: true,
  })
}

/**
 * Track calculator usage with parameters
 */
export function trackCalculatorUsage(
  calculatorName: string,
  params: Record<string, any>,
  executionTime?: number
) {
  trackEvent('calculator_used', {
    calculator: calculatorName,
    execution_time_ms: executionTime,
    // Don't send full params for privacy, just summary
    param_count: Object.keys(params).length,
  })
}

/**
 * Track errors and exceptions
 */
export function trackError(error: Error, context?: Record<string, any>) {
  trackEvent('error_occurred', {
    error_message: error.message,
    error_stack: error.stack?.substring(0, 200), // Truncate stack trace
    ...context,
  })

  // Also send to Sentry if available
  if (typeof window !== 'undefined' && (window as any).Sentry) {
    (window as any).Sentry.captureException(error, { extra: context })
  }
}

/**
 * Track user signup/login
 */
export function trackUserSignup(method: 'email' | 'google' | 'github') {
  trackEvent('user_signup', {
    signup_method: method,
    timestamp: new Date().toISOString(),
  })
}

/**
 * Track conversion to paid (critical business metric)
 */
export function trackConversion(tier: 'free' | 'pro' | 'studio', price: number) {
  trackEvent('conversion', {
    tier,
    price,
    currency: 'USD',
  })

  // GA4 Enhanced Ecommerce
  gtag('event', 'purchase', {
    transaction_id: `txn_${Date.now()}`,
    value: price,
    currency: 'USD',
    items: [
      {
        item_id: `plan_${tier}`,
        item_name: `${tier.charAt(0).toUpperCase() + tier.slice(1)} Plan`,
        price: price,
        quantity: 1,
      },
    ],
  })
}

/**
 * Track funnel progression
 */
export function trackFunnelStep(
  funnelName: string,
  step: number,
  stepName: string,
  metadata?: Record<string, any>
) {
  trackEvent('funnel_step', {
    funnel: funnelName,
    step,
    step_name: stepName,
    ...metadata,
  })
}

/**
 * Track time to first value (critical onboarding metric)
 */
export function trackTimeToFirstValue(durationSeconds: number) {
  trackEvent('time_to_first_value', {
    duration_seconds: durationSeconds,
    duration_minutes: Math.round(durationSeconds / 60),
  })
}

/**
 * Track session start (for session duration calculation)
 */
export function trackSessionStart() {
  const sessionStart = Date.now()
  sessionStorage.setItem('session_start', sessionStart.toString())

  trackEvent('session_start', {
    timestamp: new Date(sessionStart).toISOString(),
  })
}

/**
 * Track session end (call on page unload)
 */
export function trackSessionEnd() {
  const sessionStart = sessionStorage.getItem('session_start')
  if (sessionStart) {
    const duration = Date.now() - parseInt(sessionStart)
    trackEvent('session_end', {
      duration_seconds: Math.round(duration / 1000),
      duration_minutes: Math.round(duration / 60000),
    })
  }
}

// ============================================================================
// Lifecycle Hooks
// ============================================================================

/**
 * Initialize all analytics platforms
 */
export function initAnalytics() {
  initGA4()
  initPostHog()
  trackSessionStart()

  // Track session end on page unload
  if (typeof window !== 'undefined') {
    window.addEventListener('beforeunload', trackSessionEnd)
  }
}

/**
 * Disable analytics (for GDPR opt-out)
 */
export function disableAnalytics() {
  if (posthogInstance) {
    posthogInstance.opt_out_capturing()
  }

  // GA4 opt-out
  const measurementId = import.meta.env.VITE_GA4_MEASUREMENT_ID
  if (measurementId) {
    (window as any)[`ga-disable-${measurementId}`] = true
  }

  console.log('Analytics disabled')
}

/**
 * Enable analytics (for GDPR opt-in)
 */
export function enableAnalytics() {
  if (posthogInstance) {
    posthogInstance.opt_in_capturing()
  }

  // GA4 opt-in
  const measurementId = import.meta.env.VITE_GA4_MEASUREMENT_ID
  if (measurementId) {
    (window as any)[`ga-disable-${measurementId}`] = false
  }

  console.log('Analytics enabled')
}

// ============================================================================
// Performance Monitoring
// ============================================================================

/**
 * Track page load performance
 */
export function trackPerformance() {
  if (typeof window === 'undefined' || !window.performance) {
    return
  }

  const perfData = window.performance.timing
  const pageLoadTime = perfData.loadEventEnd - perfData.navigationStart
  const domReadyTime = perfData.domContentLoadedEventEnd - perfData.navigationStart
  const responseTime = perfData.responseEnd - perfData.requestStart

  trackEvent('performance_metrics', {
    page_load_time_ms: pageLoadTime,
    dom_ready_time_ms: domReadyTime,
    response_time_ms: responseTime,
    // Web Vitals (if available)
    fcp: (window as any).FCP, // First Contentful Paint
    lcp: (window as any).LCP, // Largest Contentful Paint
    cls: (window as any).CLS, // Cumulative Layout Shift
  })
}

// Track performance after page load
if (typeof window !== 'undefined') {
  window.addEventListener('load', () => {
    // Wait for all metrics to be collected
    setTimeout(trackPerformance, 1000)
  })
}

// ============================================================================
// Exports
// ============================================================================

export default {
  init: initAnalytics,
  trackEvent,
  trackPageView,
  identifyUser,
  trackFeatureUsage,
  trackDXFExport,
  trackCalculatorUsage,
  trackError,
  trackUserSignup,
  trackConversion,
  trackFunnelStep,
  trackTimeToFirstValue,
  disable: disableAnalytics,
  enable: enableAnalytics,
}
