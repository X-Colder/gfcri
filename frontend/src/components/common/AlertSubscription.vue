<template>
  <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover">
    <div class="flex flex-col gap-3">
      <div>
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[3px]">{{ copy.kicker }}</p>
        <h3 class="mt-1 text-sm font-medium text-white">{{ copy.title }}</h3>
        <p class="terminal-copy mt-2">{{ copy.description }}</p>
      </div>
      <form v-if="!submitted" class="grid gap-3" @submit.prevent="subscribe">
        <input
          v-model="email"
          required
          type="email"
          :placeholder="copy.emailPlaceholder"
          class="w-full rounded-lg border border-[var(--border)] bg-[var(--bg)] px-3 py-2 text-xs text-white focus:border-[var(--accent)] focus:outline-none"
        />
        <div class="grid gap-2 sm:grid-cols-3">
          <label v-for="option in options" :key="option.id" class="flex items-start gap-2 text-[11px] text-[var(--muted)]">
            <input v-model="preferences[option.id]" type="checkbox" class="mt-0.5 accent-[var(--accent)]" />
            <span>{{ option.label }}</span>
          </label>
        </div>
        <button
          class="rounded-lg bg-[var(--accent)] px-3 py-2 text-xs font-medium text-white transition-colors hover:bg-[var(--accent)]/80 disabled:opacity-50"
          type="submit"
          :disabled="loading"
        >
          {{ loading ? copy.submitting : copy.subscribe }}
        </button>
      </form>
      <p v-if="submitted" class="text-xs text-[var(--green)]">{{ successMessage }}</p>
      <p v-if="error" class="text-xs text-[var(--red)]">{{ error }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import client from '@/api/client'
import { useI18n } from '@/composables/useI18n'

const { lang } = useI18n()
const email = ref('')
const loading = ref(false)
const submitted = ref(false)
const error = ref('')
const preferences = reactive({
  daily_brief: true,
  risk_alerts: false,
  weekly_digest: false,
})

const copy = computed(() => lang.value === 'zh'
  ? {
      kicker: '邮件订阅',
      title: '选择你想接收的 GFCRI 内容',
      description: '验证邮箱后，我们会按你的选择发送风险简报。任何邮件都不构成投资建议。',
      emailPlaceholder: '你的邮箱',
      subscribe: '保存订阅偏好',
      submitting: '保存中...',
      success: '订阅偏好已保存。请检查邮箱完成验证；邮件服务启用后才会开始发送。',
      error: '保存失败，请稍后重试。',
      options: [
        { id: 'daily_brief', label: '每日风险简报' },
        { id: 'risk_alerts', label: '风险等级变化' },
        { id: 'weekly_digest', label: '每周宏观摘要' },
      ],
    }
  : {
      kicker: 'Email subscription',
      title: 'Choose the GFCRI updates you want',
      description: 'Verify your email and choose the risk briefs you want to receive. Emails are not investment advice.',
      emailPlaceholder: 'your@email.com',
      subscribe: 'Save preferences',
      submitting: 'Saving...',
      success: 'Preferences saved. Check your inbox to verify; delivery starts when email service is enabled.',
      error: 'Could not save preferences. Please try again.',
      options: [
        { id: 'daily_brief', label: 'Daily risk brief' },
        { id: 'risk_alerts', label: 'Risk level changes' },
        { id: 'weekly_digest', label: 'Weekly macro digest' },
      ],
    })

const options = computed(() => copy.value.options)
const successMessage = computed(() => copy.value.success)

async function subscribe() {
  loading.value = true
  submitted.value = false
  error.value = ''
  try {
    await client.post('/notifications/subscribe', {
      email: email.value,
      ...preferences,
      language: lang.value,
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    })
    submitted.value = true
  } catch {
    error.value = copy.value.error
  } finally {
    loading.value = false
  }
}
</script>