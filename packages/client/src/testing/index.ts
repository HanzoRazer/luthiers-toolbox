/**
 * Testing utilities for composable extraction verification.
 */
export {
  verifyComposable,
  runComposableTests,
  smokeTest,
  type ComposableTest,
  type Interaction,
  type VerifyResult
} from './ComposableVerifier'

export {
  withSetup,
  withSetupAsync,
  mockRef,
  mockFn,
  type SetupOptions,
  type SetupResult
} from './withSetup'
