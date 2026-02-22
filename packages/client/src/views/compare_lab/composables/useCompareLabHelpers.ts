/**
 * CompareLab helper functions composable.
 */
import type { Ref } from 'vue'
import type { ExportFormat, ExtensionMismatch } from './compareLabTypes'

// ============================================================================
// Types
// ============================================================================

export interface CompareLabHelpersReturn {
  fixTemplateExtension: () => void
  fixExportFormat: () => void
  sanitizePrefix: () => void
}

// ============================================================================
// Composable
// ============================================================================

export function useCompareLabHelpers(
  filenameTemplate: Ref<string>,
  exportFormat: Ref<ExportFormat>,
  exportPrefix: Ref<string>,
  extensionMismatch: Ref<ExtensionMismatch | null>
): CompareLabHelpersReturn {
  /**
   * Auto-fix: Change template extension to match format.
   */
  function fixTemplateExtension(): void {
    if (!extensionMismatch.value) return

    const { templateExt, expectedExt } = extensionMismatch.value
    const regex = new RegExp(`\\.${templateExt}$`, 'i')
    filenameTemplate.value = filenameTemplate.value.replace(regex, `.${expectedExt}`)
  }

  /**
   * Auto-fix: Change format to match template extension.
   */
  function fixExportFormat(): void {
    if (!extensionMismatch.value) return

    const validFormat = extensionMismatch.value.templateExt as ExportFormat
    if (['svg', 'png', 'csv'].includes(validFormat)) {
      exportFormat.value = validFormat
    }
  }

  /**
   * Sanitize prefix (remove special characters except underscore/hyphen).
   */
  function sanitizePrefix(): void {
    exportPrefix.value = exportPrefix.value.replace(/[^a-zA-Z0-9_-]/g, '')
  }

  return {
    fixTemplateExtension,
    fixExportFormat,
    sanitizePrefix
  }
}
