<template>
  <div class="space-y-6">
    <section class="terminal-section p-5">
      <p class="terminal-kicker">{{ t('pricing.kicker') }}</p>
      <h1 class="terminal-title">{{ t('pricing.title') }}</h1>
      <p class="terminal-copy mt-2 max-w-3xl">{{ t('pricing.subtitle') }}</p>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <article v-for="plan in plans" :key="plan.id" class="pricing-card" :class="{ 'pricing-card-primary': plan.primary }">
        <div>
          <p class="terminal-kicker">{{ plan.kicker }}</p>
          <h2>{{ plan.name }}</h2>
          <div class="price-row">
            <strong>{{ plan.price }}</strong>
            <span>{{ plan.period }}</span>
          </div>
          <p class="terminal-copy mt-3">{{ plan.description }}</p>
        </div>
        <ul>
          <li v-for="feature in plan.features" :key="feature">{{ feature }}</li>
        </ul>
        <button class="pricing-cta" :class="{ 'pricing-cta-primary': plan.primary }" :disabled="loadingPlan === plan.id" @click="handlePlan(plan.id)">
          {{ plan.cta }}
        </button>
      </article>
    </section>

    <p v-if="checkoutError" class="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-100">
      {{ checkoutError }}
    </p>

    <section class="terminal-section p-5">
      <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.55fr)]">
        <div>
          <p class="terminal-kicker">{{ t('pricing.disclaimerTitle') }}</p>
          <p class="terminal-copy mt-3">{{ t('pricing.disclaimerBody') }}</p>
        </div>
        <div class="grid gap-2">
          <router-link to="/methodology" class="pricing-link">{{ t('pricing.methodologyCta') }}</router-link>
          <router-link to="/analysis" class="pricing-link">{{ t('pricing.sampleBriefCta') }}</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createCheckout } from '@/api/billing'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'

const router = useRouter()
const { t, tx } = useI18n()
const { isLoggedIn } = useAuth()
const loadingPlan = ref('')
const checkoutError = ref('')

const plans = computed(() => [
  {
    id: 'free',
    kicker: t('pricing.freeKicker'),
    name: t('pricing.freeName'),
    price: '$0',
    period: t('pricing.periodForever'),
    description: t('pricing.freeDesc'),
    features: [
      t('pricing.freeFeature1'),
      t('pricing.freeFeature2'),
      t('pricing.freeFeature3'),
    ],
    cta: t('pricing.freeCta'),
    primary: false,
  },
  {
    id: 'monthly',
    kicker: t('pricing.monthlyKicker'),
    name: t('pricing.monthlyName'),
    price: '$19',
    period: t('pricing.periodMonth'),
    description: t('pricing.monthlyDesc'),
    features: [
      t('pricing.proFeature1'),
      t('pricing.proFeature2'),
      t('pricing.proFeature3'),
      t('pricing.proFeature4'),
      t('pricing.proFeature5'),
    ],
    cta: t('pricing.checkoutCta'),
    primary: true,
  },
  {
    id: 'annual',
    kicker: t('pricing.annualKicker'),
    name: t('pricing.annualName'),
    price: '$149',
    period: t('pricing.periodYear'),
    description: t('pricing.annualDesc'),
    features: [
      t('pricing.proFeature1'),
      t('pricing.proFeature2'),
      t('pricing.proFeature3'),
      t('pricing.annualFeature4'),
      t('pricing.annualFeature5'),
    ],
    cta: t('pricing.checkoutCta'),
    primary: false,
  },
])

async function handlePlan(planId: string) {
  checkoutError.value = ''
  if (planId === 'free') {
    router.push('/')
    return
  }
  if (!isLoggedIn.value) {
    router.push({ path: '/auth', query: { trial: '1' } })
    return
  }
  loadingPlan.value = planId
  try {
    const data = await createCheckout(planId as 'monthly' | 'annual')
    if (data.checkout_url) {
      window.location.href = data.checkout_url
      return
    }
    checkoutError.value = t('pricing.checkoutUnavailable')
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    checkoutError.value = typeof detail === 'object'
      ? tx(detail.message || detail.code || 'Checkout unavailable')
      : tx(detail || t('pricing.checkoutUnavailable'))
  } finally {
    loadingPlan.value = ''
  }
}
</script>

<style scoped>
.pricing-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: grid;
  gap: 18px;
  min-height: 410px;
  padding: 20px;
}

.pricing-card-primary {
  border-color: rgba(0, 200, 255, 0.42);
  box-shadow: 0 0 0 1px rgba(0, 200, 255, 0.08);
}

.pricing-card h2 {
  color: var(--text);
  font-size: 18px;
  font-weight: 500;
  margin-top: 8px;
}

.price-row {
  align-items: baseline;
  display: flex;
  gap: 8px;
  margin-top: 14px;
}

.price-row strong {
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 34px;
  font-weight: 500;
}

.price-row span {
  color: var(--muted);
  font-size: 12px;
}

.pricing-card ul {
  display: grid;
  gap: 10px;
}

.pricing-card li {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.pricing-card li::before {
  color: var(--accent);
  content: '•';
  margin-right: 8px;
}

.pricing-cta,
.pricing-link {
  align-self: end;
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  display: block;
  font-size: 13px;
  font-weight: 500;
  padding: 10px 12px;
  text-align: center;
  transition: border-color 0.18s ease, color 0.18s ease, background 0.18s ease;
  width: 100%;
}

.pricing-cta:hover,
.pricing-link:hover {
  border-color: rgba(0, 200, 255, 0.45);
  color: var(--accent);
}

.pricing-cta-primary {
  background: rgba(0, 200, 255, 0.12);
  border-color: rgba(0, 200, 255, 0.38);
  color: var(--accent);
}

.pricing-cta:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
