<template>
  <div>
    <!-- Hero -->
    <div class="text-center pt-16 pb-12 fade-in">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[6px] mb-4">Historical Validation</p>
      <h1 class="text-5xl font-extralight text-white mb-3">{{ t('backtest.title') }}</h1>
      <p class="text-lg text-[var(--muted)] font-light max-w-2xl mx-auto leading-relaxed">
        {{ t('backtest.subtitle.zh') }}<br/>
        <span class="text-white font-normal">{{ t('backtest.subtitle2') }}</span>
      </p>
    </div>

    <!-- Key Stats -->
    <div class="grid grid-cols-4 gap-4 mb-14 fade-in fade-in-delay-1">
      <div class="text-center py-6">
        <p class="text-5xl font-extralight text-[var(--green)] font-mono">15/15</p>
        <p class="text-xs text-[var(--muted)] mt-2 uppercase tracking-wider">{{ t('backtest.detected') }}</p>
      </div>
      <div class="text-center py-6">
        <p class="text-5xl font-extralight text-[var(--accent)] font-mono">0</p>
        <p class="text-xs text-[var(--muted)] mt-2 uppercase tracking-wider">{{ t('backtest.missed') }}</p>
      </div>
      <div class="text-center py-6">
        <p class="text-5xl font-extralight text-[var(--yellow)] font-mono">33</p>
        <p class="text-xs text-[var(--muted)] mt-2 uppercase tracking-wider">{{ t('backtest.early') }}</p>
      </div>
      <div class="text-center py-6">
        <p class="text-5xl font-extralight text-[var(--orange)] font-mono">83.8</p>
        <p class="text-xs text-[var(--muted)] mt-2 uppercase tracking-wider">{{ t('backtest.peak') }}</p>
      </div>
    </div>

    <!-- Crisis Summary Table -->
    <div class="mb-14 fade-in fade-in-delay-2">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Validation Results</p>
      <h3 class="text-lg font-light text-white mb-6">{{ t('backtest.overview') }}</h3>
      <div class="mb-5 rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        <p class="text-xs leading-relaxed text-[var(--muted)]">{{ t('backtest.twoAxisNote') }}</p>
      </div>

      <div class="overflow-hidden rounded-xl border border-[var(--border)]">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-[var(--card)] text-[var(--muted)] text-xs uppercase tracking-wider">
              <th class="text-left px-5 py-3 font-medium">{{ t('backtest.event') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.time') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.damageLevel') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.peakPressure') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.leadTime') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.pressureBand') }}</th>
              <th class="text-center px-3 py-3 font-medium">{{ t('backtest.result') }}</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="(c, i) in crises" :key="i">
            <tr class="border-t border-[var(--border)] hover:bg-white/[0.02] transition-colors cursor-pointer"
                @click="selectedCrisis = selectedCrisis === i ? -1 : i">
              <td class="px-5 py-4 font-medium text-white">
                <span class="mr-2 text-xs opacity-40">{{ selectedCrisis === i ? '▼' : '▶' }}</span>
                {{ tx(c.name) }}
              </td>
              <td class="text-center px-3 py-4 text-[var(--muted)]">{{ c.year }}</td>
              <td class="text-center px-3 py-4">
                <span class="inline-block px-2 py-0.5 rounded text-xs font-medium"
                      :style="damageBadgeStyle(c.name)">
                  D{{ damageLevel(c.name) }} · {{ damageLabel(damageProfile(c.name)) }}
                </span>
              </td>
              <td class="text-center px-3 py-4">
                <span class="font-mono text-base" :style="{ color: alertColor(c.peakAlert) }">{{ c.peakGfcri }}</span>
              </td>
              <td class="text-center px-3 py-4">
                <span v-if="c.leadMonths > 0" class="text-[var(--green)]">{{ c.leadMonths }} {{ t("backtest.months") }}</span>
                <span v-else class="text-[var(--muted)]"> {{ t("backtest.sameMonth") }} </span>
              </td>
              <td class="text-center px-3 py-4">
                <span class="inline-block px-2 py-0.5 rounded text-xs font-medium"
                      :style="{ background: alertColor(c.peakAlert) + '20', color: alertColor(c.peakAlert) }">
                  {{ c.peakAlert }}
                </span>
              </td>
              <td class="text-center px-3 py-4">
                <span class="text-[var(--green)]">{{ t('backtest.detected') }}</span>
              </td>
            </tr>
            <!-- Expanded detail row -->
            <tr v-if="selectedCrisis === i">
              <td colspan="7" class="px-5 py-5 bg-white/[0.01]">
                <div class="max-w-5xl">
                  <p class="text-xs text-[var(--muted)] mb-4">{{ backtestText(c.description) }}</p>

                  <div class="mb-5 rounded-lg border border-[var(--border)] bg-white/[0.012] p-4">
                    <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                      <div>
                        <p class="text-[10px] uppercase tracking-[3px] text-[var(--muted)] mb-1">{{ t('backtest.realizedDamage') }}</p>
                        <h4 class="text-sm text-white font-medium">
                          D{{ damageLevel(c.name) }} · {{ damageLabel(damageProfile(c.name)) }}
                        </h4>
                        <p class="mt-2 text-xs leading-relaxed text-[var(--muted)]">{{ damageSummary(damageProfile(c.name)) }}</p>
                      </div>
                      <div class="grid grid-cols-2 gap-2 sm:min-w-[260px]">
                        <div class="terminal-metric">
                          <span>{{ t('backtest.damageLevel') }}</span>
                          <strong :style="damageTextStyle(c.name)">D{{ damageLevel(c.name) }}</strong>
                        </div>
                        <div class="terminal-metric">
                          <span>{{ t('backtest.peakPressure') }}</span>
                          <strong :style="alertTextStyle(c.peakAlert)">{{ c.peakGfcri }}</strong>
                        </div>
                      </div>
                    </div>
                    <p class="mt-3 text-[11px] leading-relaxed text-[var(--muted)]">{{ t('backtest.damageVsPressureNote') }}</p>
                    <div class="mt-4 grid gap-3 lg:grid-cols-2">
                      <div v-for="item in damageMetrics(c.name)" :key="item.label" class="rounded-lg border border-[var(--border)] p-3">
                        <p class="text-[10px] uppercase tracking-[2px] text-[var(--muted)]">{{ damageMetricLabel(item) }}</p>
                        <p class="mt-1 text-xs leading-relaxed text-white">{{ damageMetricValue(item) }}</p>
                      </div>
                    </div>
                  </div>

                  <!-- Monthly timeline with bars -->
                  <p class="text-[10px] uppercase tracking-[3px] text-[var(--muted)] mb-3">{{ t('backtest.timeline') }}</p>
                  <div class="space-y-2">
                    <div v-for="(ev, j) in c.timeline" :key="j"
                         class="flex items-center gap-3 py-1.5"
                         :class="ev.isPeak ? 'bg-white/[0.03] -mx-2 px-2 rounded' : ''">
                      <span class="w-16 text-xs font-mono text-[var(--muted)] shrink-0">{{ ev.date }}</span>
                      <div class="w-12 text-right shrink-0">
                        <span class="font-mono text-xs" :style="{ color: alertColor(ev.alert) }">{{ ev.gfcri }}</span>
                      </div>
                      <div class="w-40 shrink-0">
                        <div class="h-2 bg-white/[0.03] rounded-full overflow-hidden">
                          <div class="h-full rounded-full transition-all" :style="{ width: (ev.gfcri / 100 * 100) + '%', backgroundColor: alertColor(ev.alert) }"></div>
                        </div>
                      </div>
                      <span class="text-xs flex-1" :class="ev.isPeak ? 'text-white font-medium' : 'text-[var(--muted)]'">
                        {{ backtestText(ev.event) }}
                        <span v-if="ev.isPeak" class="ml-1 text-[9px] px-1 py-0.5 rounded bg-[var(--red)]/10 text-[var(--red)]">{{ t('backtest.peakMarker') }}</span>
                      </span>
                    </div>
                  </div>
                </div>
              </td>
            </tr>
            </template>
          </tbody>
        </table>
      </div>
    </div>


    <!-- Current Position vs History -->
    <div class="mb-14 fade-in fade-in-delay-2" v-if="currentGfcri > 0">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Where Are We Now?</p>
      <h3 class="text-lg font-light text-white mb-6">{{ t('backtest.where') }}</h3>

      <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
        <!-- Scale bar -->
        <div class="relative h-12 mb-8">
          <!-- Background zones -->
          <div class="absolute inset-0 flex rounded-full overflow-hidden">
            <div class="h-full" style="width:25%;background:rgba(52,211,153,0.08)"></div>
            <div class="h-full" style="width:25%;background:rgba(251,191,36,0.08)"></div>
            <div class="h-full" style="width:25%;background:rgba(249,115,22,0.08)"></div>
            <div class="h-full" style="width:25%;background:rgba(239,68,68,0.08)"></div>
          </div>
          <!-- Zone labels -->
          <div class="absolute -bottom-6 w-full flex text-[9px] text-[var(--muted)]">
            <span class="w-1/4 text-center">{{ t('common.safe') }} 0-25</span>
            <span class="w-1/4 text-center">{{ t('alert.yellow') }} 25-50</span>
            <span class="w-1/4 text-center">{{ t('alert.orange') }} 50-75</span>
            <span class="w-1/4 text-center">{{ t('alert.red') }} 75-100</span>
          </div>
          <!-- Historical crisis markers -->
          <div v-for="c in crises" :key="'marker-'+c.name"
               class="absolute top-1 h-10 w-0.5 rounded opacity-30"
               :style="{ left: c.peakGfcri + '%', backgroundColor: alertColor(c.peakAlert) }"
               :title="c.name + ': ' + c.peakGfcri">
          </div>
          <!-- Historical crisis labels (top ones only) -->
          <div v-for="c in topCrises" :key="'label-'+c.name"
               class="absolute -top-5 text-[8px] text-[var(--muted)] whitespace-nowrap"
               :style="{ left: c.peakGfcri + '%', transform: 'translateX(-50%)' }">
            {{ tx(c.shortName) }}
          </div>
          <!-- Current position marker -->
          <div class="absolute top-0 h-12 flex flex-col items-center z-10"
               :style="{ left: Math.min(currentGfcri, 100) + '%', transform: 'translateX(-50%)' }">
            <div class="w-3 h-3 rounded-full border-2 border-white shadow-lg"
                 :style="{ backgroundColor: currentColor }"></div>
            <div class="w-0.5 h-6" :style="{ backgroundColor: currentColor }"></div>
            <div class="mt-1 px-2 py-0.5 rounded text-xs font-mono font-bold whitespace-nowrap"
                 :style="{ backgroundColor: currentColor + '20', color: currentColor }">
              {{ t('common.today') }} {{ currentGfcri.toFixed(1) }}
            </div>
          </div>
        </div>

        <!-- Comparison text -->
        <div class="mt-12 grid grid-cols-3 gap-4 text-center">
          <div>
            <p class="text-xs text-[var(--muted)] mb-1">{{ t('backtest.exceeded') }}</p>
            <p class="text-2xl font-extralight font-mono text-white">{{ exceededCount }} / {{ crises.length }}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--muted)] mb-1">{{ t('backtest.closest') }}</p>
            <p class="text-sm text-white font-medium">{{ closestCrisis }}</p>
          </div>
          <div>
            <p class="text-xs text-[var(--muted)] mb-1">{{ t('backtest.distTo2008') }}</p>
            <p class="text-2xl font-extralight font-mono" :style="{ color: currentColor }">
              {{ (83.8 - currentGfcri).toFixed(0) }} {{ t('common.points') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- GFCRI Peak Comparison Chart -->
    <div class="mb-14 fade-in fade-in-delay-3">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Peak Comparison</p>
      <h3 class="text-lg font-light text-white mb-6">{{ t('backtest.peakCompare') }}</h3>
      <v-chart :option="peakChartOption" style="height: 320px" autoresize />
    </div>

    <!-- Key Findings -->
    <div class="mb-14 fade-in">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Key Findings</p>
      <h3 class="text-lg font-light text-white mb-6">{{ t('backtest.keyFindings') }}</h3>

      <div class="grid grid-cols-2 gap-5">
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 card-hover border-l-[3px] border-l-[var(--green)]">
          <h4 class="text-white font-medium mb-3">{{ t('backtest.finding1.title') }}</h4>
          <p class="text-sm text-[var(--muted)] leading-relaxed">
            {{ t('backtest.finding1.body') }}
          </p>
        </div>
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 card-hover border-l-[3px] border-l-[var(--yellow)]">
          <h4 class="text-white font-medium mb-3">{{ t('backtest.finding2.title') }}</h4>
          <p class="text-sm text-[var(--muted)] leading-relaxed">
            {{ t('backtest.finding2.body') }}
          </p>
        </div>
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 card-hover border-l-[3px] border-l-[var(--accent)]">
          <h4 class="text-white font-medium mb-3">{{ t('backtest.finding3.title') }}</h4>
          <p class="text-sm text-[var(--muted)] leading-relaxed">
            {{ t('backtest.finding3.body') }}
          </p>
        </div>
        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 card-hover border-l-[3px] border-l-[var(--orange)]">
          <h4 class="text-white font-medium mb-3">{{ t('backtest.finding4.title') }}</h4>
          <p class="text-sm text-[var(--muted)] leading-relaxed">
            {{ t('backtest.finding4.body') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Historical Analogy (P5) -->
    <div class="mb-14 fade-in" v-if="currentGfcri > 0">
      <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Historical Analogy</p>
      <h3 class="text-lg font-light text-white mb-6">{{ t('backtest.analogy') }}</h3>
      <HistoricalAnalogy :currentGfcri="currentGfcri" />
    </div>

    <!-- Methodology Note -->
    <div class="text-center py-10 border-t border-[var(--border)]">
      <p class="text-[11px] text-[var(--muted)]/40 uppercase tracking-[3px] mb-2">Methodology</p>
      <p class="text-xs text-[var(--muted)]/30 max-w-lg mx-auto leading-relaxed">
        {{ t('backtest.methodology') }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import client from '@/api/client'
import HistoricalAnalogy from '@/components/charts/HistoricalAnalogy.vue'
import { useI18n } from '@/composables/useI18n'

use([BarChart, GridComponent, TooltipComponent, CanvasRenderer])

const selectedCrisis = ref(-1)
const currentGfcri = ref(0)
const { t, tx, lang } = useI18n()

const BACKTEST_TEXT_EN: Record<string, string> = {
  '华尔街崩盘→银行连环倒闭→全球经济崩溃→失业率25%': 'Wall Street crash -> cascading bank failures -> global economic collapse -> unemployment reached 25%.',
  '首次预警，比崩盘早 16 个月': 'First warning, 16 months before the crash.',
  '道琼斯见顶 362（泡沫顶峰）': 'Dow Jones peaked at 362, marking the top of the bubble.',
  '道琼斯一月跌 37%': 'The Dow fell 37% in one month.',
  '合众国银行倒闭，信用利差飙升': 'Bank of United States failed and credit spreads surged.',
  '英镑脱离金本位，全球传染': 'Sterling left the gold standard, spreading stress globally.',
  '失业 22.3%，道琼斯 52，信用利差 5.64%': 'Unemployment reached 22.3%, the Dow fell to 52, and credit spreads hit 5.64%.',
  '罗斯福就任，全国银行关门': 'Roosevelt took office and declared a nationwide bank holiday.',
  '经济部分恢复，失业仍 16.4%': 'The economy partly recovered, but unemployment was still 16.4%.',

  '布雷顿森林体系崩溃，美元与黄金脱钩，全球货币秩序重塑': 'The Bretton Woods system collapsed as the dollar was detached from gold, reshaping the global monetary order.',
  '首次预警，美国衰退开始': 'First warning as the US recession began.',
  '经济衰退深化': 'The recession deepened.',
  '西德马克浮动，美元危机': 'The Deutsche Mark floated and the dollar crisis intensified.',
  '尼克松关闭黄金窗口': 'Nixon closed the gold window.',
  '史密森协议，美元贬值 8%': 'The Smithsonian Agreement devalued the dollar by 8%.',
  '英镑浮动': 'Sterling moved to a floating exchange rate.',

  'OPEC 石油禁运→油价翻4倍→全球滞胀→SPX 暴跌 48%': 'OPEC oil embargo -> oil prices quadrupled -> global stagflation -> S&P 500 fell 48%.',
  '首次预警，OPEC 禁运后': 'First warning after the OPEC embargo.',
  '油价翻倍冲击实体经济': 'The oil price doubled and hit the real economy.',
  '石油禁运解除但油价不降': 'The embargo ended, but oil prices did not fall.',
  '通胀失控，经济衰退': 'Inflation ran out of control and the economy entered recession.',
  '尼克松辞职，SPX 接近底部': 'Nixon resigned while the S&P 500 neared its bottom.',
  'SPX 见底，跌幅 48%': 'The S&P 500 bottomed after a 48% decline.',
  '经济开始复苏': 'The economy began to recover.',

  '联邦基金利率升至 20%→深度衰退→拉美债务危机': 'Fed funds rose to 20% -> deep recession -> Latin American debt crisis.',
  '首次预警，利率升至 14%': 'First warning as rates rose to 14%.',
  '利率达 20% 历史纪录': 'Rates reached a historic 20%.',
  '二次探底开始': 'A second downturn began.',
  '经济二次衰退': 'The economy entered a second recession.',
  '失业率破 10%': 'Unemployment exceeded 10%.',
  '墨西哥债务违约': 'Mexico defaulted on its debt.',
  '美联储转向宽松': 'The Federal Reserve pivoted toward easing.',

  '单日暴跌 22.6%，史上最大单日跌幅（月度数据难捕捉闪崩）': 'The market fell 22.6% in one day, the largest daily drop on record; monthly data naturally undercaptures flash crashes.',
  '首次预警，股市过热': 'First warning as equities overheated.',
  '模型峰值（月度颗粒度限制）': 'Model peak, constrained by monthly data granularity.',
  '道指见顶 2722': 'The Dow peaked at 2,722.',
  '黑色星期一（月内事件）': 'Black Monday occurred within the month.',
  '美联储注入流动性，恢复': 'The Fed injected liquidity and markets recovered.',

  '索罗斯做空英镑，欧洲汇率机制崩溃（区域性危机，对全球冲击有限）': 'Soros shorted sterling and the European Exchange Rate Mechanism broke down; this was regional, with limited global spillover.',
  '芬兰马克贬值，ERM 压力初现': 'The Finnish markka devalued and ERM pressure emerged.',
  'GFCRI 峰值，预示危机加剧': 'GFCRI peaked, signaling intensifying stress.',
  '黑色星期三，英镑退出 ERM': 'Black Wednesday: sterling exited the ERM.',
  '瑞典放弃固定汇率': 'Sweden abandoned its fixed exchange rate.',
  '爱尔兰镑贬值 10%': 'The Irish pound devalued by 10%.',

  '美联储意外加息引发全球债券抛售 + 橙县破产 + 墨西哥比索危机': 'Unexpected Fed hikes triggered a global bond selloff, Orange County bankruptcy, and the Mexican peso crisis.',
  '预警触发，比峰值早 10 个月': 'Warning triggered 10 months before the peak.',
  '美联储意外加息 25bp': 'The Fed unexpectedly raised rates by 25 bp.',
  'VIX 飙升至 20.5，全球债市恐慌': 'VIX jumped to 20.5 as global bond markets panicked.',
  '墨西哥政治暗杀，比索承压': 'Political assassinations in Mexico pressured the peso.',
  '橙县因衍生品亏损破产': 'Orange County went bankrupt after derivatives losses.',
  '墨西哥比索危机爆发': 'The Mexican peso crisis erupted.',

  '泰铢崩盘→韩元崩盘→俄罗斯违约→LTCM 崩盘': 'Thai baht collapse -> Korean won collapse -> Russia default -> LTCM collapse.',
  '预警触发，比峰值早 12 个月': 'Warning triggered 12 months before the peak.',
  '泰铢崩盘，亚洲危机起点': 'The Thai baht collapsed, starting the Asian crisis.',
  '港股暴跌，全球传染': 'Hong Kong equities plunged and contagion spread globally.',
  '韩元崩盘，IMF 介入': 'The Korean won collapsed and the IMF stepped in.',
  '俄罗斯违约 → LTCM 崩盘': 'Russia defaulted, leading to the LTCM collapse.',
  '美联储紧急降息': 'The Fed delivered emergency rate cuts.',

  '纳斯达克崩盘→安然/世通→SPX 跌 50%': 'Nasdaq collapse -> Enron and WorldCom -> S&P 500 fell 50%.',
  '预警触发，比峰值早 33 个月': 'Warning triggered 33 months before the peak.',
  '科技股闪崩，纳斯达克单周跌 25%': 'Tech stocks crashed, with Nasdaq down 25% in one week.',
  '美国经济正式衰退': 'The US economy officially entered recession.',
  '911 恐怖袭击，首次橙色': 'The 9/11 attacks pushed GFCRI into orange for the first time.',
  'WorldCom 会计丑闻': 'WorldCom accounting scandal.',
  'SPX 见底 815': 'The S&P 500 bottomed at 815.',

  '次贷→Bear Stearns→雷曼→全球系统性崩溃（含隐藏风险修正）': 'Subprime -> Bear Stearns -> Lehman -> global systemic collapse, including hidden-risk adjustment.',
  '首次预警：信用利差异动，比雷曼早 14 个月': 'First warning: credit spreads moved abnormally, 14 months before Lehman.',
  'BNP 冻结3只基金，TED利差飙至1.71%': 'BNP froze three funds and the TED spread jumped to 1.71%.',
  '信用利差持续走阔，银行间信任未恢复': 'Credit spreads kept widening and interbank trust did not recover.',
  '全球股市暴跌，美联储紧急降息75bp': 'Global equities plunged and the Fed made an emergency 75 bp rate cut.',
  '🏛️ Bear Stearns 被收购，美联储周日紧急行动（隐藏信号：政策力度>>市场反应）': 'Bear Stearns was acquired and the Fed took emergency Sunday action; hidden signal: policy intensity far exceeded market reaction.',
  '⚡ "假平静"：VIX降到20但BAA利差3.1%不退，银行股反弹仅大盘1/3': 'False calm: VIX fell to 20, but BAA spreads stayed at 3.1%, and bank stocks rebounded only one-third as much as the broad market.',
  '⚡ 隐藏风险升级：信用分化加速+美联储资产负债表异常扩张': 'Hidden risk escalated: credit divergence accelerated and the Fed balance sheet expanded abnormally.',
  '🏛️ IndyMac倒闭（储蓄银行→零售端蔓延），政策力度持续加码': 'IndyMac failed, showing stress spreading from savings banks to retail channels, while policy support kept intensifying.',
  '⚡ VIX=20.6"正常"但4个隐藏信号亮起：政策异常+信用分化+银行背离+避险买盘': 'VIX at 20.6 looked normal, but four hidden signals flashed: policy abnormality, credit divergence, bank-stock underperformance, and safe-haven buying.',
  '💥 雷曼破产（9/15），隐藏风险全面暴露，所有侧面信号验证为真': 'Lehman failed on 9/15; hidden risk fully surfaced and all side signals were validated.',
  '恐慌顶点 VIX=59.9，🏛️ TARP 7000亿被否决→通过': 'Panic peak: VIX reached 59.9, and the $700bn TARP was rejected before later passing.',
  '🏛️ 美联储QE1（1.75万亿），信用利差开始见顶': 'Fed QE1 of $1.75tn began and credit spreads started to peak.',
  'SPX见底666，信用利差回落确认恢复开始': 'The S&P 500 bottomed at 666 and falling credit spreads confirmed recovery had begun.',

  '希腊→爱尔兰→意大利→"Whatever it takes"': 'Greece -> Ireland -> Italy -> "Whatever it takes".',
  '预警触发，比峰值早 22 个月': 'Warning triggered 22 months before the peak.',
  '希腊正式求助 EU/IMF': 'Greece formally requested EU/IMF assistance.',
  '欧盟 7500 亿救助': 'The EU announced a EUR 750bn rescue package.',
  '美国信用评级下调': 'The US sovereign credit rating was downgraded.',
  '意大利 10Y 突破 7%': 'Italy 10Y yield broke above 7%.',
  '德拉吉：Whatever it takes': 'Draghi said: "Whatever it takes."',

  'A 股暴跌→811 汇改→人民币贬值→全球恐慌→熔断': 'A-share crash -> August 11 FX reform -> RMB depreciation -> global panic -> circuit breakers.',
  'A 股见顶 5178': 'A-shares peaked at 5,178.',
  '811 汇改，人民币贬值 2%，全球恐慌': 'The August 11 FX reform devalued the RMB by 2%, triggering global panic.',
  '全球股市恐慌性抛售': 'Global equities sold off in panic.',
  'A 股熔断，全球暴跌': 'A-share circuit breakers triggered and global markets plunged.',

  '美联储加息→中美贸易战→VIX 闪崩→圣诞暴跌': 'Fed hikes -> US-China trade war -> VIX shock -> Christmas selloff.',
  '预警触发，比峰值早 11 个月': 'Warning triggered 11 months before the peak.',
  'VIX 暴涨到 50+，闪崩事件': 'VIX spiked above 50 during the volatility shock.',
  '中美贸易战开打': 'The US-China trade war began.',
  '美股暴跌，科技股领跌': 'US equities plunged, led by technology stocks.',
  'SPX 进入熊市，圣诞暴跌': 'The S&P 500 entered a bear market during the Christmas selloff.',
  '美联储转鸽，市场反弹': 'The Fed turned dovish and markets rebounded.',

  '全球熔断→VIX=82→无限 QE→V 型反弹': 'Global circuit breakers -> VIX at 82 -> unlimited QE -> V-shaped rebound.',
  '武汉封城，市场初步反应': 'Wuhan lockdown; markets began to react.',
  '疫情全球扩散，恐慌开始': 'The pandemic spread globally and panic began.',
  '全球熔断，VIX=82，美联储无限 QE': 'Global circuit breakers hit, VIX reached 82, and the Fed launched unlimited QE.',
  '油价负值，但股市开始反弹': 'Oil prices went negative, but equities began to rebound.',
  'V 型反弹确认': 'The V-shaped rebound was confirmed.',

  '美联储激进加息→强美元→英国养老金危机→SVB 倒闭': 'Aggressive Fed hikes -> strong dollar -> UK pension crisis -> SVB failure.',
  '预警触发，比峰值早 8 个月': 'Warning triggered 8 months before the peak.',
  '俄乌冲突叠加加息': 'Russia-Ukraine conflict compounded the rate-hike shock.',
  '加息 75bp，四十年最大幅度': 'The Fed hiked 75 bp, the largest move in four decades.',
  '英国养老金危机，SPX 见底': 'The UK pension crisis hit while the S&P 500 bottomed.',
  '硅谷银行倒闭': 'Silicon Valley Bank failed.',
}

type DamageMetric = {
  label: string
  labelEn: string
  value: string
  valueEn: string
}

type DamageProfile = {
  level: number
  label: string
  labelEn: string
  summary: string
  summaryEn: string
  metrics: DamageMetric[]
}

const DEFAULT_DAMAGE_PROFILE: DamageProfile = {
  level: 1,
  label: '市场调整',
  labelEn: 'Market Correction',
  summary: '主要损害集中在资产价格和风险偏好，实体经济损害有限。',
  summaryEn: 'Damage was mostly concentrated in asset prices and risk appetite, with limited real-economy damage.',
  metrics: [
    { label: '市场损害', labelEn: 'Market Damage', value: '局部资产价格回撤', valueEn: 'Localized asset-price drawdown.' },
  ],
}

const DAMAGE_PROFILES: Record<string, DamageProfile> = {
  '1929 大萧条': {
    level: 5,
    label: '萧条或结构性损害',
    labelEn: 'Depression / Structural Damage',
    summary: '股市、银行系统、就业和实体经济同时遭受长期结构性损害，是最高等级的历史损害样本。',
    summaryEn: 'Equities, banks, employment, and the real economy suffered long-duration structural damage, making this the highest-damage historical reference.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: '道琼斯从峰值下跌约 89%，熊市持续近三年。', valueEn: 'The Dow fell roughly 89% from peak to trough and the bear market lasted almost three years.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '美国实际 GDP 深度收缩，工业生产大幅下滑。', valueEn: 'US real GDP contracted deeply and industrial production collapsed.' },
      { label: '就业损害', labelEn: 'Labor Damage', value: '失业率升至约 25%。', valueEn: 'Unemployment rose to roughly 25%.' },
      { label: '银行损害', labelEn: 'Banking Damage', value: '数千家银行倒闭，全国银行假日和金融体系重组。', valueEn: 'Thousands of banks failed, leading to a national bank holiday and financial-system restructuring.' },
    ],
  },
  '1971 尼克松冲击': {
    level: 2,
    label: '区域或制度性市场损害',
    labelEn: 'Regional / Institutional Market Damage',
    summary: '主要损害是全球货币制度断裂和美元信用重定价，实体经济损害低于典型衰退危机。',
    summaryEn: 'Damage centered on the breakdown of the global monetary regime and repricing of dollar credibility, with less direct real-economy damage than a recession crisis.',
    metrics: [
      { label: '制度损害', labelEn: 'Institutional Damage', value: '美元与黄金脱钩，布雷顿森林体系实质瓦解。', valueEn: 'The dollar was detached from gold and Bretton Woods effectively broke down.' },
      { label: '汇率损害', labelEn: 'FX Damage', value: '主要货币进入重估和浮动阶段。', valueEn: 'Major currencies entered a revaluation and floating-rate phase.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '伴随美国衰退和通胀压力，但不是系统性金融崩溃。', valueEn: 'Accompanied by US recession and inflation pressure, but not a systemic financial collapse.' },
    ],
  },
  '1973 石油危机': {
    level: 3,
    label: '宏观衰退损害',
    labelEn: 'Macro Recession Damage',
    summary: '能源供给冲击造成全球滞胀、股市深度回撤和实体经济衰退。',
    summaryEn: 'The energy supply shock created global stagflation, deep equity losses, and real-economy recession damage.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: 'S&P 500 从高点下跌约 48%。', valueEn: 'The S&P 500 fell roughly 48% from peak to trough.' },
      { label: '通胀损害', labelEn: 'Inflation Damage', value: '油价数倍上涨，通胀失控。', valueEn: 'Oil prices multiplied and inflation became difficult to control.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '美国和多国经济进入衰退，实际收入和需求受损。', valueEn: 'The US and other economies entered recession, damaging real income and demand.' },
    ],
  },
  '1980 沃尔克紧缩': {
    level: 3,
    label: '宏观衰退损害',
    labelEn: 'Macro Recession Damage',
    summary: '极端加息压制通胀，但代价是深度衰退、失业上升和拉美债务危机。',
    summaryEn: 'Extreme rate hikes broke inflation, but caused deep recession, higher unemployment, and Latin American debt stress.',
    metrics: [
      { label: '利率冲击', labelEn: 'Rate Shock', value: '联邦基金利率一度接近 20%。', valueEn: 'Fed funds approached 20%.' },
      { label: '就业损害', labelEn: 'Labor Damage', value: '美国失业率升至约 10.8%。', valueEn: 'US unemployment rose to around 10.8%.' },
      { label: '外债损害', labelEn: 'External Debt Damage', value: '高美元利率触发拉美债务危机。', valueEn: 'High dollar rates helped trigger the Latin American debt crisis.' },
    ],
  },
  '1987 黑色星期一': {
    level: 1,
    label: '市场调整',
    labelEn: 'Market Correction',
    summary: '损害集中在股票市场的极速下跌，政策流动性支持后未演化为实体经济衰退。',
    summaryEn: 'Damage was concentrated in a violent equity-market crash and did not turn into a broad recession after liquidity support.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: '道琼斯单日下跌 22.6%。', valueEn: 'The Dow fell 22.6% in one day.' },
      { label: '系统损害', labelEn: 'System Damage', value: '市场微观结构和组合保险策略暴露脆弱性。', valueEn: 'Market structure and portfolio-insurance fragility were exposed.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '未造成持续宏观衰退。', valueEn: 'It did not cause a sustained macro recession.' },
    ],
  },
  '1992 ERM 危机': {
    level: 2,
    label: '区域或市场损害',
    labelEn: 'Regional / Market Damage',
    summary: '损害集中在欧洲汇率机制、英镑和部分欧洲货币体系，对全球实体经济冲击有限。',
    summaryEn: 'Damage centered on the European Exchange Rate Mechanism, sterling, and parts of the European currency system, with limited global real-economy damage.',
    metrics: [
      { label: '汇率损害', labelEn: 'FX Damage', value: '英镑退出 ERM，多国货币被迫重估。', valueEn: 'Sterling exited the ERM and several currencies were forced to reprice.' },
      { label: '政策损害', labelEn: 'Policy Damage', value: '固定汇率政策可信度受损。', valueEn: 'The credibility of fixed-exchange-rate policy was damaged.' },
      { label: '全球损害', labelEn: 'Global Damage', value: '全球信用和经济损害有限。', valueEn: 'Global credit and economic damage was limited.' },
    ],
  },
  '1994 全球债市大屠杀': {
    level: 2,
    label: '区域或市场损害',
    labelEn: 'Regional / Market Damage',
    summary: '主要损害来自全球债券重估、杠杆机构亏损和墨西哥比索危机。',
    summaryEn: 'Damage came from global bond repricing, leveraged losses, and the Mexican peso crisis.',
    metrics: [
      { label: '债券损害', labelEn: 'Bond Damage', value: '全球债券收益率快速上行，债券组合大幅亏损。', valueEn: 'Global bond yields rose sharply and bond portfolios suffered losses.' },
      { label: '机构损害', labelEn: 'Institutional Damage', value: '橙县因衍生品和利率风险破产。', valueEn: 'Orange County went bankrupt because of derivatives and rate risk.' },
      { label: '外部损害', labelEn: 'External Damage', value: '墨西哥比索危机爆发。', valueEn: 'The Mexican peso crisis erupted.' },
    ],
  },
  '1997 亚洲金融危机': {
    level: 3,
    label: '宏观衰退损害',
    labelEn: 'Macro Recession Damage',
    summary: '亚洲多国货币、银行、企业资产负债表和经济增长遭受实质损害，并外溢至俄罗斯和 LTCM。',
    summaryEn: 'Multiple Asian economies suffered real damage across currencies, banks, corporate balance sheets, and growth, with spillovers to Russia and LTCM.',
    metrics: [
      { label: '汇率损害', labelEn: 'FX Damage', value: '泰铢、韩元、印尼盾等大幅贬值。', valueEn: 'The Thai baht, Korean won, Indonesian rupiah and others depreciated sharply.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '韩国、印尼、泰国等经济体出现深度衰退或增长骤降。', valueEn: 'South Korea, Indonesia, Thailand and others experienced deep recession or sharp growth collapse.' },
      { label: '金融损害', labelEn: 'Financial Damage', value: '银行和企业外债压力爆发，IMF 救助介入。', valueEn: 'Bank and corporate external-debt stress erupted, requiring IMF assistance.' },
      { label: '传染损害', labelEn: 'Contagion Damage', value: '风险外溢至俄罗斯违约和 LTCM 危机。', valueEn: 'Stress spilled into Russia default and the LTCM crisis.' },
    ],
  },
  '2000 互联网泡沫': {
    level: 3,
    label: '宏观衰退损害',
    labelEn: 'Macro Recession Damage',
    summary: '科技股泡沫破裂导致股市深度回撤、企业破产和美国经济衰退。',
    summaryEn: 'The tech bubble collapse caused deep equity losses, corporate failures, and US recession.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: '纳斯达克从高点下跌约 78%，S&P 500 下跌约 50%。', valueEn: 'Nasdaq fell roughly 78% and the S&P 500 fell roughly 50%.' },
      { label: '企业损害', labelEn: 'Corporate Damage', value: '安然、世通等企业丑闻和破产冲击信心。', valueEn: 'Enron, WorldCom and other corporate failures damaged confidence.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '美国进入 2001 年衰退。', valueEn: 'The US entered the 2001 recession.' },
    ],
  },
  '2008 全球金融危机': {
    level: 4,
    label: '系统性金融损害',
    labelEn: 'Systemic Financial Damage',
    summary: '银行、信用、房地产、就业和全球贸易同步受损，是现代系统性金融危机基准。',
    summaryEn: 'Banks, credit, housing, jobs, and global trade were damaged simultaneously, making this the benchmark modern systemic financial crisis.',
    metrics: [
      { label: '银行损害', labelEn: 'Banking Damage', value: '雷曼破产，Bear Stearns、AIG 等被救助或接管。', valueEn: 'Lehman failed while Bear Stearns, AIG and others required rescue or takeover.' },
      { label: '信用损害', labelEn: 'Credit Damage', value: '信用市场冻结，利差飙升。', valueEn: 'Credit markets froze and spreads surged.' },
      { label: '就业损害', labelEn: 'Labor Damage', value: '美国失业率升至约 10%。', valueEn: 'US unemployment rose to around 10%.' },
      { label: '政策损害', labelEn: 'Policy Damage', value: 'TARP、QE、零利率等非常规救助出台。', valueEn: 'TARP, QE, zero-rate policy and extraordinary support were deployed.' },
    ],
  },
  '2010 欧债危机': {
    level: 3,
    label: '宏观衰退损害',
    labelEn: 'Macro Recession Damage',
    summary: '主权信用、银行体系和欧元区增长受到实质损害，但未演化为全球系统性银行崩溃。',
    summaryEn: 'Sovereign credit, banks, and Eurozone growth suffered material damage, but it did not become a global banking collapse.',
    metrics: [
      { label: '主权信用损害', labelEn: 'Sovereign Credit Damage', value: '希腊、爱尔兰、葡萄牙、西班牙、意大利等出现主权压力。', valueEn: 'Greece, Ireland, Portugal, Spain, Italy and others came under sovereign stress.' },
      { label: '银行损害', labelEn: 'Banking Damage', value: '欧洲银行资本和融资压力上升。', valueEn: 'European banks faced higher capital and funding pressure.' },
      { label: '政策损害', labelEn: 'Policy Damage', value: '欧盟救助机制和 ECB 非常规承诺介入。', valueEn: 'EU rescue mechanisms and ECB extraordinary commitments were required.' },
    ],
  },
  '2015 中国股灾': {
    level: 2,
    label: '区域或市场损害',
    labelEn: 'Regional / Market Damage',
    summary: '中国股市和人民币冲击造成区域市场损害和全球风险偏好下行，但全球实体经济损害有限。',
    summaryEn: 'China equity and RMB shocks caused regional market damage and global risk-off pressure, but limited global real-economy damage.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: 'A 股从高点快速下跌并触发熔断。', valueEn: 'A-shares fell sharply from the peak and triggered circuit breakers.' },
      { label: '汇率损害', labelEn: 'FX Damage', value: '811 汇改后人民币贬值引发全球重定价。', valueEn: 'The August 11 RMB reform triggered depreciation and global repricing.' },
      { label: '传导损害', labelEn: 'Transmission Damage', value: '商品、港股、新兴市场风险偏好承压。', valueEn: 'Commodities, Hong Kong equities, and EM risk appetite came under pressure.' },
    ],
  },
  '2018 加息+圣诞暴跌': {
    level: 1,
    label: '市场调整',
    labelEn: 'Market Correction',
    summary: '主要损害集中在美股估值和风险偏好，经济没有进入深度衰退。',
    summaryEn: 'Damage was mainly equity valuation and risk appetite, without a deep recession.',
    metrics: [
      { label: '股市损害', labelEn: 'Equity Damage', value: 'S&P 500 接近熊市区间，科技股领跌。', valueEn: 'The S&P 500 neared bear-market territory, led by technology stocks.' },
      { label: '流动性损害', labelEn: 'Liquidity Damage', value: '加息和缩表导致金融条件收紧。', valueEn: 'Rate hikes and balance-sheet runoff tightened financial conditions.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '未造成明显宏观衰退。', valueEn: 'No clear macro recession resulted.' },
    ],
  },
  '2020 新冠恐慌': {
    level: 4,
    label: '系统性金融损害',
    labelEn: 'Systemic Financial Damage',
    summary: '疫情冲击导致全球停摆、市场熔断、就业骤降和政策极限救助，虽恢复较快但损害强度极高。',
    summaryEn: 'The pandemic caused global shutdowns, market circuit breakers, job losses, and extreme policy rescue. Recovery was fast, but damage intensity was severe.',
    metrics: [
      { label: '市场损害', labelEn: 'Market Damage', value: '全球股市熔断，VIX 升至 82。', valueEn: 'Global circuit breakers hit and VIX reached 82.' },
      { label: '就业损害', labelEn: 'Labor Damage', value: '美国失业率一度升至约 14.7%。', valueEn: 'US unemployment briefly rose to around 14.7%.' },
      { label: '经济损害', labelEn: 'Economic Damage', value: '全球经济活动骤停，服务业和贸易急剧收缩。', valueEn: 'Global activity stopped abruptly, with services and trade contracting sharply.' },
      { label: '政策损害', labelEn: 'Policy Damage', value: '零利率、无限 QE 和大规模财政救助同时启动。', valueEn: 'Zero rates, unlimited QE, and large fiscal support were launched together.' },
    ],
  },
  '2022 暴力加息': {
    level: 1,
    label: '市场调整',
    labelEn: 'Market Correction',
    summary: '损害主要集中在股债估值、美元融资和部分金融机构，经济损害相对滞后且不均衡。',
    summaryEn: 'Damage was concentrated in equity/bond valuation, dollar funding, and some financial institutions; real-economy damage was more lagged and uneven.',
    metrics: [
      { label: '股债损害', labelEn: 'Equity/Bond Damage', value: '股债双杀，长久期资产和科技股大幅回撤。', valueEn: 'Stocks and bonds sold off together; long-duration assets and technology shares fell sharply.' },
      { label: '汇率损害', labelEn: 'FX Damage', value: '美元大幅走强，新兴市场和非美货币承压。', valueEn: 'The dollar surged, pressuring EM and non-US currencies.' },
      { label: '金融损害', labelEn: 'Financial Damage', value: '英国养老金危机和 2023 年 SVB 暴露利率风险。', valueEn: 'The UK pension crisis and 2023 SVB failure exposed rate-risk fragility.' },
    ],
  },
}

function damageProfile(name: string): DamageProfile {
  return DAMAGE_PROFILES[name] || DEFAULT_DAMAGE_PROFILE
}

function damageLevel(name: string): number {
  return damageProfile(name).level
}

function damageMetrics(name: string): DamageMetric[] {
  return damageProfile(name).metrics
}

function damageBadgeStyle(name: string): Record<string, string> {
  const color = damageColor(damageLevel(name))
  return { background: color + '20', color }
}

function damageTextStyle(name: string): Record<string, string> {
  return { color: damageColor(damageLevel(name)) }
}

function damageLabel(profile: DamageProfile): string {
  return lang.value === 'zh' ? profile.label : profile.labelEn
}

function damageSummary(profile: DamageProfile): string {
  return lang.value === 'zh' ? profile.summary : profile.summaryEn
}

function damageMetricLabel(metric: DamageMetric): string {
  return lang.value === 'zh' ? metric.label : metric.labelEn
}

function damageMetricValue(metric: DamageMetric): string {
  return lang.value === 'zh' ? metric.value : metric.valueEn
}

function damageColor(level: number): string {
  if (level >= 5) return '#7f1d1d'
  if (level >= 4) return '#ef4444'
  if (level >= 3) return '#f97316'
  if (level >= 2) return '#fbbf24'
  if (level >= 1) return '#60a5fa'
  return '#34d399'
}

function backtestText(text: string): string {
  if (lang.value === 'zh') return text
  return BACKTEST_TEXT_EN[text] || tx(text)
}

onMounted(async () => {
  try {
    const res = await client.get('/risk-index/latest')
    currentGfcri.value = res.data?.gfcri_value || 0
  } catch {}
})

function alertColor(level: string): string {
  const map: Record<string, string> = {
    GREEN: '#34d399', YELLOW: '#fbbf24', ORANGE: '#f97316', RED: '#ef4444',
  }
  return map[level] || '#6b7280'
}

function alertTextStyle(level: string): Record<string, string> {
  return { color: alertColor(level) }
}

const currentColor = computed(() => {
  const v = currentGfcri.value
  if (v >= 75) return '#ef4444'
  if (v >= 50) return '#f97316'
  if (v >= 25) return '#fbbf24'
  return '#34d399'
})

const topCrises = computed(() => {
  return crises.filter(c => c.peakGfcri >= 55).map(c => ({
    ...c,
    shortName: c.name.replace(/\d{4}\s*/, '').substring(0, 6),
  }))
})

const exceededCount = computed(() => {
  return crises.filter(c => currentGfcri.value > c.peakGfcri).length
})

const closestCrisis = computed(() => {
  const sorted = [...crises].sort((a, b) =>
    Math.abs(a.peakGfcri - currentGfcri.value) - Math.abs(b.peakGfcri - currentGfcri.value)
  )
  return sorted[0]?.name ? tx(sorted[0].name) : '—'
})

const crises = [
  {
    name: '1929 大萧条', year: '1929-33', peakGfcri: 75.5, peakAlert: 'RED', leadMonths: 16,
    description: '华尔街崩盘→银行连环倒闭→全球经济崩溃→失业率25%',
    timeline: [
      { date: '1928-06', gfcri: 31.0, alert: 'YELLOW', event: '首次预警，比崩盘早 16 个月', isPeak: false },
      { date: '1929-09', gfcri: 20.2, alert: 'GREEN', event: '道琼斯见顶 362（泡沫顶峰）', isPeak: false },
      { date: '1929-11', gfcri: 27.2, alert: 'YELLOW', event: '道琼斯一月跌 37%', isPeak: false },
      { date: '1930-12', gfcri: 51.5, alert: 'ORANGE', event: '合众国银行倒闭，信用利差飙升', isPeak: false },
      { date: '1931-09', gfcri: 61.6, alert: 'ORANGE', event: '英镑脱离金本位，全球传染', isPeak: false },
      { date: '1932-05', gfcri: 75.5, alert: 'RED', event: '失业 22.3%，道琼斯 52，信用利差 5.64%', isPeak: true },
      { date: '1933-03', gfcri: 61.1, alert: 'ORANGE', event: '罗斯福就任，全国银行关门', isPeak: false },
      { date: '1935-12', gfcri: 38.6, alert: 'YELLOW', event: '经济部分恢复，失业仍 16.4%', isPeak: false },
    ],
  },
  {
    name: '1971 尼克松冲击', year: '1971', peakGfcri: 71.0, peakAlert: 'ORANGE', leadMonths: 19,
    description: '布雷顿森林体系崩溃，美元与黄金脱钩，全球货币秩序重塑',
    timeline: [
      { date: '1970-01', gfcri: 71.0, alert: 'ORANGE', event: '首次预警，美国衰退开始', isPeak: true },
      { date: '1970-06', gfcri: 81.6, alert: 'RED', event: '经济衰退深化', isPeak: false },
      { date: '1971-05', gfcri: 72.5, alert: 'ORANGE', event: '西德马克浮动，美元危机', isPeak: false },
      { date: '1971-08', gfcri: 65.7, alert: 'ORANGE', event: '尼克松关闭黄金窗口', isPeak: false },
      { date: '1971-12', gfcri: 73.9, alert: 'ORANGE', event: '史密森协议，美元贬值 8%', isPeak: false },
      { date: '1972-06', gfcri: 69.1, alert: 'ORANGE', event: '英镑浮动', isPeak: false },
    ],
  },
  {
    name: '1973 石油危机', year: '1973-75', peakGfcri: 67.7, peakAlert: 'ORANGE', leadMonths: 10,
    description: 'OPEC 石油禁运→油价翻4倍→全球滞胀→SPX 暴跌 48%',
    timeline: [
      { date: '1973-11', gfcri: 34.9, alert: 'YELLOW', event: '首次预警，OPEC 禁运后', isPeak: false },
      { date: '1974-01', gfcri: 38.2, alert: 'YELLOW', event: '油价翻倍冲击实体经济', isPeak: false },
      { date: '1974-03', gfcri: 41.5, alert: 'YELLOW', event: '石油禁运解除但油价不降', isPeak: false },
      { date: '1974-07', gfcri: 55.5, alert: 'ORANGE', event: '通胀失控，经济衰退', isPeak: false },
      { date: '1974-08', gfcri: 67.7, alert: 'ORANGE', event: '尼克松辞职，SPX 接近底部', isPeak: true },
      { date: '1974-09', gfcri: 64.3, alert: 'ORANGE', event: 'SPX 见底，跌幅 48%', isPeak: false },
      { date: '1975-03', gfcri: 28.0, alert: 'YELLOW', event: '经济开始复苏', isPeak: false },
    ],
  },
  {
    name: '1980 沃尔克紧缩', year: '1980-82', peakGfcri: 41.3, peakAlert: 'YELLOW', leadMonths: 31,
    description: '联邦基金利率升至 20%→深度衰退→拉美债务危机',
    timeline: [
      { date: '1980-01', gfcri: 32.3, alert: 'YELLOW', event: '首次预警，利率升至 14%', isPeak: false },
      { date: '1980-03', gfcri: 38.0, alert: 'YELLOW', event: '利率达 20% 历史纪录', isPeak: false },
      { date: '1980-11', gfcri: 41.3, alert: 'YELLOW', event: '二次探底开始', isPeak: true },
      { date: '1981-07', gfcri: 37.5, alert: 'YELLOW', event: '经济二次衰退', isPeak: false },
      { date: '1982-06', gfcri: 35.0, alert: 'YELLOW', event: '失业率破 10%', isPeak: false },
      { date: '1982-08', gfcri: 33.0, alert: 'YELLOW', event: '墨西哥债务违约', isPeak: false },
      { date: '1982-10', gfcri: 25.0, alert: 'YELLOW', event: '美联储转向宽松', isPeak: false },
    ],
  },
  {
    name: '1987 黑色星期一', year: '1987', peakGfcri: 27.6, peakAlert: 'YELLOW', leadMonths: 7,
    description: '单日暴跌 22.6%，史上最大单日跌幅（月度数据难捕捉闪崩）',
    timeline: [
      { date: '1987-03', gfcri: 26.3, alert: 'YELLOW', event: '首次预警，股市过热', isPeak: false },
      { date: '1987-04', gfcri: 27.6, alert: 'YELLOW', event: '模型峰值（月度颗粒度限制）', isPeak: true },
      { date: '1987-08', gfcri: 21.0, alert: 'GREEN', event: '道指见顶 2722', isPeak: false },
      { date: '1987-10', gfcri: 24.0, alert: 'GREEN', event: '黑色星期一（月内事件）', isPeak: false },
      { date: '1988-01', gfcri: 18.0, alert: 'GREEN', event: '美联储注入流动性，恢复', isPeak: false },
    ],
  },
  {
    name: '1992 ERM 危机', year: '1992', peakGfcri: 25.6, peakAlert: 'YELLOW', leadMonths: 2,
    description: '索罗斯做空英镑，欧洲汇率机制崩溃（区域性危机，对全球冲击有限）',
    timeline: [
      { date: '1992-06', gfcri: 30.4, alert: 'YELLOW', event: '芬兰马克贬值，ERM 压力初现', isPeak: false },
      { date: '1992-07', gfcri: 35.5, alert: 'YELLOW', event: 'GFCRI 峰值，预示危机加剧', isPeak: true },
      { date: '1992-09', gfcri: 32.4, alert: 'YELLOW', event: '黑色星期三，英镑退出 ERM', isPeak: false },
      { date: '1992-11', gfcri: 30.0, alert: 'YELLOW', event: '瑞典放弃固定汇率', isPeak: false },
      { date: '1993-01', gfcri: 31.8, alert: 'YELLOW', event: '爱尔兰镑贬值 10%', isPeak: false },
    ],
  },
  {
    name: '1994 全球债市大屠杀', year: '1994', peakGfcri: 42.2, peakAlert: 'YELLOW', leadMonths: 10,
    description: '美联储意外加息引发全球债券抛售 + 橙县破产 + 墨西哥比索危机',
    timeline: [
      { date: '1994-01', gfcri: 34.0, alert: 'YELLOW', event: '预警触发，比峰值早 10 个月', isPeak: false },
      { date: '1994-02', gfcri: 32.3, alert: 'YELLOW', event: '美联储意外加息 25bp', isPeak: false },
      { date: '1994-03', gfcri: 42.2, alert: 'YELLOW', event: 'VIX 飙升至 20.5，全球债市恐慌', isPeak: true },
      { date: '1994-06', gfcri: 32.8, alert: 'YELLOW', event: '墨西哥政治暗杀，比索承压', isPeak: false },
      { date: '1994-11', gfcri: 30.9, alert: 'YELLOW', event: '橙县因衍生品亏损破产', isPeak: false },
      { date: '1994-12', gfcri: 30.4, alert: 'YELLOW', event: '墨西哥比索危机爆发', isPeak: false },
    ],
  },
  {
    name: '1997 亚洲金融危机', year: '1997-98', peakGfcri: 58.1, peakAlert: 'ORANGE', leadMonths: 12,
    description: '泰铢崩盘→韩元崩盘→俄罗斯违约→LTCM 崩盘',
    timeline: [
      { date: '1997-01', gfcri: 37.2, alert: 'YELLOW', event: '预警触发，比峰值早 12 个月', isPeak: false },
      { date: '1997-07', gfcri: 34.3, alert: 'YELLOW', event: '泰铢崩盘，亚洲危机起点', isPeak: false },
      { date: '1997-10', gfcri: 49.7, alert: 'YELLOW', event: '港股暴跌，全球传染', isPeak: false },
      { date: '1997-11', gfcri: 38.2, alert: 'YELLOW', event: '韩元崩盘，IMF 介入', isPeak: false },
      { date: '1998-08', gfcri: 58.1, alert: 'ORANGE', event: '俄罗斯违约 → LTCM 崩盘', isPeak: true },
      { date: '1998-10', gfcri: 40.8, alert: 'YELLOW', event: '美联储紧急降息', isPeak: false },
    ],
  },
  {
    name: '2000 互联网泡沫', year: '2000-02', peakGfcri: 59.2, peakAlert: 'ORANGE', leadMonths: 33,
    description: '纳斯达克崩盘→安然/世通→SPX 跌 50%',
    timeline: [
      { date: '2000-01', gfcri: 30.1, alert: 'YELLOW', event: '预警触发，比峰值早 33 个月', isPeak: false },
      { date: '2000-04', gfcri: 33.3, alert: 'YELLOW', event: '科技股闪崩，纳斯达克单周跌 25%', isPeak: false },
      { date: '2001-03', gfcri: 46.2, alert: 'YELLOW', event: '美国经济正式衰退', isPeak: false },
      { date: '2001-09', gfcri: 52.0, alert: 'ORANGE', event: '911 恐怖袭击，首次橙色', isPeak: false },
      { date: '2002-07', gfcri: 48.9, alert: 'YELLOW', event: 'WorldCom 会计丑闻', isPeak: false },
      { date: '2002-09', gfcri: 59.2, alert: 'ORANGE', event: 'SPX 见底 815', isPeak: true },
    ],
  },
  {
    name: '2008 全球金融危机', year: '2007-09', peakGfcri: 83.8, peakAlert: 'RED', leadMonths: 14,
    description: '次贷→Bear Stearns→雷曼→全球系统性崩溃（含隐藏风险修正）',
    timeline: [
      { date: '2007-07', gfcri: 34.3, alert: 'YELLOW', event: '首次预警：信用利差异动，比雷曼早 14 个月', isPeak: false },
      { date: '2007-08', gfcri: 37.2, alert: 'YELLOW', event: 'BNP 冻结3只基金，TED利差飙至1.71%', isPeak: false },
      { date: '2007-11', gfcri: 36.1, alert: 'YELLOW', event: '信用利差持续走阔，银行间信任未恢复', isPeak: false },
      { date: '2008-01', gfcri: 40.4, alert: 'YELLOW', event: '全球股市暴跌，美联储紧急降息75bp', isPeak: false },
      { date: '2008-03', gfcri: 45.0, alert: 'YELLOW', event: '🏛️ Bear Stearns 被收购，美联储周日紧急行动（隐藏信号：政策力度>>市场反应）', isPeak: false },
      { date: '2008-04', gfcri: 45.0, alert: 'YELLOW', event: '⚡ "假平静"：VIX降到20但BAA利差3.1%不退，银行股反弹仅大盘1/3', isPeak: false },
      { date: '2008-06', gfcri: 50.4, alert: 'ORANGE', event: '⚡ 隐藏风险升级：信用分化加速+美联储资产负债表异常扩张', isPeak: false },
      { date: '2008-07', gfcri: 51.3, alert: 'ORANGE', event: '🏛️ IndyMac倒闭（储蓄银行→零售端蔓延），政策力度持续加码', isPeak: false },
      { date: '2008-08', gfcri: 53.4, alert: 'ORANGE', event: '⚡ VIX=20.6"正常"但4个隐藏信号亮起：政策异常+信用分化+银行背离+避险买盘', isPeak: false },
      { date: '2008-09', gfcri: 65.2, alert: 'ORANGE', event: '💥 雷曼破产（9/15），隐藏风险全面暴露，所有侧面信号验证为真', isPeak: false },
      { date: '2008-10', gfcri: 83.8, alert: 'RED', event: '恐慌顶点 VIX=59.9，🏛️ TARP 7000亿被否决→通过', isPeak: true },
      { date: '2008-11', gfcri: 75.4, alert: 'RED', event: '🏛️ 美联储QE1（1.75万亿），信用利差开始见顶', isPeak: false },
      { date: '2009-03', gfcri: 58.2, alert: 'ORANGE', event: 'SPX见底666，信用利差回落确认恢复开始', isPeak: false },
    ],
  },
  {
    name: '2010 欧债危机', year: '2010-12', peakGfcri: 58.6, peakAlert: 'ORANGE', leadMonths: 22,
    description: '希腊→爱尔兰→意大利→"Whatever it takes"',
    timeline: [
      { date: '2010-01', gfcri: 32.6, alert: 'YELLOW', event: '预警触发，比峰值早 22 个月', isPeak: false },
      { date: '2010-04', gfcri: 30.6, alert: 'YELLOW', event: '希腊正式求助 EU/IMF', isPeak: false },
      { date: '2010-05', gfcri: 36.0, alert: 'YELLOW', event: '欧盟 7500 亿救助', isPeak: false },
      { date: '2011-08', gfcri: 42.6, alert: 'YELLOW', event: '美国信用评级下调', isPeak: false },
      { date: '2011-09', gfcri: 58.6, alert: 'ORANGE', event: '意大利 10Y 突破 7%', isPeak: true },
      { date: '2012-07', gfcri: 27.0, alert: 'YELLOW', event: '德拉吉：Whatever it takes', isPeak: false },
    ],
  },
  {
    name: '2015 中国股灾', year: '2015-16', peakGfcri: 38.8, peakAlert: 'YELLOW', leadMonths: 5,
    description: 'A 股暴跌→811 汇改→人民币贬值→全球恐慌→熔断',
    timeline: [
      { date: '2015-06', gfcri: 20.6, alert: 'GREEN', event: 'A 股见顶 5178', isPeak: false },
      { date: '2015-08', gfcri: 38.8, alert: 'YELLOW', event: '811 汇改，人民币贬值 2%，全球恐慌', isPeak: true },
      { date: '2015-09', gfcri: 38.2, alert: 'YELLOW', event: '全球股市恐慌性抛售', isPeak: false },
      { date: '2016-01', gfcri: 28.7, alert: 'YELLOW', event: 'A 股熔断，全球暴跌', isPeak: false },
    ],
  },
  {
    name: '2018 加息+圣诞暴跌', year: '2018', peakGfcri: 36.7, peakAlert: 'YELLOW', leadMonths: 11,
    description: '美联储加息→中美贸易战→VIX 闪崩→圣诞暴跌',
    timeline: [
      { date: '2018-01', gfcri: 27.9, alert: 'YELLOW', event: '预警触发，比峰值早 11 个月', isPeak: false },
      { date: '2018-02', gfcri: 26.3, alert: 'YELLOW', event: 'VIX 暴涨到 50+，闪崩事件', isPeak: false },
      { date: '2018-03', gfcri: 26.9, alert: 'YELLOW', event: '中美贸易战开打', isPeak: false },
      { date: '2018-10', gfcri: 25.3, alert: 'YELLOW', event: '美股暴跌，科技股领跌', isPeak: false },
      { date: '2018-12', gfcri: 36.7, alert: 'YELLOW', event: 'SPX 进入熊市，圣诞暴跌', isPeak: true },
      { date: '2019-01', gfcri: 18.7, alert: 'GREEN', event: '美联储转鸽，市场反弹', isPeak: false },
    ],
  },
  {
    name: '2020 新冠恐慌', year: '2020', peakGfcri: 64.4, peakAlert: 'ORANGE', leadMonths: 0,
    description: '全球熔断→VIX=82→无限 QE→V 型反弹',
    timeline: [
      { date: '2020-01', gfcri: 21.6, alert: 'GREEN', event: '武汉封城，市场初步反应', isPeak: false },
      { date: '2020-02', gfcri: 35.6, alert: 'YELLOW', event: '疫情全球扩散，恐慌开始', isPeak: false },
      { date: '2020-03', gfcri: 64.4, alert: 'ORANGE', event: '全球熔断，VIX=82，美联储无限 QE', isPeak: true },
      { date: '2020-04', gfcri: 32.5, alert: 'YELLOW', event: '油价负值，但股市开始反弹', isPeak: false },
      { date: '2020-06', gfcri: 23.7, alert: 'GREEN', event: 'V 型反弹确认', isPeak: false },
    ],
  },
  {
    name: '2022 暴力加息', year: '2022-23', peakGfcri: 37.9, peakAlert: 'YELLOW', leadMonths: 8,
    description: '美联储激进加息→强美元→英国养老金危机→SVB 倒闭',
    timeline: [
      { date: '2022-02', gfcri: 34.2, alert: 'YELLOW', event: '预警触发，比峰值早 8 个月', isPeak: false },
      { date: '2022-04', gfcri: 37.6, alert: 'YELLOW', event: '俄乌冲突叠加加息', isPeak: false },
      { date: '2022-06', gfcri: 36.4, alert: 'YELLOW', event: '加息 75bp，四十年最大幅度', isPeak: false },
      { date: '2022-09', gfcri: 37.9, alert: 'YELLOW', event: '英国养老金危机，SPX 见底', isPeak: true },
      { date: '2023-03', gfcri: 20.1, alert: 'GREEN', event: '硅谷银行倒闭', isPeak: false },
    ],
  },
]

const peakChartOption = computed(() => {
  const sorted = [...crises].sort((a, b) => a.peakGfcri - b.peakGfcri)
  return {
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#111214',
      borderColor: 'rgba(255,255,255,0.06)',
      textStyle: { color: '#eff1f5', fontSize: 12 },
    },
    grid: { left: 160, right: 60, top: 10, bottom: 30 },
    xAxis: {
      type: 'value', max: 100,
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.04)' } },
      axisLabel: { color: '#6b7280', fontSize: 11 },
    },
    yAxis: {
      type: 'category',
      data: sorted.map(c => tx(c.name)),
      axisLabel: { color: '#eff1f5', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    series: [{
      type: 'bar',
      data: sorted.map(c => ({
        value: c.peakGfcri,
        itemStyle: {
          color: c.peakGfcri >= 75 ? '#ef4444'
            : c.peakGfcri >= 50 ? '#f97316'
            : c.peakGfcri >= 25 ? '#fbbf24'
            : '#34d399',
          borderRadius: [0, 4, 4, 0],
        },
      })),
      barWidth: 18,
      label: {
        show: true, position: 'right',
        color: '#6b7280', fontSize: 11,
        formatter: (p: any) => p.value.toFixed(1),
      },
    }],
  }
})
</script>
