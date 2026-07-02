<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <h2 class="text-xl font-bold">{{ t('social.title') }}</h2>
      <span v-if="contentDate" class="text-sm text-muted">{{ contentDate }}</span>
    </div>

    <!-- Tabs -->
    <div class="flex gap-1 bg-card border border-border rounded-xl p-1">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
        :class="activeTab === tab.key
          ? 'bg-accent/15 text-accent shadow-sm'
          : 'text-muted hover:text-white hover:bg-white/5'"
        @click="activeTab = tab.key"
      >
        <span class="text-base">{{ tab.icon }}</span>
        <span>{{ tab.label }}</span>
      </button>
    </div>

    <!-- WeChat Article -->
    <div v-show="activeTab === 'wechat'">
      <LoadingSpinner v-if="wechatLoading" />
      <div v-else-if="wechatContent" class="bg-card border border-border rounded-xl overflow-hidden">
        <div class="flex items-center justify-between px-5 py-3 border-b border-border">
          <div class="flex items-center gap-2">
            <div class="w-2 h-2 rounded-full bg-alert-green"></div>
            <span class="text-sm text-muted">{{ t('social.wechatPreview') }}</span>
          </div>
          <a
            :href="'data:text/html;charset=utf-8,' + encodeURIComponent(wechatContent.content)"
            download="wechat.html"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent/10 text-accent text-xs font-medium hover:bg-accent/20 transition-colors"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            {{ t('social.downloadHtml') }}
          </a>
        </div>
        <div class="p-4">
          <div class="mx-auto max-w-[375px] rounded-2xl overflow-hidden border border-border shadow-2xl shadow-black/20">
            <iframe :srcdoc="wechatContent.content" class="w-full" style="height: 720px" sandbox="allow-same-origin"></iframe>
          </div>
        </div>
      </div>
      <EmptyState v-else icon="📝" :text="t('social.noWechat')" />
    </div>

    <!-- Zsxq Post - Structured View -->
    <div v-show="activeTab === 'zsxq'">
      <LoadingSpinner v-if="zsxqLoading" />
      <div v-else-if="zsxqParsed" class="space-y-4">
        <!-- Toolbar -->
        <div class="bg-card border border-border rounded-xl px-5 py-3 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple to-accent flex items-center justify-center text-sm">🌟</div>
            <div>
              <p class="text-sm font-medium">{{ t('social.zsxqPost') }}</p>
              <p class="text-xs text-muted">{{ t('social.structuredPreview') }}</p>
            </div>
          </div>
          <div class="flex items-center gap-2">
            <span v-if="copySuccess" class="text-xs text-alert-green">{{ t('social.copied') }}</span>
            <button @click="copyZsxq" class="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-purple/15 text-purple text-sm font-medium hover:bg-purple/25 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/></svg>
              {{ t('social.copyRaw') }}
            </button>
          </div>
        </div>

        <!-- Hero Card -->
        <div class="bg-gradient-to-br from-[#0d1822] to-[#071018] border border-border rounded-xl p-6">
          <div class="text-center">
            <p class="text-xs text-muted tracking-wider uppercase mb-1">{{ t('social.gfcriTitle') }}</p>
            <p class="text-5xl font-bold font-mono mt-2" :style="{ color: alertColor }">{{ zsxqParsed.gfcri }}</p>
            <span class="inline-block mt-2 px-3 py-1 rounded-full text-xs font-medium" :style="{ color: alertColor, backgroundColor: alertColor + '1a', border: '1px solid ' + alertColor + '40' }">
              {{ tx(zsxqParsed.alertLabel) }}
            </span>
            <p class="text-xs text-muted mt-3">{{ zsxqParsed.date }} · {{ t('dash.coherence') }} {{ zsxqParsed.coherence }}</p>
          </div>
        </div>

        <!-- Sub-indices -->
        <div class="bg-card border border-border rounded-xl p-5">
          <h3 class="text-sm font-medium mb-4 flex items-center gap-2">
            <span class="w-1 h-4 rounded-full bg-accent"></span>
            {{ t('social.riskPanorama') }}
          </h3>
          <div class="space-y-3">
            <div v-for="si in zsxqParsed.subIndices" :key="si.name" class="group">
              <div class="flex items-center justify-between mb-1">
                <span class="text-xs">{{ tx(si.name) }}</span>
                <div class="flex items-center gap-2">
                  <span class="text-xs font-mono font-bold" :style="{ color: scoreColor(si.score) }">{{ si.score }}</span>
                  <span class="text-xs" :class="si.trend === '▲' ? 'text-alert-red' : 'text-muted'">{{ si.trend }}</span>
                </div>
              </div>
              <div class="h-2 bg-bg rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-500" :style="{ width: si.score + '%', backgroundColor: scoreColor(si.score) }"></div>
              </div>
              <p class="text-[10px] text-muted mt-0.5 pl-2">{{ tx(si.driver) }}</p>
            </div>
          </div>
        </div>

        <!-- Anomalous Nodes -->
        <div class="bg-card border border-border rounded-xl p-5">
          <h3 class="text-sm font-medium mb-4 flex items-center gap-2">
            <span class="w-1 h-4 rounded-full bg-alert-red"></span>
            {{ t('analysis.anomalyTitle') }} ({{ zsxqParsed.anomalies.length }})
          </h3>
          <div class="grid grid-cols-2 gap-2">
            <div v-for="a in zsxqParsed.anomalies" :key="a.name" class="bg-bg rounded-lg px-3 py-2.5 border border-border/50">
              <div class="flex items-center justify-between">
                <span class="text-xs font-medium">{{ tx(a.name) }}</span>
                <span class="text-[10px] font-mono font-bold" :class="a.sigma >= 3 ? 'text-alert-red' : 'text-alert-orange'">{{ a.direction }}{{ a.sigma }}σ</span>
              </div>
              <p class="text-[10px] text-muted mt-1">{{ a.value }}</p>
            </div>
          </div>
        </div>

        <!-- Transmission Chains -->
        <div class="bg-card border border-border rounded-xl p-5">
          <h3 class="text-sm font-medium mb-4 flex items-center gap-2">
            <span class="w-1 h-4 rounded-full bg-alert-orange"></span>
            {{ t('analysis.chainTitle') }} ({{ zsxqParsed.activeChains.length }} {{ t('analysis.chainActive') }})
          </h3>
          <div class="space-y-3">
            <div v-for="chain in zsxqParsed.activeChains" :key="chain.name" class="bg-bg rounded-lg p-3 border border-border/50">
              <div class="flex items-center justify-between mb-2">
                <span class="text-xs font-medium">{{ tx(chain.name) }}</span>
                <div class="flex items-center gap-2">
                  <div class="h-1.5 w-16 bg-border rounded-full overflow-hidden">
                    <div class="h-full rounded-full" :style="{ width: chain.stress + '%', backgroundColor: scoreColor(chain.stress) }"></div>
                  </div>
                  <span class="text-[10px] font-mono" :style="{ color: scoreColor(chain.stress) }">{{ chain.stress }}</span>
                </div>
              </div>
              <!-- Chain path visualization -->
              <div class="flex items-center gap-1 flex-wrap mb-2">
                <template v-for="(node, i) in chain.path" :key="i">
                  <span class="px-2 py-0.5 bg-accent/10 text-accent text-[10px] rounded-md border border-accent/20">{{ tx(node) }}</span>
                  <svg v-if="i < chain.path.length - 1" class="w-3 h-3 text-muted shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
                </template>
              </div>
              <p class="text-[10px] text-muted">{{ tx(chain.description) }}</p>
            </div>
          </div>
          <!-- Dormant chains -->
          <div v-if="zsxqParsed.dormantChains.length" class="mt-3 pt-3 border-t border-border/50">
            <p class="text-[10px] text-muted mb-2">{{ t('social.dormantChains') }}:</p>
            <div class="flex flex-wrap gap-1.5">
              <span v-for="dc in zsxqParsed.dormantChains" :key="dc" class="px-2 py-0.5 bg-border/30 text-muted text-[10px] rounded">{{ tx(dc) }}</span>
            </div>
          </div>
        </div>

        <!-- Alerts -->
        <div v-if="zsxqParsed.alerts.length" class="bg-card border border-border rounded-xl p-5">
          <h3 class="text-sm font-medium mb-4 flex items-center gap-2">
            <span class="w-1 h-4 rounded-full bg-alert-yellow"></span>
            {{ t('social.riskAlerts') }}
          </h3>
          <div class="space-y-2">
            <div v-for="(alert, i) in zsxqParsed.alerts" :key="i" class="flex gap-2 items-start">
              <span class="text-xs mt-0.5" :class="alert.level === 'critical' ? 'text-alert-red' : 'text-alert-yellow'">{{ alert.level === 'critical' ? '‼' : '△' }}</span>
              <p class="text-xs text-[#c9d1d9] leading-relaxed">{{ tx(alert.text) }}</p>
            </div>
          </div>
        </div>

        <!-- Analysis -->
        <div v-if="zsxqParsed.aiAnalysis" class="bg-card border border-border rounded-xl p-5">
          <h3 class="text-sm font-medium mb-4 flex items-center gap-2">
            <span class="w-1 h-4 rounded-full bg-purple"></span>
            {{ t('social.analysisView') }}
          </h3>
          <div class="text-xs leading-relaxed text-[#c9d1d9] whitespace-pre-wrap">{{ tx(zsxqParsed.aiAnalysis) }}</div>
        </div>
      </div>
      <EmptyState v-else icon="🌟" :text="t('social.noZsxq')" />
    </div>

    <!-- Share Card -->
    <div v-show="activeTab === 'card'">
      <div v-if="!cardError" class="space-y-4">
        <div class="bg-card border border-border rounded-xl p-6">
          <p class="text-center text-xs text-muted mb-4">{{ t('social.fontNote') }}</p>
          <div class="mx-auto max-w-[320px]">
            <div class="rounded-[2rem] border-[3px] border-border bg-bg p-3 shadow-2xl shadow-black/30">
              <div class="rounded-2xl overflow-hidden">
                <img :src="cardUrl" alt="GFCRI Share Card" class="w-full" @error="cardError = true" />
              </div>
            </div>
          </div>
        </div>
        <div class="bg-card border border-border rounded-xl px-5 py-4 flex items-center justify-between">
          <div>
            <p class="text-sm font-medium">{{ t('social.shareCard') }}</p>
            <p class="text-xs text-muted mt-0.5">{{ t('social.shareCardDesc') }}</p>
          </div>
          <a :href="cardUrl" download="gfcri_card.png" class="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-alert-green/15 text-alert-green text-sm font-medium hover:bg-alert-green/25 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/></svg>
            {{ t('social.downloadPng') }}
          </a>
        </div>
      </div>
      <EmptyState v-else icon="🖼️" :text="t('social.noCard')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { fetchWechatContent, fetchZsxqContent, getCardImageUrl } from '@/api/social'
