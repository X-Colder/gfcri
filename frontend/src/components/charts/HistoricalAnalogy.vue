<template>
  <div v-if="currentGfcri > 0" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 card-hover">
    <p class="text-[10px] text-[var(--muted)] uppercase tracking-[3px] mb-3">Historical Analogy</p>
    <p class="text-white font-medium mb-4">
      {{ t('analogy.current') }} GFCRI <span class="font-mono" :style="{color: currentColor}">{{ currentGfcri.toFixed(1) }}</span>
      {{ t('analogy.closestTo') }} <span class="text-white">{{ analogyText(closest.crisis) }}</span>
      <span class="font-mono ml-1">{{ closest.date }}</span>
      <span class="text-[var(--muted)] ml-1">({{ t('analogy.then') }} {{ closest.gfcri }})</span>
    </p>
    <p class="text-xs text-[var(--muted)] leading-relaxed" v-if="closest.aftermath">
      ⚠️ {{ analogyText(closest.aftermath) }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '@/composables/useI18n'

const props = defineProps<{ currentGfcri: number }>()
const { t, tx } = useI18n()

const ANALOGY_TEXT_EN: Record<string, string> = {
  '1929 大萧条': '1929 Great Depression',
  '1973 石油危机': '1973 Oil Crisis',
  '1997 亚洲危机': '1997 Asian Crisis',
  '2000 互联网泡沫': '2000 Dot-Com Bubble',
  '2008 金融危机': '2008 Financial Crisis',
  '2010 欧债危机': '2010 Eurozone Debt Crisis',
  '2015 中国股灾': '2015 China Equity Crash',
  '2018 加息暴跌': '2018 Rate-Hike Selloff',
  '2020 新冠': '2020 COVID Panic',
  '2022 暴力加息': '2022 Aggressive Rate Hikes',
  '之后12个月内道琼斯再跌60%，失业率从3%升至25%': 'Over the next 12 months, the Dow fell another 60% and unemployment rose from 3% to 25%.',
  '银行开始连环倒闭，经济全面崩溃': 'Banks began failing in waves and the economy collapsed broadly.',
  '大萧条最黑暗时期，但6个月后罗斯福新政开启复苏': 'This was the darkest point of the Great Depression, but Roosevelt\'s New Deal began the recovery six months later.',
  '之后8个月SPX再跌30%，滞胀持续至1975年': 'Over the next 8 months, the S&P 500 fell another 30%, and stagflation lasted into 1975.',
  '尼克松辞职+SPX见底，但经济复苏缓慢': 'Nixon resigned and the S&P 500 bottomed, but the economic recovery was slow.',
  '之后10个月俄罗斯违约+LTCM崩盘，GFCRI升至59': 'Over the next 10 months, Russia defaulted, LTCM collapsed, and GFCRI rose to 59.',
  '美国正式衰退，之后18个月SPX再跌35%': 'The US officially entered recession, and the S&P 500 fell another 35% over the next 18 months.',
  'SPX在下月见底，之后开启5年牛市': 'The S&P 500 bottomed the following month, then began a five-year bull market.',
  '之后13个月雷曼倒闭，GFCRI飙至83.8': 'Thirteen months later, Lehman failed and GFCRI surged to 83.8.',
  '之后8个月雷曼破产，全球金融体系险些崩溃': 'Eight months later, Lehman failed and the global financial system nearly collapsed.',
  '雷曼破产当月，下月GFCRI升至83.8（峰值）': 'Lehman failed that month; GFCRI rose to its 83.8 peak the following month.',
  '恐慌顶点，美联储全力救市，5个月后SPX见底': 'This was the panic peak; the Fed intervened aggressively, and the S&P 500 bottomed five months later.',
  '美国信用降级+意大利危机，GFCRI升至58.6': 'US credit was downgraded and Italy\'s crisis intensified, lifting GFCRI to 58.6.',
  '全球恐慌性抛售，5个月后A股熔断': 'Global markets sold off in panic, and A-share circuit breakers triggered five months later.',
  '之后2个月SPX进入熊市，圣诞前夕暴跌': 'Over the next two months, the S&P 500 entered a bear market and plunged before Christmas.',
  '峰值，美联储次月转鸽，市场V型反弹': 'This was the peak; the Fed turned dovish the next month and markets staged a V-shaped rebound.',
  '之后1个月全球熔断，VIX飙至82，GFCRI达64.4': 'One month later, global circuit breakers hit, VIX surged to 82, and GFCRI reached 64.4.',
  '恐慌顶点，美联储无限QE，之后3个月V型反弹': 'This was the panic peak; the Fed launched unlimited QE, followed by a V-shaped rebound over the next three months.',
  '加息75bp后，之后3个月SPX再跌至3577': 'After the 75 bp rate hike, the S&P 500 fell to 3,577 over the next three months.',
}

function analogyText(text: string): string {
  return ANALOGY_TEXT_EN[text] || tx(text)
}

const currentColor = computed(() => {
  const v = props.currentGfcri
  return v >= 60 ? '#ef4444' : v >= 45 ? '#f97316' : v >= 25 ? '#fbbf24' : '#34d399'
})

const historicalPoints = [
  { crisis: '1929 大萧条', date: '1929-11', gfcri: 27.2, aftermath: '之后12个月内道琼斯再跌60%，失业率从3%升至25%' },
  { crisis: '1929 大萧条', date: '1930-12', gfcri: 51.5, aftermath: '银行开始连环倒闭，经济全面崩溃' },
  { crisis: '1929 大萧条', date: '1932-05', gfcri: 75.5, aftermath: '大萧条最黑暗时期，但6个月后罗斯福新政开启复苏' },
  { crisis: '1973 石油危机', date: '1974-01', gfcri: 38.2, aftermath: '之后8个月SPX再跌30%，滞胀持续至1975年' },
  { crisis: '1973 石油危机', date: '1974-08', gfcri: 67.7, aftermath: '尼克松辞职+SPX见底，但经济复苏缓慢' },
  { crisis: '1997 亚洲危机', date: '1997-10', gfcri: 49.7, aftermath: '之后10个月俄罗斯违约+LTCM崩盘，GFCRI升至59' },
  { crisis: '2000 互联网泡沫', date: '2001-03', gfcri: 46.2, aftermath: '美国正式衰退，之后18个月SPX再跌35%' },
  { crisis: '2000 互联网泡沫', date: '2002-09', gfcri: 59.2, aftermath: 'SPX在下月见底，之后开启5年牛市' },
  { crisis: '2008 金融危机', date: '2007-08', gfcri: 37.2, aftermath: '之后13个月雷曼倒闭，GFCRI飙至83.8' },
  { crisis: '2008 金融危机', date: '2008-01', gfcri: 40.4, aftermath: '之后8个月雷曼破产，全球金融体系险些崩溃' },
  { crisis: '2008 金融危机', date: '2008-09', gfcri: 65.2, aftermath: '雷曼破产当月，下月GFCRI升至83.8（峰值）' },
  { crisis: '2008 金融危机', date: '2008-10', gfcri: 83.8, aftermath: '恐慌顶点，美联储全力救市，5个月后SPX见底' },
  { crisis: '2010 欧债危机', date: '2011-08', gfcri: 42.6, aftermath: '美国信用降级+意大利危机，GFCRI升至58.6' },
  { crisis: '2015 中国股灾', date: '2015-08', gfcri: 38.8, aftermath: '全球恐慌性抛售，5个月后A股熔断' },
  { crisis: '2018 加息暴跌', date: '2018-10', gfcri: 25.3, aftermath: '之后2个月SPX进入熊市，圣诞前夕暴跌' },
  { crisis: '2018 加息暴跌', date: '2018-12', gfcri: 46.6, aftermath: '峰值，美联储次月转鸽，市场V型反弹' },
  { crisis: '2020 新冠', date: '2020-02', gfcri: 35.6, aftermath: '之后1个月全球熔断，VIX飙至82，GFCRI达64.4' },
  { crisis: '2020 新冠', date: '2020-03', gfcri: 64.4, aftermath: '恐慌顶点，美联储无限QE，之后3个月V型反弹' },
  { crisis: '2022 暴力加息', date: '2022-06', gfcri: 44.2, aftermath: '加息75bp后，之后3个月SPX再跌至3577' },
]

const closest = computed(() => {
  const sorted = [...historicalPoints].sort((a, b) =>
    Math.abs(a.gfcri - props.currentGfcri) - Math.abs(b.gfcri - props.currentGfcri)
  )
  return sorted[0] || { crisis: '—', date: '—', gfcri: 0, aftermath: '' }
})
</script>
