<template>
  <InstitutionalView v-if="isInstitutionalAccount" />

  <div v-else class="space-y-6">
    <section class="terminal-section p-6">
      <div class="grid gap-8 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] xl:items-end">
        <div>
          <p class="terminal-kicker">{{ copy.eyebrow }}</p>
          <h1 class="terminal-title mt-2">{{ copy.title }}</h1>
          <p class="terminal-copy mt-4 max-w-3xl">{{ copy.subtitle }}</p>
          <div class="mt-6 flex flex-wrap gap-3">
            <a href="#request-pilot" class="sales-primary">{{ copy.primaryCta }}</a>
            <router-link to="/pricing" class="sales-secondary">{{ copy.personalCta }}</router-link>
          </div>
        </div>
        <div class="sales-signal">
          <p class="terminal-kicker">{{ copy.signalKicker }}</p>
          <strong>{{ copy.signalTitle }}</strong>
          <p>{{ copy.signalBody }}</p>
        </div>
      </div>
    </section>

    <section class="grid gap-4 lg:grid-cols-3">
      <article v-for="offer in offers" :key="offer.id" class="sales-card" :class="{ 'sales-card-primary': offer.primary }">
        <p class="terminal-kicker">{{ offer.kicker }}</p>
        <h2>{{ offer.name }}</h2>
        <div class="sales-price">
          <strong>{{ offer.price }}</strong>
          <span>{{ offer.period }}</span>
        </div>
        <p class="terminal-copy mt-3">{{ offer.description }}</p>
        <ul class="mt-5">
          <li v-for="feature in offer.features" :key="feature">{{ feature }}</li>
        </ul>
        <a href="#request-pilot" class="sales-card-cta">{{ offer.cta }}</a>
      </article>
    </section>

    <section class="terminal-section p-6">
      <div class="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
        <div>
          <p class="terminal-kicker">{{ copy.workflowKicker }}</p>
          <h2 class="mt-2 text-xl font-medium text-white">{{ copy.workflowTitle }}</h2>
          <p class="terminal-copy mt-3">{{ copy.workflowBody }}</p>
          <div class="mt-5 grid gap-2 text-xs text-[var(--muted)]">
            <p v-for="item in workflowItems" :key="item">{{ item }}</p>
          </div>
        </div>

        <form id="request-pilot" class="sales-form" @submit.prevent="submitLead">
          <div class="grid gap-4 sm:grid-cols-2">
            <label>
              <span>{{ copy.company }}</span>
              <input v-model="form.company_name" required minlength="2" maxlength="160" autocomplete="organization" />
            </label>
            <label>
              <span>{{ copy.workEmail }}</span>
              <input v-model="form.work_email" required type="email" maxlength="255" autocomplete="email" />
            </label>
            <label>
              <span>{{ copy.fullName }}</span>
              <input v-model="form.full_name" maxlength="120" autocomplete="name" />
            </label>
            <label>
              <span>{{ copy.role }}</span>
              <input v-model="form.role" maxlength="120" />
            </label>
            <label>
              <span>{{ copy.teamSize }}</span>
              <select v-model="form.team_size">
                <option value="1-2">1-2</option>
                <option value="3-10">3-10</option>
                <option value="11-50">11-50</option>
                <option value="50+">50+</option>
              </select>
            </label>
            <label>
              <span>{{ copy.deployment }}</span>
              <select v-model="form.deployment">
                <option value="Hosted">{{ copy.hosted }}</option>
                <option value="Private cloud">{{ copy.privateCloud }}</option>
                <option value="Customer VPC">{{ copy.customerVpc }}</option>
              </select>
            </label>
          </div>
          <label class="mt-4 block">
            <span>{{ copy.useCase }}</span>
            <textarea v-model="form.use_case" required minlength="10" maxlength="2000" rows="3" :placeholder="copy.useCasePlaceholder" />
          </label>
          <label class="mt-4 block">
            <span>{{ copy.message }}</span>
            <textarea v-model="form.message" maxlength="2000" rows="2" :placeholder="copy.messagePlaceholder" />
          </label>
          <p v-if="error" class="sales-error">{{ error }}</p>
          <p v-if="submitted" class="sales-success">{{ copy.success }}</p>
          <div class="mt-5 flex flex-wrap items-center justify-between gap-3">
            <p class="text-[10px] leading-relaxed text-[var(--muted)]">{{ copy.privacy }}</p>
            <button type="submit" class="sales-primary" :disabled="submitting">
              {{ submitting ? copy.submitting : copy.submit }}
            </button>
          </div>
        </form>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import { submitInstitutionalLead } from '@/api/institutionalLead'