import type { SocialContent } from '@/api/types'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { useI18n } from '@/composables/useI18n'

const activeTab = ref('zsxq')
const { t, tx } = useI18n()
const tabs = computed(() => [
  { key: 'wechat', icon: '💬', label: t('social.wechat') },
  { key: 'zsxq', icon: '🌟', label: t('social.zsxq') },
  { key: 'card', icon: '🖼️', label: t('social.card') },
])

const wechatContent = ref<SocialContent | null>(null)
const wechatLoading = ref(false)
const zsxqContent = ref<SocialContent | null>(null)
const zsxqLoading = ref(false)
const cardUrl = getCardImageUrl()
const cardError = ref(false)
const copySuccess = ref(false)

const contentDate = computed(() => zsxqContent.value?.date || wechatContent.value?.date || '')

interface ParsedZsxq {
  gfcri: string
  alertLabel: string
  date: string
  coherence: string
  subIndices: { name: string; score: number; trend: string; driver: string }[]
  anomalies: { name: string; value: string; sigma: number; direction: string }[]
  activeChains: { name: string; path: string[]; stress: number; description: string }[]
  dormantChains: string[]
  alerts: { level: string; text: string }[]
  aiAnalysis: string
}

const zsxqParsed = computed<ParsedZsxq | null>(() => {
  if (!zsxqContent.value) return null
  const text = zsxqContent.value.content
  return parseZsxq(text)
})

