<template>
  <div class="space-y-6">
    <section class="terminal-section p-6">
      <p class="terminal-kicker">{{ copy.eyebrow }}</p>
      <h1 class="terminal-title mt-2">{{ copy.title }}</h1>
      <p class="terminal-copy mt-3 max-w-3xl">{{ copy.subtitle }}</p>
      <div class="audience-switch mt-5" role="tablist" :aria-label="copy.audienceLabel">
        <button :class="{ active: audience === 'personal' }" @click="audience = 'personal'">{{ copy.personalTab }}</button>
        <button :class="{ active: audience === 'institutional' }" @click="audience = 'institutional'">{{ copy.institutionalTab }}</button>
      </div>
    </section>

    <template v-if="audience === 'personal'">
      <section class="pricing-section">
        <div class="section-heading">
          <div>
            <p class="terminal-kicker">{{ copy.personalKicker }}</p>
            <h2>{{ copy.personalTitle }}</h2>
            <p class="terminal-copy mt-2">{{ copy.personalSubtitle }}</p>
          </div>
          <span class="section-badge">{{ billingConfigured ? copy.checkoutReady : copy.trialAvailable }}</span>
        </div>

        <div class="grid gap-4 lg:grid-cols-3">
          <article v-for="plan in personalPlans" :key="plan.id" class="pricing-card" :class="{ 'pricing-card-primary': plan.primary }">
            <div>
              <p class="terminal-kicker">{{ plan.kicker }}</p>
              <h3>{{ plan.name }}</h3>
              <div class="price-row">
                <strong>{{ plan.price }}</strong>
                <span>{{ plan.period }}</span>
              </div>
              <p v-if="plan.savings" class="price-savings">{{ plan.savings }}</p>
              <p class="terminal-copy mt-3">{{ plan.description }}</p>
            </div>
            <ul>
              <li v-for="feature in plan.features" :key="feature">{{ feature }}</li>
            </ul>
            <button class="pricing-cta" :class="{ 'pricing-cta-primary': plan.primary }" :disabled="loadingPlan === plan.id || catalogLoading" @click="handlePlan(plan.id)">
              {{ loadingPlan === plan.id ? copy.loading : plan.cta }}
            </button>
          </article>
        </div>

        <p v-if="checkoutError" class="pricing-error">{{ checkoutError }}</p>
      </section>
    </template>

    <template v-else>
      <section class="pricing-section">
        <div class="section-heading">
          <div>
            <p class="terminal-kicker">{{ copy.institutionalKicker }}</p>
            <h2>{{ copy.institutionalTitle }}</h2>
            <p class="terminal-copy mt-2">{{ copy.institutionalSubtitle }}</p>
          </div>
          <span class="section-badge">{{ copy.assistedSales }}</span>
        </div>
        <div class="grid gap-4 lg:grid-cols-3">
          <article v-for="offer in institutionalOffers" :key="offer.id" class="pricing-card" :class="{ 'pricing-card-primary': offer.primary }">
            <div>
              <p class="terminal-kicker">{{ offer.kicker }}</p>
              <h3>{{ offer.name }}</h3>
              <div class="price-row">
                <strong>{{ offer.price }}</strong>
                <span>{{ offer.period }}</span>
              </div>
              <p class="terminal-copy mt-3">{{ offer.description }}</p>
            </div>
            <ul>
              <li v-for="feature in offer.features" :key="feature">{{ feature }}</li>
            </ul>
            <router-link to="/institutional#request-pilot" class="pricing-cta pricing-cta-primary">{{ offer.cta }}</router-link>
          </article>
        </div>
      </section>
    </template>

    <section class="terminal-section p-6">
      <div class="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(280px,0.55fr)]">
        <div>
          <p class="terminal-kicker">{{ copy.disclaimerTitle }}</p>
          <p class="terminal-copy mt-3">{{ copy.disclaimer }}</p>
        </div>
        <div class="grid gap-2">
          <router-link to="/methodology" class="pricing-link">{{ copy.methodology }}</router-link>
          <router-link to="/analysis" class="pricing-link">{{ copy.sampleBrief }}</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { createCheckout, fetchBillingCatalog } from '@/api/billing'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'

const router = useRouter()
const { lang } = useI18n()
const { isLoggedIn, startTrial } = useAuth()
const audience = ref<'personal' | 'institutional'>('personal')
const loadingPlan = ref('')
const checkoutError = ref('')
const catalogLoading = ref(true)
const billingCatalog = ref<Record<string, any> | null>(null)

