<template>
  <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover">
    <p class="text-xs text-[var(--muted)] mb-2 uppercase tracking-wider">{{ label }}</p>
    <p class="text-3xl font-extralight font-mono" :style="{ color }">{{ value }}</p>
    <p v-if="subtitle" class="text-xs text-[var(--muted)] mt-2">{{ subtitle }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  color?: string
  subtitle?: string
}>()
</script>