import InstitutionalView from './InstitutionalView.vue'

const { isInstitutionalAccount } = useAuth()
const { lang } = useI18n()
const submitting = ref(false)
const submitted = ref(false)
const error = ref('')

const form = reactive({
  company_name: '',
  work_email: '',
  full_name: '',
  role: '',
  team_size: '3-10',
  use_case: '',
  deployment: 'Hosted',
  message: '',
})

const copy = computed(() => lang.value === 'zh'
  ? {
      eyebrow: '机构版 / 团队工作流',
      title: '让宏观风险进入团队的研究、风控和客户沟通流程',
      subtitle: 'GFCRI Institutional Edition 将风险指数、数据质量、传导假设和可审计报告组合成团队工作台。它不提供交易信号，而是帮助团队解释风险如何形成、传播和需要复核。',
      primaryCta: '申请机构试点',
      personalCta: '查看个人版价格',
      signalKicker: '适合',
      signalTitle: '研究、财富管理与风险团队',
      signalBody: '从 30 天付费试点开始，先验证一个真实的周度风险工作流。',
      workflowKicker: '交付方式',
      workflowTitle: '先验证工作流，再扩展组织权限',
      workflowBody: '提交信息后，我们会根据团队人数、部署要求和使用场景安排试点沟通。',
      company: '公司 / 机构',
      workEmail: '工作邮箱',
      fullName: '姓名',
      role: '职位',
      teamSize: '团队人数',
      deployment: '部署方式',
      hosted: '托管环境',
      privateCloud: '私有云',
      customerVpc: '客户 VPC',
      useCase: '最重要的使用场景',
      useCasePlaceholder: '例如：每周投资委员会宏观风险复盘',
      message: '补充信息',
      messagePlaceholder: '可选：数据、合规或集成要求',
      privacy: '仅用于安排产品沟通，不会用于投资推荐或营销转售。',
      submit: '提交试点申请',
      submitting: '提交中...',
      success: '申请已收到，我们会根据工作邮箱联系你。',
    }
  : {
      eyebrow: 'Institutional / Team Workflow',
      title: 'Put macro risk into your research, risk, and client workflow',
      subtitle: 'GFCRI Institutional Edition combines the risk index, data quality, transmission hypotheses, and auditable reports into a team workspace. It does not sell trading signals; it helps teams explain how risk forms, spreads, and should be reviewed.',
      primaryCta: 'Request a pilot',
      personalCta: 'View personal pricing',
      signalKicker: 'Built for',
      signalTitle: 'Research, wealth, and risk teams',
      signalBody: 'Start with a 30-day paid pilot and validate one recurring risk workflow.',
      workflowKicker: 'Delivery model',
      workflowTitle: 'Validate the workflow before expanding access',
      workflowBody: 'Share your team size, deployment needs, and use case so we can scope the right pilot.',
      company: 'Company / institution',
      workEmail: 'Work email',
      fullName: 'Full name',
      role: 'Role',
      teamSize: 'Team size',
      deployment: 'Deployment',
      hosted: 'Hosted',
      privateCloud: 'Private cloud',
      customerVpc: 'Customer VPC',
      useCase: 'Primary use case',
      useCasePlaceholder: 'For example: weekly investment committee macro-risk review',
      message: 'Additional context',
      messagePlaceholder: 'Optional: data, compliance, or integration requirements',
      privacy: 'Used only to arrange product conversations. No investment recommendations or resale.',
      submit: 'Submit pilot request',
      submitting: 'Submitting...',
      success: 'Request received. We will contact you at your work email.',
    })

