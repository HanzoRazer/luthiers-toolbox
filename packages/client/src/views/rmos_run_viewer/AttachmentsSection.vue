<template>
  <section :class="styles.infoSection">
    <h2>Attachments ({{ attachments?.length || 0 }})</h2>
    <div
      v-if="attachments?.length"
      :class="styles.attachmentList"
    >
      <div
        v-for="att in attachments"
        :key="att.sha256"
        :class="styles.attachmentItem"
      >
        <span :class="styles.attKind">{{ att.kind }}</span>
        <span :class="styles.attName">{{ att.filename }}</span>
        <span :class="styles.attMime">{{ att.mime }}</span>
        <span :class="styles.attSize">{{ (att.size_bytes / 1024).toFixed(1) }} KB</span>
        <button
          :class="buttons.btnSm"
          :disabled="loading"
          @click="$emit('download', att)"
        >
          Download
        </button>
      </div>
    </div>
    <div
      v-else
      :class="styles.emptyState"
    >
      No attachments
    </div>
  </section>
</template>

<script setup lang="ts">
import styles from '../RmosRunViewerView.module.css'
import { buttons } from '@/styles/shared'

export interface Attachment {
  sha256: string
  kind: string
  filename: string
  mime: string
  size_bytes: number
}

defineProps<{
  attachments: Attachment[] | undefined
  loading: boolean
}>()

defineEmits<{
  download: [att: Attachment]
}>()
</script>
