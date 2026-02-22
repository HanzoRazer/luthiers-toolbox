<template>
  <div :class="styles.page">
    <header :class="styles.header">
      <h1>Ingest Audit Log</h1>
      <p :class="styles.sub">
        Browse all <code :class="styles.code">/import-zip</code> events with outcome status.
      </p>
    </header>

    <!-- Outcome Filter -->
    <section :class="styles.card">
      <h2>Filter by Outcome</h2>
      <div :class="styles.outcomeFilters">
        <button
          v-for="o in outcomes"
          :key="o.value"
          :class="[
            styles.outcomeChip,
            outcomeFilter === o.value && styles.outcomeChipActive,
            o.color === 'green' && styles.outcomeChipGreen,
            o.color === 'red' && styles.outcomeChipRed,
            o.color === 'yellow' && styles.outcomeChipYellow,
          ]"
          @click="toggleOutcome(o.value)"
        >
          <span :class="styles.chipIcon">{{ o.icon }}</span>
          {{ o.label }}
        </button>
        <button
          v-if="outcomeFilter"
          :class="styles.btnClear"
          @click="outcomeFilter = null"
        >
          Clear
        </button>
      </div>
    </section>

    <!-- Events List -->
    <section :class="styles.cardWide">
      <h2>Events</h2>
      <div :class="styles.listHeader">
        <span :class="styles.listCount">
          Showing {{ events.length }} events
          <template v-if="outcomeFilter"> ({{ outcomeFilter }})</template>
        </span>
        <button
          :class="styles.btn"
          :disabled="loading"
          @click="loadEvents"
        >
          {{ loading ? "Loading..." : "Refresh" }}
        </button>
      </div>

      <div
        v-if="loading && !events.length"
        :class="styles.muted"
      >
        Loading events...
      </div>
      <div
        v-else-if="error"
        :class="styles.error"
      >
        {{ error }}
      </div>
      <div
        v-else-if="!events.length"
        :class="styles.muted"
      >
        No events found. Import a viewer_pack to create events.
      </div>

      <table
        v-else
        :class="styles.tbl"
      >
        <thead>
          <tr>
            <th>Outcome</th>
            <th>Time</th>
            <th>File</th>
            <th>Size</th>
            <th>Run</th>
            <th>Error</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="evt in events"
            :key="evt.event_id"
            :class="getEventRowClass(evt.outcome)"
          >
            <td>
              <span
                :class="getOutcomeBadgeClass(evt.outcome)"
                :title="getOutcomeTooltip(evt.outcome)"
              >
                {{ getOutcomeIcon(evt.outcome) }} {{ evt.outcome }}
              </span>
            </td>
            <td
              :class="styles.timeCell"
              :title="evt.created_at_utc"
            >
              {{ formatRelative(evt.created_at_utc) }}
            </td>
            <td
              :class="styles.filenameCell"
              :title="evt.uploader_filename || '-'"
            >
              {{ truncate(evt.uploader_filename || "-", 30) }}
            </td>
            <td :class="styles.sizeCell">
              {{ formatSize(evt.zip_size_bytes) }}
            </td>
            <td :class="styles.runCell">
              <router-link
                v-if="evt.run_id"
                :to="`/rmos/run/${evt.run_id}`"
                :class="styles.runLink"
              >
                {{ evt.run_id.slice(0, 8) }}...
              </router-link>
              <span
                v-else
                :class="styles.muted"
              >-</span>
            </td>
            <td :class="styles.errorCell">
              <span
                v-if="evt.error_code"
                :class="styles.errorCode"
                :title="evt.error_message ?? undefined"
              >
                {{ evt.error_code }}
              </span>
              <span
                v-else
                :class="styles.muted"
              >-</span>
            </td>
            <td :class="styles.actionsCell">
              <button
                :class="styles.btnSm"
                @click="showDetail(evt)"
              >
                Detail
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="nextCursor"
        :class="styles.loadMore"
      >
        <button
          :class="styles.btn"
          :disabled="loadingMore"
          @click="loadMore"
        >
          {{ loadingMore ? "Loading..." : "Load More" }}
        </button>
      </div>
    </section>

    <!-- Detail Modal -->
    <div
      v-if="detailEvent"
      :class="styles.modalOverlay"
      @click.self="detailEvent = null"
    >
      <div :class="styles.modal">
        <header :class="styles.modalHeader">
          <h3>Event Detail</h3>
          <button
            :class="styles.modalClose"
            @click="detailEvent = null"
          >
            X
          </button>
        </header>
        <div :class="styles.modalBody">
          <dl :class="styles.detailGrid">
            <dt>Event ID</dt>
            <dd><code :class="styles.code">{{ detailEvent.event_id }}</code></dd>

            <dt>Created</dt>
            <dd>{{ detailEvent.created_at_utc }}</dd>

            <dt>Outcome</dt>
            <dd>
              <span :class="getOutcomeBadgeClass(detailEvent.outcome)">
                {{ getOutcomeIcon(detailEvent.outcome) }} {{ detailEvent.outcome }}
              </span>
            </dd>

            <dt>HTTP Status</dt>
            <dd>{{ detailEvent.http_status || "-" }}</dd>

            <dt>Filename</dt>
            <dd>{{ detailEvent.uploader_filename || "-" }}</dd>

            <dt>ZIP SHA256</dt>
            <dd>
              <code
                v-if="detailEvent.zip_sha256"
                :class="styles.sha"
              >
                {{ detailEvent.zip_sha256 }}
              </code>
              <span v-else>-</span>
            </dd>

            <dt>Size</dt>
            <dd>{{ formatSize(detailEvent.zip_size_bytes) }}</dd>

            <dt>Session ID</dt>
            <dd>{{ detailEvent.session_id || "-" }}</dd>

            <dt>Batch Label</dt>
            <dd>{{ detailEvent.batch_label || "-" }}</dd>

            <template v-if="detailEvent.run_id">
              <dt>Run ID</dt>
              <dd>
                <router-link :to="`/rmos/run/${detailEvent.run_id}`">
                  {{ detailEvent.run_id }}
                </router-link>
              </dd>
            </template>

            <template v-if="detailEvent.bundle_id">
              <dt>Bundle ID</dt>
              <dd><code :class="styles.code">{{ detailEvent.bundle_id }}</code></dd>
            </template>

            <template v-if="detailEvent.error">
              <dt>Error Code</dt>
              <dd :class="styles.error">
                {{ detailEvent.error.code }}
              </dd>

              <dt>Error Message</dt>
              <dd :class="styles.error">
                {{ detailEvent.error.message }}
              </dd>

              <template v-if="detailEvent.error.detail">
                <dt>Error Detail</dt>
                <dd>
                  <pre :class="styles.detailPre">{{ JSON.stringify(detailEvent.error.detail, null, 2) }}</pre>
                </dd>
              </template>
            </template>

            <template v-if="detailEvent.validation">
              <dt>Validation Passed</dt>
              <dd :class="detailEvent.validation.passed ? styles.ok : styles.error">
                {{ detailEvent.validation.passed ? "Yes" : "No" }}
              </dd>

              <dt>Validation Errors</dt>
              <dd>{{ detailEvent.validation.errors_count ?? 0 }}</dd>

              <dt>Validation Warnings</dt>
              <dd>{{ detailEvent.validation.warnings_count ?? 0 }}</dd>

              <template v-if="detailEvent.validation.reason">
                <dt>Reason</dt>
                <dd>{{ detailEvent.validation.reason }}</dd>
              </template>
            </template>
          </dl>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import {
  browseIngestEvents,
  getIngestEvent,
  formatRelativeTime,
  formatSize,
} from "@/sdk/endpoints/rmosAcousticsIngest";
import type {
  IngestEventSummary,
  IngestEventDetail,
} from "@/types/rmosAcousticsIngest";
import styles from "./AcousticsIngestEvents.module.css";