const copy = computed(() => lang.value === 'zh'
  ? {
      eyebrow: '订阅与机构方案',
      title: '按你的工作方式选择 GFCRI',
      subtitle: '个人版用于理解宏观风险，机构版用于把风险监测、解释和报告纳入团队工作流。',
      audienceLabel: '选择用户类型',
      personalTab: '个人用户',
      institutionalTab: '团队与机构',
      personalKicker: '个人版',
      personalTitle: '个人风险监测',
      personalSubtitle: '自助注册、7 天试用和 Stripe 月付/年付。',
      checkoutReady: '可在线订阅',
      trialAvailable: '可先开始试用',
      institutionalKicker: '机构版',
      institutionalTitle: '团队风险工作流',
      institutionalSubtitle: '机构版通过试点和销售沟通开通，不使用个人订阅流程。',
      assistedSales: '申请试点 / 联系销售',
      loading: '处理中...',
      unavailable: '在线支付尚未配置。你仍可以先开始 7 天试用，机构用户可以申请试点。',
      error: '操作失败，请稍后重试。',
      personal: [
        { id: 'free', kicker: '入门', name: 'Free', price: '$0', period: '永久免费', description: '快速了解今天系统性风险是否升温。', features: ['今日 GFCRI 与风险等级', '一个核心风险主题', '基础方法论说明'], cta: '查看今日风险', primary: false },
        { id: 'monthly', kicker: '主力', name: 'Pro Monthly', price: '$19', period: '/ 月', description: '适合每天跟踪宏观风险、驱动因素和下一步观察点。', features: ['完整 Daily Risk Brief', '1 年 GFCRI 趋势', 'Hidden Risk Scan', 'Top drivers 与 Watch Next', '邮件风险提醒'], cta: '订阅 Pro', primary: true },
        { id: 'annual', kicker: '最佳价值', name: 'Pro Annual', price: '$149', period: '/ 年', savings: '相比月付节省约 35%', description: '适合长期跟踪全球宏观风险周期。', features: ['包含 Pro 全部功能', '长期历史趋势跟踪', '年度价格锁定'], cta: '订阅年度 Pro', primary: false },
      ],
      institutional: [
        { id: 'pilot', kicker: '第一步', name: 'Institutional Pilot', price: '起价 $3,000', period: '/ 30 天', description: '验证一个研究、投顾或风控工作流。', features: ['3-10 名用户', '机构雷达与数据质量', '一次入门与两次复盘'], cta: '申请机构试点', primary: true },
        { id: 'team', kicker: '团队版', name: 'Institutional Team', price: '起价 $1,500', period: '/ 月，按年计费', description: '适合需要持续报告和团队协作的机构。', features: ['最多 10 个席位', '报告导出与定时简报', '标准支持与方法更新'], cta: '联系销售', primary: false },
        { id: 'enterprise', kicker: '大型机构', name: 'Enterprise Private', price: '起价 $30,000', period: '/ 年 + 部署费', description: '适合需要私有化、集成和治理能力的组织。', features: ['私有部署与 API', 'SSO/RBAC/审计路线', '定制数据与合规范围'], cta: '联系销售', primary: false },
      ],
      disclaimerTitle: '非投资建议',
      disclaimer: 'GFCRI 仅用于信息和风险监测目的，不构成投资建议、交易建议、资产配置建议或任何金融产品推荐。',
      methodology: '查看方法论',
      sampleBrief: '查看今日简报',
    }
  : {
      eyebrow: 'Plans and institutional solutions',
      title: 'Choose GFCRI for the way you work',
      subtitle: 'Personal helps you understand macro risk. Institutional helps your team monitor, explain, and operationalize it.',
      audienceLabel: 'Choose audience',
      personalTab: 'For Individuals',
      institutionalTab: 'For Teams & Institutions',
      personalKicker: 'Personal',
      personalTitle: 'Personal risk monitoring',
      personalSubtitle: 'Self-serve signup, 7-day trial, and Stripe monthly or annual billing.',
      checkoutReady: 'Online checkout ready',
      trialAvailable: 'Start with a trial',
      institutionalKicker: 'Institutional',
      institutionalTitle: 'Team risk workflow',
      institutionalSubtitle: 'Institutional access starts with a pilot or sales conversation, not a personal checkout.',
      assistedSales: 'Pilot and sales assisted',
      loading: 'Working...',
      unavailable: 'Online checkout is not configured yet. You can still start the 7-day trial or request an institutional pilot.',
      error: 'The action failed. Please try again.',
      personal: [
        { id: 'free', kicker: 'Starter', name: 'Free', price: '$0', period: 'forever', description: 'Quickly understand whether systemic risk is heating up today.', features: ['Current GFCRI and risk level', 'One core risk theme', 'Basic methodology access'], cta: "View today's risk", primary: false },
        { id: 'monthly', kicker: 'Most flexible', name: 'Pro Monthly', price: '$19', period: '/ month', description: 'For users who want daily macro-risk tracking, drivers, and watch points.', features: ['Full Daily Risk Brief', '1Y GFCRI trend', 'Hidden Risk Scan', 'Top drivers and Watch Next', 'Email risk alerts'], cta: 'Subscribe to Pro', primary: true },
        { id: 'annual', kicker: 'Best value', name: 'Pro Annual', price: '$149', period: '/ year', savings: 'Save about 35% vs monthly', description: 'For users tracking the global macro-risk cycle over time.', features: ['Everything in Pro', 'Longer-cycle trend tracking', 'Annual price lock'], cta: 'Subscribe annually', primary: false },
      ],
      institutional: [
        { id: 'pilot', kicker: 'Start here', name: 'Institutional Pilot', price: 'From $3,000', period: '/ 30 days', description: 'Validate one research, advisory, or risk workflow.', features: ['3-10 users', 'Institutional Radar and data quality', 'Onboarding plus two reviews'], cta: 'Request a pilot', primary: true },
        { id: 'team', kicker: 'Team', name: 'Institutional Team', price: 'From $1,500', period: '/ month, billed annually', description: 'For teams that need recurring reports and collaboration.', features: ['Up to 10 seats', 'Report exports and scheduled briefs', 'Standard support and methodology updates'], cta: 'Contact sales', primary: false },
        { id: 'enterprise', kicker: 'Large organizations', name: 'Enterprise Private', price: 'From $30,000', period: '/ year + setup', description: 'For private deployment, integration, and governance needs.', features: ['Private deployment and API', 'SSO/RBAC/audit roadmap', 'Custom data and compliance scope'], cta: 'Contact sales', primary: false },
      ],
      disclaimerTitle: 'Not investment advice',
      disclaimer: 'GFCRI is for informational and risk-monitoring purposes only. It is not investment advice, trading advice, asset-allocation advice, or a recommendation to buy or sell any financial product.',
      methodology: 'View methodology',
      sampleBrief: "View today's brief",
    })

