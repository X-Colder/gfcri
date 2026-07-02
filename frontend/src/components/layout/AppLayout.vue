<template>
  <div class="flex h-screen overflow-hidden">
    <NavSidebar />
    <main class="flex-1 overflow-y-auto p-6">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import NavSidebar from './NavSidebar.vue'
</script>