// State
const events = ref<IngestEventSummary[]>([]);
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const nextCursor = ref<string | null>(null);
const outcomeFilter = ref<string | null>(null);
const detailEvent = ref<IngestEventDetail | null>(null);

// Outcome chips
const outcomes = [
  { value: "accepted", label: "Accepted", icon: "\u2713", color: "green" },
  { value: "rejected", label: "Rejected", icon: "\u2717", color: "red" },
  { value: "quarantined", label: "Quarantined", icon: "\u26a0", color: "yellow" },
];

// Load events
async function loadEvents() {
  loading.value = true;
  error.value = null;
  try {
    const result = await browseIngestEvents({
      limit: 50,
      outcome: outcomeFilter.value as "accepted" | "rejected" | "quarantined" | undefined,
    });
    events.value = result.entries;
    nextCursor.value = result.next_cursor;
  } catch (e) {
    error.value = String(e);
  } finally {
    loading.value = false;
  }
}

// Load more
async function loadMore() {
  if (!nextCursor.value) return;
  loadingMore.value = true;
  try {
    const result = await browseIngestEvents({
      limit: 50,
      cursor: nextCursor.value,
      outcome: outcomeFilter.value as "accepted" | "rejected" | "quarantined" | undefined,
    });
    events.value.push(...result.entries);
    nextCursor.value = result.next_cursor;
  } catch (e) {
    error.value = String(e);
  } finally {
    loadingMore.value = false;
  }
}

// Show detail
async function showDetail(evt: IngestEventSummary) {
  try {
    detailEvent.value = await getIngestEvent(evt.event_id);
  } catch (e) {
    error.value = `Failed to load detail: ${e}`;
  }
}

// Toggle outcome filter
function toggleOutcome(value: string) {
  outcomeFilter.value = outcomeFilter.value === value ? null : value;
}

// Helpers
function formatRelative(ts: string): string {
  return formatRelativeTime(ts);
}

function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len - 3) + "..." : s;
}

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

function getOutcomeTooltip(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return "Pack imported successfully";
    case "rejected":
      return "Pack rejected (400/422)";
    case "quarantined":
      return "Import failed (500)";
    default:
      return outcome;
  }
}

function getEventRowClass(outcome: string): string {
  switch (outcome) {
    case "accepted":
      return styles.eventRowAccepted;
    case "rejected":
      return styles.eventRowRejected;
    case "quarantined":
      return styles.eventRowQuarantined;
    default:
      return "";
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

// Watch filter changes
watch(outcomeFilter, () => {
  loadEvents();
});

// Initial load
onMounted(() => {
  loadEvents();
});
</script>
