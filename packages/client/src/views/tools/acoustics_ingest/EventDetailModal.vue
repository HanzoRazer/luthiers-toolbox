<template>
  <div
    :class="styles.modalOverlay"
    @click.self="emit('close')"
  >
    <div :class="styles.modal">
      <header :class="styles.modalHeader">
        <h3>Event Detail</h3>
        <button
          :class="styles.modalClose"
          @click="emit('close')"
        >
          X
        </button>
      </header>
      <div :class="styles.modalBody">
        <dl :class="styles.detailGrid">
          <dt>Event ID</dt>
          <dd><code :class="styles.code">{{ event.event_id }}</code></dd>

          <dt>Created</dt>
          <dd>{{ event.created_at_utc }}</dd>

          <dt>Outcome</dt>
          <dd>
            <span :class="getOutcomeBadgeClass(event.outcome)">
              {{ getOutcomeIcon(event.outcome) }} {{ event.outcome }}
            </span>
          </dd>

          <dt>HTTP Status</dt>
          <dd>{{ event.http_status || "-" }}</dd>

          <dt>Filename</dt>
          <dd>{{ event.uploader_filename || "-" }}</dd>

          <dt>ZIP SHA256</dt>
          <dd>
            <code
              v-if="event.zip_sha256"
              :class="styles.sha"
            >
              {{ event.zip_sha256 }}
            </code>
            <span v-else>-</span>
          </dd>

          <dt>Size</dt>
          <dd>{{ formatSize(event.zip_size_bytes) }}</dd>

          <dt>Session ID</dt>
          <dd>{{ event.session_id || "-" }}</dd>

          <dt>Batch Label</dt>
          <dd>{{ event.batch_label || "-" }}</dd>

          <template v-if="event.run_id">
            <dt>Run ID</dt>
            <dd>
              <router-link :to="`/rmos/run/${event.run_id}`">
                {{ event.run_id }}
              </router-link>
            </dd>
          </template>

          <template v-if="event.bundle_id">
            <dt>Bundle ID</dt>
            <dd><code :class="styles.code">{{ event.bundle_id }}</code></dd>
          </template>

          <template v-if="event.error">
            <dt>Error Code</dt>
            <dd :class="styles.error">
              {{ event.error.code }}
            </dd>

            <dt>Error Message</dt>
            <dd :class="styles.error">
              {{ event.error.message }}
            </dd>

            <template v-if="event.error.detail">
              <dt>Error Detail</dt>
              <dd>
                <pre :class="styles.detailPre">{{ JSON.stringify(event.error.detail, null, 2) }}</pre>
              </dd>
            </template>
          </template>

          <template v-if="event.validation">
            <dt>Validation Passed</dt>
            <dd :class="event.validation.passed ? styles.ok : styles.error">
              {{ event.validation.passed ? "Yes" : "No" }}
            </dd>

            <dt>Validation Errors</dt>
            <dd>{{ event.validation.errors_count ?? 0 }}</dd>

            <dt>Validation Warnings</dt>
            <dd>{{ event.validation.warnings_count ?? 0 }}</dd>

            <template v-if="event.validation.reason">
              <dt>Reason</dt>
              <dd>{{ event.validation.reason }}</dd>
            </template>
          </template>
        </dl>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { IngestEventDetail } from "@/types/rmosAcousticsIngest";
import { formatSize } from "@/sdk/endpoints/rmosAcousticsIngest";
import styles from "../AcousticsIngestEvents.module.css";

defineProps<{
  event: IngestEventDetail
}>()

const emit = defineEmits<{
  close: []
}>()

function getOutcomeIcon(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return "\u2713";
    case "rejected":
      return "\u2717";
    case "quarantined":
      return "\u26a0";
    default:
      return "?";
  }
}

function getOutcomeBadgeClass(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return styles.outcomeBadgeAccepted;
    case "rejected":
      return styles.outcomeBadgeRejected;
    case "quarantined":
      return styles.outcomeBadgeQuarantined;
    default:
      return styles.outcomeBadge;
  }
}
</script>
