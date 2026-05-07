<script setup lang="ts">
import type { WorkflowPrerequisite } from '@/types/workflow'
import styles from './workflow.module.css'

defineProps<{
  message: string
  prerequisites?: WorkflowPrerequisite[]
}>()
</script>

<template>
  <div :class="styles.prerequisiteNotice">
    <p>{{ message }}</p>
    <ul v-if="prerequisites?.length">
      <li
        v-for="prereq in prerequisites"
        :key="prereq.label"
        :class="prereq.satisfied ? styles.satisfied : styles.unsatisfied"
      >
        <span v-if="prereq.satisfied">&#10003;</span>
        <span v-else>&#10007;</span>
        {{ prereq.label }}
      </li>
    </ul>
  </div>
</template>