const offers = computed(() => lang.value === 'zh'
  ? [
      { id: 'pilot', kicker: '第一步', name: 'Institutional Pilot', price: '起价 $3,000', period: '/ 30 天', description: '适合验证一个研究、投顾或风控工作流。', features: ['3-10 名用户', '机构雷达与数据质量', '一次入门与两次复盘'], cta: '申请试点', primary: true },
      { id: 'team', kicker: '团队版', name: 'Institutional Team', price: '起价 $1,500', period: '/ 月，按年计费', description: '适合需要持续报告和团队协作的机构。', features: ['最多 10 个席位', '报告导出与定时简报', '标准支持与方法更新'], cta: '联系销售', primary: false },
      { id: 'enterprise', kicker: '大型机构', name: 'Enterprise Private', price: '起价 $30,000', period: '/ 年 + 部署费', description: '适合需要私有化、集成和治理能力的组织。', features: ['私有部署与 API', 'SSO/RBAC/审计路线', '定制数据与合规范围'], cta: '联系销售', primary: false },
    ]
  : [
      { id: 'pilot', kicker: 'Start here', name: 'Institutional Pilot', price: 'From $3,000', period: '/ 30 days', description: 'Validate one research, advisory, or risk workflow.', features: ['3-10 users', 'Institutional Radar and data quality', 'Onboarding plus two reviews'], cta: 'Request a pilot', primary: true },
      { id: 'team', kicker: 'Team', name: 'Institutional Team', price: 'From $1,500', period: '/ month, billed annually', description: 'For teams that need recurring reports and collaboration.', features: ['Up to 10 seats', 'Report exports and scheduled briefs', 'Standard support and methodology updates'], cta: 'Contact sales', primary: false },
      { id: 'enterprise', kicker: 'Large organizations', name: 'Enterprise Private', price: 'From $30,000', period: '/ year + setup', description: 'For private deployment, integration, and governance needs.', features: ['Private deployment and API', 'SSO/RBAC/audit roadmap', 'Custom data and compliance scope'], cta: 'Contact sales', primary: false },
    ])

const workflowItems = computed(() => lang.value === 'zh'
  ? ['研究会议：每日/周度风险简报和历史参照', '风控会议：数据质量、风险驱动和传导链复核', '客户沟通：可解释的风险卡片和非投资建议免责声明']
  : ['Research meetings: daily/weekly briefs and historical context', 'Risk meetings: data quality, drivers, and transmission review', 'Client communication: explainable risk cards with non-advisory disclosure'])

async function submitLead() {
  error.value = ''
  submitted.value = false
  submitting.value = true
  try {
    await submitInstitutionalLead({ ...form, language: lang.value })
    submitted.value = true
    form.company_name = ''
    form.work_email = ''
    form.full_name = ''
    form.role = ''
    form.use_case = ''
    form.message = ''
  } catch (err: any) {
    error.value = err?.response?.data?.detail || copy.value.success.replace(/received|已收到.*/, lang.value === 'zh' ? '提交失败，请稍后重试。' : 'Submission failed. Please try again.')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.sales-signal,
.sales-card,
.sales-form {
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.012);
  border-radius: 8px;
}

.sales-signal {
  padding: 18px;
}

.sales-signal strong {
  display: block;
  color: var(--text);
  font-size: 18px;
  font-weight: 500;
  margin-top: 10px;
}

.sales-signal p:last-child {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
  margin-top: 10px;
}

.sales-primary,
.sales-secondary,
.sales-card-cta {
  border: 1px solid rgba(0, 200, 255, 0.35);
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 40px;
  padding: 9px 14px;
  font-size: 12px;
  font-weight: 500;
  transition: 0.18s ease;
}

.sales-primary {
  background: rgba(0, 200, 255, 0.14);
  color: var(--accent);
}

.sales-secondary,
.sales-card-cta {
  border-color: var(--border);
  color: var(--text);
}

.sales-primary:hover,
.sales-secondary:hover,
.sales-card-cta:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.sales-card {
  display: flex;
  flex-direction: column;
  min-height: 360px;
  padding: 20px;
}

.sales-card-primary {
  border-color: rgba(0, 200, 255, 0.45);
  box-shadow: 0 0 0 1px rgba(0, 200, 255, 0.08);
}

.sales-card h2 {
  color: var(--text);
  font-size: 18px;
  font-weight: 500;
  margin-top: 8px;
}

.sales-price {
  align-items: baseline;
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.sales-price strong {
  color: var(--text);
  font-family: 'JetBrains Mono', monospace;
  font-size: 25px;
  font-weight: 500;
}

.sales-price span {
  color: var(--muted);
  font-size: 11px;
}

.sales-card ul {
  display: grid;
  gap: 9px;
  margin-bottom: 22px;
}

.sales-card li {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.sales-card li::before {
  color: var(--accent);
  content: '+';
  margin-right: 8px;
}

.sales-card-cta {
  margin-top: auto;
  width: 100%;
}

.sales-form {
  padding: 20px;
}

.sales-form label > span {
  color: var(--muted);
  display: block;
  font-size: 11px;
  margin-bottom: 6px;
}

.sales-form input,
.sales-form select,
.sales-form textarea {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-size: 12px;
  outline: none;
  padding: 10px 11px;
  width: 100%;
}

.sales-form input:focus,
.sales-form select:focus,
.sales-form textarea:focus {
  border-color: var(--accent);
}

.sales-error,
.sales-success {
  font-size: 11px;
  margin-top: 12px;
}

.sales-error {
  color: var(--red);
}

.sales-success {
  color: var(--green);
}

.sales-primary:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
</style>
