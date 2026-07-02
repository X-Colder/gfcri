<template>
  <div class="bg-card border border-border rounded-xl py-16 flex flex-col items-center justify-center">
    <span class="text-4xl mb-3 opacity-40">{{ icon }}</span>
    <p class="text-sm text-muted">{{ text }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon: string
  text: string
}>()
</script>
