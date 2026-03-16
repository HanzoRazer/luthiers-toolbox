<!-- @deprecated — dev scratch view, not routed -->
<template>
  <div class="gallery">
    <!-- ActionButton -->
    <section class="comp-section">
      <h2 class="section-title">
        ActionButton
      </h2>
      <p class="section-desc">
        4 variants × 3 sizes × loading + disabled states
      </p>

      <div class="row-group">
        <div class="row-label">
          Variants
        </div>
        <div class="row-items">
          <ActionButton variant="primary">
            Primary
          </ActionButton>
          <ActionButton variant="secondary">
            Secondary
          </ActionButton>
          <ActionButton variant="danger">
            Danger
          </ActionButton>
          <ActionButton variant="success">
            Success
          </ActionButton>
        </div>
      </div>

      <div class="row-group">
        <div class="row-label">
          Sizes
        </div>
        <div class="row-items">
          <ActionButton size="sm">
            Small
          </ActionButton>
          <ActionButton size="md">
            Medium
          </ActionButton>
          <ActionButton size="lg">
            Large
          </ActionButton>
        </div>
      </div>

      <div class="row-group">
        <div class="row-label">
          States
        </div>
        <div class="row-items">
          <ActionButton
            :loading="true"
            loading-text="Processing..."
          >
            Loading
          </ActionButton>
          <ActionButton :disabled="true">
            Disabled
          </ActionButton>
        </div>
      </div>
    </section>

    <!-- CardPanel -->
    <section class="comp-section">
      <h2 class="section-title">
        CardPanel
      </h2>
      <p class="section-desc">
        Container with optional header, actions slot, and collapse
      </p>

      <div class="card-demo-grid">
        <CardPanel title="Basic Card">
          <p class="demo-text">
            Card body content goes here. Use for grouping related controls or data.
          </p>
        </CardPanel>

        <CardPanel
          title="Collapsible Card"
          :collapsible="true"
        >
          <p class="demo-text">
            This card can be collapsed by clicking the header.
          </p>
        </CardPanel>

        <CardPanel title="Card with Actions">
          <template #actions>
            <ActionButton
              size="sm"
              variant="secondary"
            >
              Edit
            </ActionButton>
          </template>
          <p class="demo-text">
            Header slot for actions on the right side.
          </p>
        </CardPanel>
      </div>
    </section>

    <!-- RiskBadge -->
    <section class="comp-section">
      <h2 class="section-title">
        RiskBadge
      </h2>
      <p class="section-desc">
        RMOS risk levels — GREEN / YELLOW / RED / UNKNOWN
      </p>

      <div class="row-group">
        <div class="row-label">
          Levels
        </div>
        <div class="row-items">
          <RiskBadge level="GREEN" />
          <RiskBadge level="YELLOW" />
          <RiskBadge level="RED" />
          <RiskBadge level="UNKNOWN" />
        </div>
      </div>

      <div class="row-group">
        <div class="row-label">
          Sizes
        </div>
        <div class="row-items">
          <RiskBadge
            level="GREEN"
            size="sm"
          />
          <RiskBadge
            level="GREEN"
            size="md"
          />
          <RiskBadge
            level="GREEN"
            size="lg"
          />
        </div>
      </div>

      <div class="row-group">
        <div class="row-label">
          No Icon
        </div>
        <div class="row-items">
          <RiskBadge
            level="RED"
            :show-icon="false"
          />
        </div>
      </div>
    </section>

    <!-- LoadingSpinner -->
    <section class="comp-section">
      <h2 class="section-title">
        LoadingSpinner
      </h2>
      <p class="section-desc">
        Animated SVG spinner with optional label
      </p>

      <div class="row-group">
        <div class="row-label">
          Sizes
        </div>
        <div class="row-items">
          <LoadingSpinner size="sm" />
          <LoadingSpinner size="md" />
          <LoadingSpinner size="lg" />
        </div>
      </div>

      <div class="row-group">
        <div class="row-label">
          With Label
        </div>
        <div class="row-items">
          <LoadingSpinner
            size="md"
            label="Processing G-code..."
          />
        </div>
      </div>
    </section>

    <!-- SkeletonLoader -->
    <section class="comp-section">
      <h2 class="section-title">
        SkeletonLoader
      </h2>
      <p class="section-desc">
        Shimmer placeholders for async content
      </p>

      <div class="skeleton-demo-grid">
        <div>
          <div class="demo-label">
            Text (3 lines)
          </div>
          <SkeletonLoader
            variant="text"
            :lines="3"
          />
        </div>
        <div>
          <div class="demo-label">
            Card
          </div>
          <SkeletonLoader variant="card" />
        </div>
        <div>
          <div class="demo-label">
            Avatar + Button
          </div>
          <div style="display: flex; gap: 12px; align-items: center;">
            <SkeletonLoader variant="avatar" />
            <SkeletonLoader variant="button" />
          </div>
        </div>
      </div>
    </section>

    <!-- LabeledInput -->
    <section class="comp-section">
      <h2 class="section-title">
        LabeledInput
      </h2>
      <p class="section-desc">
        Number, text, and select variants with v-model
      </p>

      <div class="input-demo-grid">
        <LabeledInput
          v-model="demoNumber"
          label="Scale Length"
          type="number"
          :min="600"
          :max="700"
          :step="0.5"
          suffix="mm"
          hint="Standard electric: 648mm (25.5&quot;)"
        />
        <LabeledInput
          v-model="demoText"
          label="Guitar Model"
          type="text"
        />
        <LabeledInput
          v-model="demoSelect"
          label="Body Style"
          type="select"
          :options="[
            { value: 'strat', label: 'Stratocaster' },
            { value: 'les_paul', label: 'Les Paul' },
            { value: 'j45', label: 'J-45 Acoustic' },
            { value: 'archtop', label: 'Archtop' },
          ]"
        />
      </div>
    </section>

    <!-- OverrideBanner -->
    <section class="comp-section">
      <h2 class="section-title">
        OverrideBanner
      </h2>
      <p class="section-desc">
        Shown when an RMOS run has a manual override applied
      </p>

      <OverrideBanner
        reason="Operator approved: material substitution from Adirondack to Sitka spruce for this batch"
        :override-artifact="{ sha256: 'a1b2c3d4e5f6789012345678', created_at: '2026-03-01' }"
      />
    </section>

    <!-- SideDrawer -->
    <section class="comp-section">
      <h2 class="section-title">
        SideDrawer
      </h2>
      <p class="section-desc">
        Slide-in panel for contextual detail without navigation
      </p>

      <div class="row-items">
        <ActionButton
          variant="secondary"
          @click="showDrawerRight = true"
        >
          Open Right Drawer
        </ActionButton>
        <ActionButton
          variant="secondary"
          @click="showDrawerLeft = true"
        >
          Open Left Drawer
        </ActionButton>
      </div>

      <SideDrawer
        :open="showDrawerRight"
        title="Run Details"
        @close="showDrawerRight = false"
      >
        <div style="padding: 16px;">
          <p style="font-size: 13px; color: #6b7280;">
            Drawer content goes here — run logs, parameter inspection, G-code preview, etc.
          </p>
          <RiskBadge
            level="GREEN"
            style="margin-top: 12px;"
          />
        </div>
      </SideDrawer>

      <SideDrawer
        :open="showDrawerLeft"
        title="Context Panel"
        side="left"
        @close="showDrawerLeft = false"
      >
        <div style="padding: 16px;">
          <p style="font-size: 13px; color: #6b7280;">
            Left-side drawer for navigation or filters.
          </p>
        </div>
      </SideDrawer>
    </section>

    <!-- SmallModal -->
    <section class="comp-section">
      <h2 class="section-title">
        SmallModal
      </h2>
      <p class="section-desc">
        Confirm and prompt dialogs — replaces browser native dialogs
      </p>

      <div class="row-items">
        <ActionButton
          variant="secondary"
          @click="showConfirm = true"
        >
          Confirm Dialog
        </ActionButton>
        <ActionButton
          variant="secondary"
          @click="showPrompt = true"
        >
          Prompt Dialog
        </ActionButton>
        <span
          v-if="modalResult"
          class="demo-result"
        >Result: "{{ modalResult }}"</span>
      </div>

      <SmallModal
        :open="showConfirm"
        mode="confirm"
        title="Promote to Manufacturing?"
        message="This will mark the rosette variant as approved and add it to the production queue. This action cannot be undone."
        ok-text="Promote"
        @ok="modalResult = 'Confirmed'; showConfirm = false"
        @cancel="showConfirm = false"
      />

      <SmallModal
        :open="showPrompt"
        mode="prompt"
        title="Rename Preset"
        message="Enter a new name for this CAM preset:"
        placeholder="e.g. Sitka Spruce Fast Pass"
        ok-text="Rename"
        @ok="(v) => { modalResult = v || '(empty)'; showPrompt = false }"
        @cancel="showPrompt = false"
      />
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import ActionButton from '@/components/ui/ActionButton.vue'
import CardPanel from '@/components/ui/CardPanel.vue'
import RiskBadge from '@/components/ui/RiskBadge.vue'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'
import LabeledInput from '@/components/ui/LabeledInput.vue'
import OverrideBanner from '@/components/ui/OverrideBanner.vue'
import SideDrawer from '@/components/ui/SideDrawer.vue'
import SmallModal from '@/components/ui/SmallModal.vue'

const demoNumber = ref(648)
const demoText = ref('Custom Build #1')
const demoSelect = ref('strat')
const showDrawerRight = ref(false)
const showDrawerLeft = ref(false)
const showConfirm = ref(false)
const showPrompt = ref(false)
const modalResult = ref('')
</script>

<style scoped>
.gallery {
  display: flex;
  flex-direction: column;
  gap: var(--space-10);
}

.comp-section {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
}

.section-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text);
  margin: 0 0 var(--space-1) 0;
}

.section-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0 0 var(--space-5) 0;
}

.row-group {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
}

.row-group:last-child {
  margin-bottom: 0;
}

.row-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-muted);
  width: 80px;
  flex-shrink: 0;
}

.row-items {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.card-demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
}

.demo-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-muted);
  margin: 0;
}

.skeleton-demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-6);
}

.demo-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-muted);
  margin-bottom: var(--space-2);
}

.input-demo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--space-4);
}

.demo-result {
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
  color: var(--color-success-dark);
  background: var(--color-success-light);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-md);
}
</style>
