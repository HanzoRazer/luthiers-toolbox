/**
 * Error Catalog - Domain-specific error definitions
 *
 * Provides consistent error messages and recovery hints for common
 * failure scenarios in luthier workflows.
 */

import type { ErrorInfo } from '@/components/ui/ErrorRecovery.vue'

/**
 * Error categories for grouping and analytics
 */
export type ErrorCategory =
  | 'network'
  | 'validation'
  | 'dxf'
  | 'cam'
  | 'rmos'
  | 'file'
  | 'auth'
  | 'server'
  | 'unknown'

/**
 * Extended error info with category
 */
export interface CategorizedError extends ErrorInfo {
  category: ErrorCategory
  recoverable: boolean
}

/**
 * DXF-specific errors
 */
export const DXF_ERRORS: Record<string, CategorizedError> = {
  DXF_PARSE_FAILED: {
    code: 'DXF_001',
    category: 'dxf',
    message: 'Failed to parse DXF file',
    hint: 'The file may be corrupted or use an unsupported DXF version. Try exporting as DXF R14 or R2000.',
    recoverable: true,
  },
  DXF_NO_GEOMETRY: {
    code: 'DXF_002',
    category: 'dxf',
    message: 'No valid geometry found in DXF file',
    hint: 'Ensure the file contains closed polylines or circles. Open paths cannot be machined.',
    recoverable: true,
  },
  DXF_INVALID_UNITS: {
    code: 'DXF_003',
    category: 'dxf',
    message: 'Invalid or missing unit specification',
    hint: 'The DXF file units could not be determined. Specify units manually or re-export with unit information.',
    recoverable: true,
  },
  DXF_OPEN_CONTOURS: {
    code: 'DXF_004',
    category: 'dxf',
    message: 'Open contours detected',
    hint: 'Some paths are not closed. Use the "Auto-close contours" option or fix the geometry in your CAD software.',
    recoverable: true,
  },
  DXF_SELF_INTERSECTING: {
    code: 'DXF_005',
    category: 'dxf',
    message: 'Self-intersecting geometry detected',
    hint: 'Some paths cross themselves. This can cause toolpath issues. Clean up geometry in your CAD software.',
    recoverable: true,
  },
  DXF_TOO_SMALL: {
    code: 'DXF_006',
    category: 'dxf',
    message: 'Geometry too small for selected tool',
    hint: 'Some features are smaller than the tool diameter. Use a smaller tool or adjust the design.',
    recoverable: true,
  },
}

/**
 * CAM-specific errors
 */
export const CAM_ERRORS: Record<string, CategorizedError> = {
  CAM_TOOLPATH_FAILED: {
    code: 'CAM_001',
    category: 'cam',
    message: 'Toolpath generation failed',
    hint: 'Check geometry for issues like self-intersections or too-small features. Try simplifying the design.',
    recoverable: true,
  },
  CAM_INVALID_PARAMS: {
    code: 'CAM_002',
    category: 'cam',
    message: 'Invalid CAM parameters',
    hint: 'Review cutting parameters. Ensure depth of cut and stepover are appropriate for your tool and material.',
    recoverable: true,
  },
  CAM_TOOL_TOO_LARGE: {
    code: 'CAM_003',
    category: 'cam',
    message: 'Tool diameter too large for geometry',
    hint: 'Select a smaller tool or modify the design to accommodate the current tool.',
    recoverable: true,
  },
  CAM_COLLISION_DETECTED: {
    code: 'CAM_004',
    category: 'cam',
    message: 'Potential collision detected',
    hint: 'The toolpath may collide with clamps or workholding. Adjust clearance height or workholding position.',
    recoverable: true,
  },
  CAM_GCODE_EXPORT_FAILED: {
    code: 'CAM_005',
    category: 'cam',
    message: 'G-code export failed',
    hint: 'Try a different post processor or check that all required CAM parameters are set.',
    recoverable: true,
  },
  CAM_SIMULATION_ERROR: {
    code: 'CAM_006',
    category: 'cam',
    message: 'Simulation encountered an error',
    hint: 'The toolpath may have issues. Review the simulation warnings and adjust parameters.',
    recoverable: true,
  },
}

/**
 * RMOS-specific errors
 */
