<template>
  <div :class="[styles.validationCard, validationStatusClass]">
    <h2>
      <span :class="styles.validationIcon">{{ validationIcon }}</span>
      Validation Report
    </h2>
    <div
      v-if="!validation"
      :class="styles.validationUnknown"
    >
      <p>No validation_report.json found in pack.</p>
      <p :class="shared.muted">
        Legacy packs may not include validation data.
      </p>
    </div>
    <div
      v-else
      :class="styles.validationContent"
    >
      <div :class="styles.validationStatus">
        <span :class="validation.passed ? styles.validationBadgePass : styles.validationBadgeFail">
          {{ validation.passed ? "PASS" : "FAIL" }}
        </span>
      </div>
      <div :class="shared.kv">
        <div><span>errors</span><code>{{ validation.errors.length }}</code></div>
        <div><span>warnings</span><code>{{ validation.warnings.length }}</code></div>
        <div v-if="validation.schema_id">
          <span>schema_id</span><code>{{ validation.schema_id }}</code>
        </div>
        <div v-if="validation.validated_at">
          <span>validated_at</span><code>{{ validation.validated_at }}</code>
        </div>
      </div>
      <details
        v-if="validation.errors.length > 0"
        :class="styles.validationDetails"
      >
        <summary>Errors ({{ validation.errors.length }})</summary>
        <ul :class="styles.validationList">
          <li
            v-for="(e, i) in validation.errors"
            :key="'err-' + i"
          >
            <code>{{ e.path }}</code>: {{ e.message }}
          </li>
        </ul>
      </details>
      <details
        v-if="validation.warnings.length > 0"
        :class="styles.validationDetails"
      >
        <summary>Warnings ({{ validation.warnings.length }})</summary>
        <ul :class="styles.validationList">
          <li
            v-for="(w, i) in validation.warnings"
            :key="'warn-' + i"
          >
            <code>{{ w.path }}</code>: {{ w.message }}
          </li>
        </ul>
      </details>
    </div>
  </div>
</template>

<script setup lang="ts">
import styles from '../AudioAnalyzerViewer.module.css'
import shared from '@/styles/dark-theme-shared.module.css'

export interface ValidationError {
  path: string
  message: string
}

export interface ValidationReport {
  passed: boolean
  errors: ValidationError[]
  warnings: ValidationError[]
  schema_id?: string
  validated_at?: string
}

defineProps<{
  validation?: ValidationReport | null
  validationStatusClass: string
  validationIcon: string
}>()
</script>
