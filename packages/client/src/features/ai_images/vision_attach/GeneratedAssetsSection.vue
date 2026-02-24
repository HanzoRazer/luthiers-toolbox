<script setup lang="ts">
/**
 * GeneratedAssetsSection - Asset grid for selecting generated images
 * Extracted from VisionAttachToRunWidget.vue
 */

defineProps<{
  assets: Array<{
    sha256: string
    url: string
    filename: string
    provider: string
  }>
  selectedAssetSha: string | null
  styles: Record<string, string>
}>()

const emit = defineEmits<{
  'select-asset': [sha256: string]
}>()

function assetCardClass(sha: string, selectedSha: string | null, styles: Record<string, string>): string {
  return selectedSha === sha ? styles.assetCardSelected : styles.assetCard
}

function truncate(s: string, len: number): string {
  return s.length > len ? s.slice(0, len) + '...' : s
}

/** Base URL for cross-origin API deployments */
const API_BASE = (import.meta as any).env?.VITE_API_BASE || ''

function resolveAssetUrl(url: string): string {
  if (!url) return '/placeholder.svg'
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url
  }
  return `${API_BASE}${url}`
}
</script>

<template>
  <section :class="styles.section">
    <h4>2. Select Asset</h4>
    <div :class="styles.assetsGrid">
      <div
        v-for="asset in assets"
        :key="asset.sha256"
        :class="assetCardClass(asset.sha256, selectedAssetSha, styles)"
        @click="emit('select-asset', asset.sha256)"
      >
        <div :class="styles.assetPreview">
          <img
            :src="resolveAssetUrl(asset.url)"
            :alt="asset.filename"
            loading="lazy"
            @error="($event.target as HTMLImageElement).src = '/placeholder.svg'"
          >
        </div>
        <div :class="styles.assetInfo">
          <div
            :class="styles.assetFilename"
            :title="asset.filename"
          >
            {{ truncate(asset.filename, 20) }}
          </div>
          <div :class="styles.assetMeta">
            <span
              :class="styles.assetSha"
              :title="asset.sha256"
            >
              {{ asset.sha256.slice(0, 8) }}...
            </span>
            <span :class="styles.assetProvider">{{ asset.provider }}</span>
          </div>
        </div>
        <div
          v-if="selectedAssetSha === asset.sha256"
          :class="styles.checkBadge"
        >
          &#10003;
        </div>
      </div>
    </div>
  </section>
</template>