export const RMOS_ERRORS: Record<string, CategorizedError> = {
  RMOS_FEASIBILITY_BLOCKED: {
    code: 'RMOS_001',
    category: 'rmos',
    message: 'Operation blocked by safety rules',
    hint: 'Review the triggered rules and adjust parameters to meet safety requirements.',
    recoverable: true,
  },
  RMOS_OVERRIDE_REQUIRED: {
    code: 'RMOS_002',
    category: 'rmos',
    message: 'Manual override required',
    hint: 'This operation requires supervisor approval. Contact your supervisor or review safety documentation.',
    recoverable: true,
  },
  RMOS_RUN_NOT_FOUND: {
    code: 'RMOS_003',
    category: 'rmos',
    message: 'Manufacturing run not found',
    hint: 'The run may have been deleted or you may not have access. Check the run ID and your permissions.',
    recoverable: false,
  },
  RMOS_ARTIFACT_MISSING: {
    code: 'RMOS_004',
    category: 'rmos',
    message: 'Required artifact not found',
    hint: 'A previous step may not have completed successfully. Try re-running the workflow from the beginning.',
    recoverable: true,
  },
  RMOS_VALIDATION_FAILED: {
    code: 'RMOS_005',
    category: 'rmos',
    message: 'Run validation failed',
    hint: 'The run parameters did not pass validation. Review the error details and correct the issues.',
    recoverable: true,
  },
}

/**
 * File operation errors
 */
export const FILE_ERRORS: Record<string, CategorizedError> = {
  FILE_TOO_LARGE: {
    code: 'FILE_001',
    category: 'file',
    message: 'File is too large',
    hint: 'Maximum file size is 50MB. Try compressing the file or splitting it into smaller parts.',
    recoverable: true,
  },
  FILE_INVALID_TYPE: {
    code: 'FILE_002',
    category: 'file',
    message: 'Invalid file type',
    hint: 'This file type is not supported. Check the accepted formats and convert your file.',
    recoverable: true,
  },
  FILE_UPLOAD_FAILED: {
    code: 'FILE_003',
    category: 'file',
    message: 'File upload failed',
    hint: 'Check your network connection and try again. If the problem persists, try a smaller file.',
    recoverable: true,
  },
  FILE_DOWNLOAD_FAILED: {
    code: 'FILE_004',
    category: 'file',
    message: 'File download failed',
    hint: 'Check your network connection and try again. The file may no longer be available.',
    recoverable: true,
  },
}

/**
 * All error catalogs combined
 */
export const ERROR_CATALOG = {
  ...DXF_ERRORS,
  ...CAM_ERRORS,
  ...RMOS_ERRORS,
  ...FILE_ERRORS,
}

/**
 * Get error info by code
 */
export function getErrorByCode(code: string): CategorizedError | null {
  return ERROR_CATALOG[code] || null
}

/**
 * Create error info from API response
 */
export function createErrorFromResponse(response: {
  ok: false
  error: string
  code?: string
  hint?: string
  details?: any
}): CategorizedError {
  // Try to find a matching catalog error
  if (response.code && ERROR_CATALOG[response.code]) {
    return {
      ...ERROR_CATALOG[response.code],
      details: response.details ? JSON.stringify(response.details, null, 2) : undefined,
    }
  }

  // Extract category from code prefix
  let category: ErrorCategory = 'unknown'
  if (response.code) {
    const prefix = response.code.split('_')[0]
    if (['DXF', 'CAM', 'RMOS', 'FILE'].includes(prefix)) {
      category = prefix.toLowerCase() as ErrorCategory
    }
  }

  return {
    code: response.code,
    category,
    message: response.error,
    hint: response.hint,
    details: response.details ? JSON.stringify(response.details, null, 2) : undefined,
    recoverable: true,
  }
}

/**
 * Determine if an error is recoverable (can be retried)
 */
export function isRecoverableError(error: CategorizedError | ErrorInfo): boolean {
  if ('recoverable' in error) {
    return error.recoverable
  }

  // Network errors are generally recoverable
  if ('code' in error && error.code?.startsWith('NETWORK')) {
    return true
  }

  // Validation errors are recoverable (user can fix input)
  if ('code' in error && error.code?.includes('VALIDATION')) {
    return true
  }

  // Server errors may be transient
  if ('code' in error && error.code?.startsWith('SERVER')) {
    return true
  }

  return true // Default to recoverable
}

/**
 * Get recovery actions for an error
 */
export function getRecoveryActions(
  error: CategorizedError,
  handlers: {
    onRetry?: () => void
    onModifyInput?: () => void
    onContactSupport?: () => void
    onViewDocs?: () => void
  }
): ErrorInfo['actions'] {
  const actions: ErrorInfo['actions'] = []

  if (error.recoverable && handlers.onRetry) {
    actions.push({
      label: 'Try Again',
      variant: 'primary',
      action: handlers.onRetry,
    })
  }

  if (error.category === 'validation' && handlers.onModifyInput) {
    actions.push({
      label: 'Modify Input',
      variant: 'secondary',
      action: handlers.onModifyInput,
    })
  }

  if (error.category === 'dxf' && handlers.onViewDocs) {
    actions.push({
      label: 'View DXF Guide',
      variant: 'secondary',
      action: handlers.onViewDocs,
    })
  }

  if (!error.recoverable && handlers.onContactSupport) {
    actions.push({
      label: 'Contact Support',
      variant: 'secondary',
      action: handlers.onContactSupport,
    })
  }

  return actions
}
