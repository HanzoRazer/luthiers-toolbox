<template>
  <div :class="styles.tabContent">
    <div :class="styles.sectionHeader">
      <h2>Finish Types</h2>
      <p>Select a finishing technique and explore its requirements</p>
    </div>

    <div :class="styles.finishGrid">
      <div
        :class="styles.finishCard"
        @click="emit('select', 'varnish')"
      >
        <div :class="styles.finishName">
          Simple Varnish
        </div>
        <div :class="styles.finishTime">
          8-12 hours labor
        </div>
        <div :class="styles.finishInfo">
          <div>• Easiest for beginners</div>
          <div>• 3-5 coats</div>
          <div>• Wipe-on or brush application</div>
          <div>• Good durability</div>
        </div>
      </div>

      <div
        :class="styles.finishCard"
        @click="emit('select', 'french')"
      >
        <div :class="styles.finishName">
          French Polish (Shellac)
        </div>
        <div :class="styles.finishTime">
          20-40 hours labor
        </div>
        <div :class="styles.finishInfo">
          <div>• Traditional hand-rubbed</div>
          <div>• 50-100+ applications</div>
          <div>• Requires skill and patience</div>
          <div>• Beautiful thin finish</div>
        </div>
      </div>

      <div
        :class="styles.finishCard"
        @click="emit('select', 'nitro')"
      >
        <div :class="styles.finishName">
          Nitrocellulose Lacquer
        </div>
        <div :class="styles.finishTime">
          15-25 hours labor
        </div>
        <div :class="styles.finishInfo">
          <div>• Classic guitar finish</div>
          <div>• 6-12 coats + sanding</div>
          <div>• Spray gun required</div>
          <div>• Vintage tone reputation</div>
        </div>
      </div>

      <div
        :class="styles.finishCard"
        @click="emit('select', 'poly')"
      >
        <div :class="styles.finishName">
          Polyurethane
        </div>
        <div :class="styles.finishTime">
          10-18 hours labor
        </div>
        <div :class="styles.finishInfo">
          <div>• Modern durable finish</div>
          <div>• 3-6 coats</div>
          <div>• Spray or wipe-on</div>
          <div>• Thick protective layer</div>
        </div>
      </div>

      <div
        :class="styles.finishCard"
        @click="emit('select', 'oil')"
      >
        <div :class="styles.finishName">
          Oil Finish (Tung/Linseed)
        </div>
        <div :class="styles.finishTime">
          12-20 hours labor
        </div>
        <div :class="styles.finishInfo">
          <div>• Natural "in-the-wood" finish</div>
          <div>• 5-8 coats + buffing</div>
          <div>• Hand application</div>
          <div>• Easy to repair</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  styles: Record<string, string>
}>()

const emit = defineEmits<{
  'select': [type: string]
}>()
</script>
