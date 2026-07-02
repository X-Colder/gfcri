<template>
  <span
    class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border"
    :style="{
      color: alertColor,
      borderColor: alertColor,
      backgroundColor: alertColor + '1a',
    }"
  >
    {{ alertLabel }}
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { getAlertColor } from '@/composables/useTheme'
import { useI18n } from '@/composables/useI18n'

const props = defineProps<{ level: string }>()
const { t } = useI18n()

const alertColor = computed(() => getAlertColor(props.level))
const alertLabel = computed(() => t(`alert.${props.level}`))
</script>