const personalPlans = computed(() => copy.value.personal)
const institutionalOffers = computed(() => copy.value.institutional)
const billingConfigured = computed(() => Boolean(billingCatalog.value?.personal?.monthly?.checkout_configured))

onMounted(async () => {
  try {
    billingCatalog.value = await fetchBillingCatalog()
  } catch {
    billingCatalog.value = null
  } finally {
    catalogLoading.value = false
  }
})

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
    if (!billingConfigured.value) {
      const trialError = await startTrial()
      if (trialError) checkoutError.value = trialError
      else router.push('/')
      return
    }
    const data = await createCheckout(planId as 'monthly' | 'annual')
    if (data.checkout_url) {
      window.location.href = data.checkout_url
      return
    }
    checkoutError.value = copy.value.error
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    checkoutError.value = typeof detail === 'object' ? detail.message || detail.code || copy.value.error : detail || copy.value.error
  } finally {
    loadingPlan.value = ''
  }
}
</script>

<style scoped>
.audience-switch {
  display: inline-flex;
  gap: 4px;
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 4px;
}

.audience-switch button {
  border-radius: 5px;
  color: var(--muted);
  font-size: 12px;
  padding: 8px 12px;
}

.audience-switch button.active {
  background: rgba(0, 200, 255, 0.14);
  color: var(--accent);
}

.pricing-section {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 20px;
}

.section-heading {
  align-items: flex-start;
  display: flex;
  gap: 16px;
  justify-content: space-between;
  margin-bottom: 18px;
}

.section-heading h2 {
  color: var(--text);
  font-size: 20px;
  font-weight: 500;
  margin-top: 6px;
}

.section-badge,
.price-savings {
  color: var(--accent);
  font-size: 11px;
}

.section-badge {
  border: 1px solid rgba(0, 200, 255, 0.28);
  border-radius: 999px;
  padding: 6px 9px;
  white-space: nowrap;
}

.pricing-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 8px;
  display: grid;
  gap: 18px;
  min-height: 395px;
  padding: 20px;
}

.pricing-card-primary {
  border-color: rgba(0, 200, 255, 0.42);
  box-shadow: 0 0 0 1px rgba(0, 200, 255, 0.08);
}

.pricing-card h3 {
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
  font-size: 30px;
  font-weight: 500;
}

.price-row span {
  color: var(--muted);
  font-size: 11px;
}

.price-savings {
  margin-top: 6px;
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
  content: '+';
  margin-right: 8px;
}

.pricing-cta,
.pricing-link {
  align-self: end;
  border: 1px solid var(--border);
  border-radius: 7px;
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

.pricing-error {
  border: 1px solid rgba(255, 82, 82, 0.3);
  background: rgba(255, 82, 82, 0.08);
  border-radius: 7px;
  color: #ffd2d2;
  font-size: 12px;
  margin-top: 16px;
  padding: 10px 12px;
}

@media (max-width: 640px) {
  .section-heading {
    flex-direction: column;
  }

  .section-badge {
    white-space: normal;
  }
}
</style>