const alertColor = computed(() => {
  const label = zsxqParsed.value?.alertLabel || ''
  if (label.includes('危险')) return '#f85149'
  if (label.includes('警告')) return '#db6d28'
  if (label.includes('关注')) return '#d29922'
  return '#2ea043'
})

function scoreColor(s: number): string {
  if (s >= 75) return '#f85149'
  if (s >= 50) return '#db6d28'
  if (s >= 25) return '#d29922'
  return '#2ea043'
}

function parseZsxq(text: string): ParsedZsxq {
  const result: ParsedZsxq = {
    gfcri: '0', alertLabel: '', date: '', coherence: '',
    subIndices: [], anomalies: [], activeChains: [], dormantChains: [], alerts: [], aiAnalysis: ''
  }

  // Header
  const gfcriMatch = text.match(/风险指数:\s*([\d.]+)\s*\/\s*100\s*【(.+?)】/)
  if (gfcriMatch) {
    result.gfcri = gfcriMatch[1]
    result.alertLabel = gfcriMatch[2]
  }
  const dateMatch = text.match(/(\d{4}-\d{2}-\d{2})/)
  if (dateMatch) result.date = dateMatch[1]
  const cohMatch = text.match(/共振系数:\s*([\d.]+x)/)
  if (cohMatch) result.coherence = cohMatch[1]

  // Narrative analysis (now section 1)
  const narrativeSection = text.match(/━━ 1\. 分析观点 ━━\n\n([\s\S]*?)(?=━━ \d)/)
  if (narrativeSection) {
    result.aiAnalysis = narrativeSection[1].replace(/^\s{2}/gm, '').trim()
  }

  // Sub-indices (now section 2)
  const siRegex = /^\s{2}(\S+(?:\s+\S+)?)\s+[■□]+\s+(\d+)\s+(▲|▼|—)/gm
  const driverRegex = /^\s+└\s*主因:\s*(.+)/gm
  let m
  const sis: { name: string; score: number; trend: string }[] = []
  while ((m = siRegex.exec(text)) !== null) {
    sis.push({ name: m[1].trim(), score: parseInt(m[2]), trend: m[3] })
  }
  const drivers: string[] = []
  while ((m = driverRegex.exec(text)) !== null) {
    drivers.push(m[1].trim())
  }
  result.subIndices = sis.map((si, i) => ({ ...si, driver: drivers[i] || '' }))

  // Anomalies (now section 3)
  const anomSection = text.match(/━━ \d+\. 异常指标[\s\S]*?(?=━━ \d)/)
  if (anomSection) {
    const anomRegex = /●\s*(.+)\n\s*当前值:\s*([\d.,]+)\s*\|\s*(偏[高低])\s*([\d.]+)σ/g
    while ((m = anomRegex.exec(anomSection[0])) !== null) {
      result.anomalies.push({ name: m[1].trim(), value: m[2], sigma: parseFloat(m[4]), direction: m[3] === '偏高' ? '↑' : '↓' })
    }
  }

  // Active chains (now section 4)
  const chainSection = text.match(/━━ \d+\. 风险传导链[\s\S]*?(?=━━ \d|━━━━━)/)
  if (chainSection) {
    const chainBlocks = chainSection[0].split(/▶\s*/).slice(1)
    for (const block of chainBlocks) {
      const nameLine = block.match(/^(.+?)【活跃】/)
      if (!nameLine) continue
      const pathMatch = block.match(/│\s*(.+?)\s*│/)
      const stressMatch = block.match(/压力:\s*(\d+)/)
      const descMatch = block.match(/解读:\s*(.+)/)
      const path = pathMatch ? pathMatch[1].split(/\s*→\s*/).map(s => s.trim()) : []
      result.activeChains.push({
        name: nameLine[1].trim(),
        path,
        stress: stressMatch ? parseInt(stressMatch[1]) : 0,
        description: descMatch ? descMatch[1].trim() : '',
      })
    }
    const dormantRegex = /○\s*(.+?)【休眠/g
    while ((m = dormantRegex.exec(chainSection[0])) !== null) {
      result.dormantChains.push(m[1].trim())
    }
  }

  // Alerts (now section 5)
  const alertSection = text.match(/━━ \d+\. 风险预警[\s\S]*?(?=━━━━━)/)
  if (alertSection) {
    const criticalRegex = /‼\s*(.+?)(?=\n\s*[△‼]|\n\n━)/gs
    while ((m = criticalRegex.exec(alertSection[0])) !== null) {
      result.alerts.push({ level: 'critical', text: m[1].trim().replace(/\n\s+/g, '') })
    }
    const warnRegex = /△\s*(.+)/g
    while ((m = warnRegex.exec(alertSection[0])) !== null) {
      result.alerts.push({ level: 'warning', text: m[1].trim() })
    }
  }

  return result
}

onMounted(async () => {
  wechatLoading.value = true
  try { wechatContent.value = await fetchWechatContent() } catch {}
  wechatLoading.value = false

  zsxqLoading.value = true
  try { zsxqContent.value = await fetchZsxqContent() } catch {}
  zsxqLoading.value = false
})

function copyZsxq() {
  if (zsxqContent.value) {
    navigator.clipboard.writeText(zsxqContent.value.content)
    copySuccess.value = true
    setTimeout(() => { copySuccess.value = false }, 2000)
  }
}
</script>
