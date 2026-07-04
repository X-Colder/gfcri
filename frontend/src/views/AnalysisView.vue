<template>
  <div>
    <LoadingSpinner v-if="riskStore.loading && !riskStore.latest" />

    <template v-else-if="riskStore.latest">

      <!-- Section 1: Judgment -->
      <div class="mb-12 fade-in">
        <div v-if="riskStore.latest" class="min-w-0">
          <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">AI Analysis</p>
          <h2 class="text-lg font-light text-white mb-6">{{ t("analysis.aiTitle") }}</h2>
          <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6 lg:p-7 card-hover">
            <div v-if="isPro" class="prose prose-invert prose-sm max-w-none judgment-markdown" v-html="renderedNarrative"></div>
            <div v-else>
              <div class="prose prose-invert prose-sm max-w-none judgment-markdown" v-html="truncatedNarrative"></div>
              <div class="relative mt-4">
                <div class="h-20 bg-gradient-to-b from-transparent to-[var(--card)]"></div>
                <div class="text-center -mt-8">
                  <span class="text-xs text-[var(--accent)]">{{ t("analysis.upgradeHint") }}</span>
                </div>
              </div>
            </div>

            <div class="judgment-workbench">
              <div class="explain-grid">
                <div v-for="card in todayEvidenceCards" :key="card.id" class="explain-card">
                  <div class="explain-card-head">
                    <p>{{ card.kicker }}</p>
                    <strong>{{ card.value }}</strong>
                  </div>
                  <h3>{{ card.title }}</h3>
                  <p>{{ card.body }}</p>
                  <div class="evidence-actions">
                    <button type="button" @click="scrollToSection(card.target)">
                      {{ card.action }}
                    </button>
                    <button v-if="card.watchType && card.watchId" type="button" @click="toggleWatchCard(card)">
                      {{ isWatched(card.watchType, card.watchId) ? t('watch.done') : t('analysis.addToWatch') }}
                    </button>
                  </div>
                </div>
              </div>

              <div class="action-workbench">
                <div class="action-panel">
                  <div class="action-head">
                    <div>
                      <p class="text-[10px] uppercase tracking-[3px] text-[var(--muted)]">{{ t('analysis.actionPanel') }}</p>
                      <h3>{{ t('analysis.watchlistTitle') }}</h3>
                    </div>
                    <span>{{ watchItems.length }} {{ t('analysis.watched') }}</span>
                  </div>
                  <p class="terminal-copy mt-2">{{ t('analysis.watchlistDesc') }}</p>
                  <div class="watch-chip-grid">
                    <button v-for="item in watchActionItems" :key="item.id" type="button"
                            class="watch-chip"
                            :class="{ 'watch-chip-active': isIndicatorWatched(item.id) }"
                            @click="toggleIndicatorWatch(item.id)">
                      <span>{{ item.name }}</span>
                      <small>{{ item.reason }}</small>
                    </button>
                  </div>
                </div>

                <div class="action-panel">
                  <div class="action-head">
                    <div>
                      <p class="text-[10px] uppercase tracking-[3px] text-[var(--muted)]">{{ t('analysis.fastAccess') }}</p>
                      <h3>{{ selectedWatchItem?.name || t('analysis.selectIndicator') }}</h3>
                    </div>
                    <button type="button" class="plain-link" @click="scrollToSection('node-contribution')">
                      {{ t('analysis.openDataDetail') }}
                    </button>
                  </div>
                  <div v-if="selectedWatchItem" class="indicator-detail">
                    <div class="indicator-metrics">
                      <div>
                        <span>{{ t('analysis.current') }}</span>
                        <strong>{{ selectedWatchItem.currentDisplay }}</strong>
                      </div>
                      <div>
                        <span>{{ t('analysis.zscore') }}</span>
                        <strong>{{ selectedWatchItem.zscoreDisplay }}</strong>
                      </div>
                      <div>
                        <span>{{ t('analysis.absScore') }}</span>
                        <strong>{{ selectedWatchItem.absScoreDisplay }}</strong>
                      </div>
                    </div>
                    <v-chart v-if="selectedWatchTrend.length > 1" :option="selectedWatchTrendOption" style="height: 180px" autoresize />
                    <p v-else class="terminal-copy mt-3">{{ t('analysis.noIndicatorTrend') }}</p>
                    <div class="related-chain-list" v-if="selectedWatchRelatedChains.length">
                      <button v-for="chain in selectedWatchRelatedChains" :key="chain.id" type="button" @click="openChainDetail(chain.id)">
                        {{ chain.name }} · {{ t('analysis.stress') }} {{ chain.stress.toFixed(0) }}
                      </button>
                    </div>
                  </div>
                  <p v-else class="terminal-copy mt-3">{{ t('analysis.selectIndicatorHint') }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="lang === 'en'" class="mb-12 fade-in bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Alert Beta</p>
            <h2 class="text-base font-medium text-white">{{ t('forward.alertSub') }}</h2>
            <p class="terminal-copy mt-1">{{ t('forward.alertDesc') }}</p>
          </div>
          <div v-if="!subscribed" class="flex w-full gap-2 lg:max-w-sm">
            <input v-model="alertEmail" type="email" placeholder="your@email.com"
                   class="min-w-0 flex-1 px-4 py-2.5 rounded-lg bg-[var(--bg)] border border-[var(--border)] text-white text-sm focus:border-[var(--accent)] focus:outline-none" />
            <button @click="subscribe"
                    class="px-4 py-2.5 rounded-lg bg-[var(--accent)] text-white text-sm font-medium hover:bg-[var(--accent)]/80 transition-colors">
              {{ t('common.subscribe') }}
            </button>
          </div>
          <p v-else class="text-sm text-[var(--green)]">✓ {{ t('forward.subscribed') }} {{ alertEmail }}</p>
        </div>
      </div>

      <!-- Section 2: Model Logic Breakdown -->
      <div class="mb-12 fade-in fade-in-delay-1">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Model Explainability</p>
        <h2 class="text-lg font-light text-white mb-6">{{ t('analysis.modelLogic') }}</h2>

        <CrisisRegimePanel class="mb-5" />

        <CausalDiscoveryPanel class="mb-5" />

        <div id="hidden-risk-section" class="mb-5 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover">
          <div class="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
            <div class="max-w-3xl">
              <div class="flex items-center gap-3">
                <p class="text-sm text-white font-medium">{{ t('analysis.hiddenRisk') }}</p>
                <span class="px-2 py-0.5 rounded-full border text-[10px] font-mono"
                      :style="{ color: hiddenRiskColor, borderColor: hiddenRiskColor, backgroundColor: hiddenRiskColor + '18' }">
                  {{ hiddenRisk.statusLabel }}
                </span>
              </div>
              <p class="terminal-copy mt-2">{{ t('analysis.hiddenRiskDesc') }}</p>
              <p class="text-xs text-[var(--muted)] mt-3">{{ hiddenRisk.primaryDetail }}</p>
            </div>
            <div class="grid grid-cols-2 gap-3 sm:grid-cols-4 xl:min-w-[460px]">
              <div class="terminal-metric">
                <span>{{ t('analysis.undercurrentBoost') }}</span>
                <strong :style="{ color: hiddenRiskColor }">+{{ hiddenRisk.undercurrent.toFixed(1) }}</strong>
              </div>
              <div class="terminal-metric">
                <span>{{ t('analysis.surfaceStress') }}</span>
                <strong>{{ hiddenRisk.surfaceAvgDisplay }}</strong>
              </div>
              <div class="terminal-metric">
                <span>{{ t('analysis.deepStress') }}</span>
                <strong>{{ hiddenRisk.deepAvgDisplay }}</strong>
              </div>
              <div class="terminal-metric">
                <span>{{ t('analysis.gap') }}</span>
                <strong>{{ hiddenRisk.gapDisplay }}</strong>
              </div>
            </div>
          </div>

          <div class="mt-4 grid gap-3 lg:grid-cols-2" v-if="hiddenRisk.items.length">
            <div v-for="item in hiddenRisk.items" :key="item.title" class="rounded-lg border border-[var(--border)] bg-white/[0.015] p-3">
              <p class="text-xs text-white font-medium">{{ item.title }}</p>
              <p class="text-[11px] text-[var(--muted)] leading-relaxed mt-1">{{ item.detail }}</p>
            </div>
          </div>
          <p v-else class="mt-4 text-xs text-[var(--muted)]">{{ t('analysis.hiddenNone') }}</p>
          <p class="mt-4 text-[11px] text-[var(--accent)]">{{ t('analysis.hiddenWhyPro') }}</p>
        </div>

        <TradeSpilloverPanel class="mb-5" />

        <div class="grid gap-5 xl:grid-cols-[minmax(0,1.05fr)_minmax(360px,0.95fr)]">
          <div id="sub-index-breakdown" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4 lg:p-5 card-hover min-w-0">
            <div class="flex items-center justify-between mb-3">
              <p class="text-sm text-white font-medium">{{ t('analysis.subIndexBreakdown') }}</p>
              <span class="text-[10px] text-[var(--muted)] font-mono">{{ t('dash.coherence') }} {{ (riskStore.latest.coherence_multiplier || 1).toFixed(2) }}x</span>
            </div>
            <v-chart :option="subIndexBreakdownOption" style="height: 320px" autoresize />
            <div class="receipt-tabs">
              <button v-for="row in subIndexRows" :key="row.id" type="button"
                      :class="{ 'receipt-tab-active': selectedSubIndexId === row.id }"
                      @click="selectedSubIndexId = row.id">
                {{ row.name }}
              </button>
            </div>
            <div v-if="selectedSubIndexReceipt" class="formula-receipt">
              <div class="formula-receipt-head">
                <div>
                  <p>{{ t('analysis.formulaReceipt') }}</p>
                  <h3>{{ selectedSubIndexReceipt.name }} · {{ selectedSubIndexReceipt.score.toFixed(1) }}</h3>
                </div>
                <span>{{ t('analysis.sourceTier') }} {{ sourceTierSummaryText(selectedSubIndexReceipt.source_tier_summary) }}</span>
              </div>
              <div class="formula-steps">
                <div>
                  <span>{{ t('analysis.anomalyStress') }}</span>
                  <strong>{{ (selectedSubIndexReceipt.mean_stress * 100).toFixed(1) }}</strong>
                </div>
                <div>
                  <span>{{ t('analysis.absoluteStress') }}</span>
                  <strong>{{ (selectedSubIndexReceipt.mean_abs_stress * 100).toFixed(1) }}</strong>
                </div>
                <div>
                  <span>{{ t('analysis.transmissionAmp') }}</span>
                  <strong>{{ (selectedSubIndexReceipt.transmission * 100).toFixed(1) }}</strong>
                </div>
              </div>
              <p class="formula-text">{{ selectedSubIndexReceipt.formula }}</p>
              <div class="receipt-node-table">
                <div class="receipt-node-row receipt-node-head">
                  <span>{{ t('analysis.node') }}</span>
                  <span>{{ t('analysis.current') }}</span>
                  <span>{{ t('analysis.zscore') }}</span>
                  <span>{{ t('analysis.absScore') }}</span>
                  <span>{{ t('analysis.sourceTier') }}</span>
                </div>
                <div v-for="node in selectedSubIndexReceipt.nodes" :key="node.node_id" class="receipt-node-row">
                  <span>{{ tx(node.display_name) }}</span>
                  <span>{{ formatCurrentValue(node.current_value) }}</span>
                  <span>{{ node.zscore === null || node.zscore === undefined ? '-' : Number(node.zscore).toFixed(2) }}</span>
                  <span>{{ node.abs_score === null || node.abs_score === undefined ? '-' : (Number(node.abs_score) * 100).toFixed(0) }}</span>
                  <span :class="'tier-' + node.source_tier">{{ node.source_tier }}</span>
                </div>
              </div>
              <p v-if="selectedSubIndexReceipt.limitations.length" class="formula-limit">
                {{ selectedSubIndexReceipt.limitations[0] }}
              </p>
            </div>
          </div>

          <div id="node-contribution" class="bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden card-hover min-w-0">
            <div class="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
              <p class="text-sm text-white font-medium">{{ t('analysis.nodeContribution') }}</p>
              <span class="text-[10px] text-[var(--muted)] font-mono">Top {{ topNodeContributions.length }}</span>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-[var(--muted)] border-b border-[var(--border)]">
                    <th class="text-left px-5 py-2 font-medium">{{ t('analysis.node') }}</th>
                    <th class="text-right px-3 py-2 font-medium">{{ t('analysis.zscore') }}</th>
                    <th class="text-right px-3 py-2 font-medium">{{ t('analysis.absScore') }}</th>
                    <th class="text-right px-5 py-2 font-medium">{{ t('analysis.current') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="node in topNodeContributions" :key="node.id" class="border-b border-[var(--border)]/40 hover:bg-white/[0.02]">
                    <td class="px-5 py-2.5 text-white whitespace-nowrap">{{ node.name }}</td>
                    <td class="px-3 py-2.5 text-right font-mono" :style="{ color: Math.abs(node.zscore) >= 2 ? 'var(--red)' : 'var(--muted)' }">{{ node.zscore.toFixed(2) }}</td>
                    <td class="px-3 py-2.5 text-right font-mono">{{ node.absScoreDisplay }}</td>
                    <td class="px-5 py-2.5 text-right font-mono text-[var(--muted)]">{{ node.currentDisplay }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div id="chain-pressure" class="mt-5 bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden card-hover">
          <div class="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
            <p class="text-sm text-white font-medium">{{ t('analysis.chainPressure') }}</p>
            <span class="text-[10px] text-[var(--muted)] font-mono">{{ activeChains.length }} {{ t('analysis.chainActive') }}</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-xs">
              <thead>
                <tr class="text-[var(--muted)] border-b border-[var(--border)]">
                  <th class="text-left px-5 py-2 font-medium">{{ t('analysis.chain') }}</th>
                  <th class="text-left px-3 py-2 font-medium">{{ t('common.path') }}</th>
                  <th class="text-right px-3 py-2 font-medium">{{ t('analysis.stress') }}</th>
                  <th class="text-right px-5 py-2 font-medium">{{ t('analysis.pathStrength') }}</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="chain in chainPressureRows" :key="chain.id">
                <tr class="border-b border-[var(--border)]/40 hover:bg-white/[0.02] cursor-pointer" @click="toggleChainDetail(chain.id)">
                  <td class="px-5 py-2.5 text-white whitespace-nowrap">
                    <span class="mr-2 text-[10px] text-[var(--muted)]">{{ expandedChainId === chain.id ? '▼' : '▶' }}</span>
                    {{ chain.name }}
                  </td>
                  <td class="px-3 py-2.5 text-[var(--muted)] min-w-[280px]">{{ chain.path }}</td>
                  <td class="px-3 py-2.5 text-right">
                    <div class="inline-flex items-center gap-2 min-w-[110px] justify-end">
                      <div class="h-1.5 w-16 bg-white/[0.05] rounded-full overflow-hidden">
                        <div class="h-full rounded-full" :style="{ width: Math.min(chain.stress, 100) + '%', backgroundColor: scoreColor(chain.stress) }"></div>
                      </div>
                      <span class="font-mono" :style="{ color: scoreColor(chain.stress) }">{{ chain.stress.toFixed(0) }}</span>
                    </div>
                  </td>
                  <td class="px-5 py-2.5 text-right font-mono text-[var(--muted)]">{{ chain.pathStrength }}</td>
                </tr>
                <tr v-if="expandedChainId === chain.id" class="border-b border-[var(--border)] bg-white/[0.012]">
                  <td colspan="4" class="px-5 py-5">
                    <div class="grid gap-4 xl:grid-cols-2">
                      <div class="space-y-4">
                        <div>
                          <p class="text-[11px] uppercase tracking-[3px] text-[var(--muted)] mb-2">{{ t('analysis.stressFormula') }}</p>
                          <p class="text-xs text-[var(--muted)] leading-relaxed">{{ chain.stressFormula }}</p>
                        </div>
                        <div>
                          <p class="text-[11px] uppercase tracking-[3px] text-[var(--muted)] mb-2">{{ t('analysis.pathFormula') }}</p>
                          <p class="text-xs text-[var(--muted)] leading-relaxed">{{ chain.pathFormula }}</p>
                        </div>
                        <div v-if="chain.edgeDetails.length">
                          <p class="text-[11px] uppercase tracking-[3px] text-[var(--muted)] mb-2">{{ t('analysis.edgeStrengths') }}</p>
                          <div class="flex flex-wrap gap-2">
                            <span v-for="edge in chain.edgeDetails" :key="edge" class="px-2 py-1 rounded border border-[var(--border)] text-[10px] font-mono text-[var(--muted)]">{{ edge }}</span>
                          </div>
                        </div>
                      </div>
                      <div class="overflow-x-auto">
                        <p class="text-[11px] uppercase tracking-[3px] text-[var(--muted)] mb-2">{{ t('analysis.nodeContribution') }}</p>
                        <table class="w-full text-xs">
                          <thead>
                            <tr class="text-[var(--muted)] border-b border-[var(--border)]">
                              <th class="text-left py-2 pr-3">{{ t('analysis.node') }}</th>
                              <th class="text-right py-2 px-3">{{ t('analysis.current') }}</th>
                              <th class="text-right py-2 px-3">{{ t('analysis.zscore') }}</th>
                              <th class="text-right py-2 px-3">{{ t('analysis.anomalyScore') }}</th>
                              <th class="text-right py-2 pl-3">{{ t('analysis.absScore') }}</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="node in chain.nodes" :key="node.id" class="border-b border-[var(--border)]/40">
                              <td class="py-2 pr-3 text-white whitespace-nowrap">{{ node.name }}</td>
                              <td class="py-2 px-3 text-right font-mono text-[var(--muted)]">{{ node.currentDisplay }}</td>
                              <td class="py-2 px-3 text-right font-mono">{{ node.zscoreDisplay }}</td>
                              <td class="py-2 px-3 text-right font-mono">{{ node.anomalyDisplay }}</td>
                              <td class="py-2 pl-3 text-right font-mono">{{ node.absScoreDisplay }}</td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </td>
                </tr>
                </template>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Section 2: Transmission Chains — Pro only -->
      <Paywall :blurred="!isPro" :title="t('analysis.unlockChain')" :description="t('analysis.unlockChainDesc')">
      <div class="mb-12 fade-in fade-in-delay-1">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Risk Transmission</p>
        <h2 class="text-lg font-light text-white mb-6">
          {{ t('analysis.chainTitle') }}
          <span class="text-sm text-[var(--muted)] font-normal ml-2">{{ activeChains.length }} {{ t('analysis.chainActive') }} / {{ dormantChains.length }} {{ t('analysis.chainDormant') }}</span>
        </h2>

        <div class="grid gap-4 lg:grid-cols-2">
          <div v-for="chain in sortedChains" :key="chain.id"
               class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 card-hover"
               :class="chain.active ? 'border-l-[3px]' : 'opacity-50'"
               :style="chain.active ? { borderLeftColor: chain.stress >= 50 ? 'var(--red)' : 'var(--orange)' } : {}">
            <div class="flex justify-between items-start mb-2">
              <div>
                <span class="text-xs px-1.5 py-0.5 rounded mr-2"
                      :class="chain.active ? 'bg-[var(--red)]/10 text-[var(--red)]' : 'bg-white/5 text-[var(--muted)]'">
                  {{ chain.active ? t('analysis.transmitting') : t('analysis.sleeping') }}
                </span>
                <span class="text-sm text-white font-medium">{{ tx(chain.name) }}</span>
              </div>
              <span class="text-sm font-mono" :style="{ color: chain.stress >= 50 ? 'var(--red)' : chain.stress >= 30 ? 'var(--orange)' : 'var(--green)' }">
                {{ chain.stress.toFixed(0) }}
              </span>
            </div>
            <p class="text-xs text-[var(--muted)]">{{ chain.path?.map((n: string) => tx(nodeNames[n] || n)).join(' → ') }}</p>
            <div class="mt-3 space-y-1">
              <div v-for="node in chainNodeBars(chain)" :key="node.id" class="flex items-center gap-2">
                <span class="w-24 truncate text-[10px] text-[var(--muted)]">{{ node.name }}</span>
                <div class="h-1.5 flex-1 rounded-full bg-white/[0.05] overflow-hidden">
                  <div class="h-full rounded-full" :style="{ width: node.width + '%', backgroundColor: scoreColor(node.score * 100) }"></div>
                </div>
                <span class="w-8 text-right text-[10px] font-mono text-[var(--muted)]">{{ (node.score * 100).toFixed(0) }}</span>
              </div>
            </div>
            <div class="mt-3 flex items-center justify-between text-[10px] text-[var(--muted)] font-mono">
              <span>{{ t('analysis.pathStrength') }}</span>
              <span>{{ Number(chain.path_strength || 0).toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>
      </Paywall>

      <!-- Section 3: Anomalous Indicators — Pro only -->
      <Paywall :blurred="!isPro" :title="t('analysis.unlockAnomaly')" :description="t('analysis.unlockAnomalyDesc')">
      <!-- Section 3: Anomalous Indicators — WHAT is abnormal -->
      <div class="mb-12 fade-in fade-in-delay-2">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Anomaly Detection</p>
        <h2 class="text-lg font-light text-white mb-6">
          {{ t('analysis.anomalyTitle') }}
          <span class="text-sm text-[var(--muted)] font-normal ml-2">{{ anomalousNodes.length }} {{ t('analysis.deviating') }}</span>
        </h2>

        <div class="bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="text-[var(--muted)] text-xs uppercase tracking-wider border-b border-[var(--border)]">
                <th class="text-left px-5 py-3 font-medium">{{ t('analysis.indicator') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.currentVal') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.deviation') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.anomalyScore') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.absScore') }}</th>
                <th class="text-right px-5 py-3 font-medium">{{ t('analysis.direction') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="node in anomalousNodes" :key="node.id"
                  class="border-t border-[var(--border)] hover:bg-white/[0.02] transition-colors">
                <td class="px-5 py-3 text-white">{{ tx(node.name) }}</td>
                <td class="px-5 py-3 text-right font-mono text-[var(--muted)]">{{ node.value?.toFixed(2) ?? '—' }}</td>
                <td class="px-5 py-3 text-right font-mono" :style="{ color: Math.abs(node.zscore) > 3 ? 'var(--red)' : 'var(--yellow)' }">
                  {{ Math.abs(node.zscore).toFixed(1) }}×
                </td>
                <td class="px-5 py-3 text-right font-mono" :style="{ color: node.anomalyScore > 0 ? 'var(--orange)' : 'var(--muted)' }">{{ (node.anomalyScore * 100).toFixed(0) }}</td>
                <td class="px-5 py-3 text-right font-mono text-[var(--muted)]">{{ node.absScoreDisplay }}</td>
                <td class="px-5 py-3 text-right">
                  <span :class="node.zscore > 0 ? 'text-[var(--red)]' : 'text-[var(--green)]'">
                    {{ node.zscore > 0 ? t('analysis.high') : t('analysis.low') }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      </Paywall>

      <!-- Section 4: Full Report — Chinese publishing format only -->
      <div class="mb-12 fade-in fade-in-delay-3" v-if="lang === 'zh' && reportStore.latest">
        <div class="flex items-center justify-between mb-6">
          <div>
            <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Full Report</p>
            <h2 class="text-lg font-light text-white">{{ t('analysis.report') }}</h2>
          </div>
          <button @click="showFullReport = !showFullReport"
                  class="text-xs text-[var(--accent)] hover:text-white transition-colors px-3 py-1.5 rounded border border-[var(--border)] hover:border-[var(--accent)]">
            {{ showFullReport ? t('common.collapse') : t('common.expand') }}
          </button>
        </div>
        <div v-show="showFullReport" class="bg-[var(--card)] border border-[var(--border)] rounded-xl p-4">
          <!-- Prefer WeChat HTML (better formatting), fallback to Markdown -->
          <div v-if="lang === 'zh' && socialContent.wechat" class="flex justify-center">
            <div class="w-full max-w-[640px] rounded-xl overflow-hidden">
              <iframe :srcdoc="socialContent.wechat" class="w-full border-0" style="height:800px" sandbox="allow-same-origin"></iframe>
            </div>
          </div>
          <div v-else class="prose prose-invert prose-sm max-w-none" v-html="renderedMarkdown"></div>
        </div>
      </div>

      <!-- Section 6: Share & Export -->
      <div v-if="lang === 'zh'" class="mb-12 fade-in">
        <p class="text-[11px] text-[var(--muted)] uppercase tracking-[4px] mb-2">Share & Export</p>
        <h2 class="text-lg font-light text-white mb-6">{{ t('analysis.share') }}</h2>

        <div class="flex gap-3">
          <button @click="activeExport = activeExport === 'wechat' ? '' : 'wechat'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'wechat' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            💬 {{ lang === 'zh' ? '微信文章' : 'WeChat' }}
          </button>
          <button @click="activeExport = activeExport === 'zsxq' ? '' : 'zsxq'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'zsxq' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            🌟 {{ lang === 'zh' ? '知识星球' : 'Zsxq' }}
          </button>
          <button @click="activeExport = activeExport === 'card' ? '' : 'card'"
                  class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm transition-all"
                  :class="activeExport === 'card' ? 'bg-[var(--accent)]/15 text-[var(--accent)]' : 'bg-[var(--card)] border border-[var(--border)] text-[var(--muted)] hover:text-white'">
            🖼️ {{ lang === 'zh' ? '分享卡片' : 'Card' }}
          </button>
        </div>

        <!-- WeChat Preview -->
        <div v-if="lang === 'zh' && activeExport === 'wechat' && socialContent.wechat" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl overflow-hidden">
          <div class="flex items-center justify-between px-5 py-3 border-b border-[var(--border)]">
            <span class="text-xs text-[var(--muted)]">{{ lang === 'zh' ? '微信公众号文章预览' : 'WeChat Article Preview' }}</span>
            <a :href="'data:text/html;charset=utf-8,' + encodeURIComponent(socialContent.wechat)"
               download="gfcri_wechat.html"
               class="text-xs text-[var(--accent)] hover:text-white transition-colors"> {{ lang === 'zh' ? '下载 HTML' : 'Download HTML' }} </a>
          </div>
          <div class="p-4 flex justify-center">
            <div class="max-w-[375px] w-full rounded-2xl overflow-hidden border border-[var(--border)]">
              <iframe :srcdoc="socialContent.wechat" class="w-full" style="height:600px" sandbox="allow-same-origin"></iframe>
            </div>
          </div>
        </div>

        <!-- Zsxq Preview -->
        <div v-if="lang === 'zh' && activeExport === 'zsxq' && socialContent.zsxq" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5">
          <div class="flex items-center justify-between mb-3">
            <span class="text-xs text-[var(--muted)]">{{ lang === 'zh' ? '知识星球帖子' : 'Zsxq Post' }}</span>
            <button @click="copyText(socialContent.zsxq)" class="text-xs text-[var(--accent)] hover:text-white transition-colors">
              {{ copied ? (lang === 'zh' ? '已复制 ✓' : 'Copied ✓') : (lang === 'zh' ? '复制原文' : 'Copy') }}
            </button>
          </div>
          <pre class="text-xs text-[var(--muted)] whitespace-pre-wrap leading-relaxed max-h-[500px] overflow-y-auto">{{ socialContent.zsxq }}</pre>
        </div>

        <!-- Card Preview -->
        <div v-if="lang === 'zh' && activeExport === 'card' && socialContent.cardUrl" class="mt-4 bg-[var(--card)] border border-[var(--border)] rounded-xl p-5 flex justify-center">
          <img :src="socialContent.cardUrl" alt="Share Card" class="max-w-[400px] rounded-xl shadow-lg" />
        </div>
      </div>

    </template>

    <div v-else class="text-[var(--muted)] text-center py-20 text-sm">{{ t("common.noData") }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import MarkdownIt from 'markdown-it'

import { useRiskStore } from '@/stores/risk'
import { useReportStore } from '@/stores/report'
import { COLORS } from '@/composables/useTheme'
import { useAuth } from '@/composables/useAuth'
import { useI18n } from '@/composables/useI18n'
import { useRiskWatch, type RiskWatchType } from '@/composables/useRiskWatch'
import { fetchModelFoundation } from '@/api/modelFoundation'
import type { ModelFoundation, SubIndexReceipt } from '@/api/types'
import LoadingSpinner from '@/components/common/LoadingSpinner.vue'
import Paywall from '@/components/common/Paywall.vue'
import TradeSpilloverPanel from '@/components/common/TradeSpilloverPanel.vue'
import CrisisRegimePanel from '@/components/common/CrisisRegimePanel.vue'
import CausalDiscoveryPanel from '@/components/common/CausalDiscoveryPanel.vue'
import client from '@/api/client'

use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer])

const md = new MarkdownIt()
const riskStore = useRiskStore()
const reportStore = useReportStore()
const { isPro } = useAuth()
const { t, tx, lang } = useI18n()
const showFullReport = ref(false)
const activeExport = ref('')
const copied = ref(false)
const expandedChainId = ref('')
const alertEmail = ref(localStorage.getItem('gfcri_alert_email') || '')
const subscribed = ref(!!localStorage.getItem('gfcri_alert_email'))
const socialContent = ref<{ wechat: string; zsxq: string; cardUrl: string }>({ wechat: '', zsxq: '', cardUrl: '' })
const selectedWatchIndicatorId = ref('')
const riskWatch = useRiskWatch()
const watchItems = riskWatch.items
const watchedIndicatorIds = riskWatch.watchedIndicatorIds
const modelFoundation = ref<ModelFoundation | null>(null)
const selectedSubIndexId = ref('SI_CREDIT')

onMounted(async () => {
  riskStore.loadLatest()
  riskStore.loadHistory(30)
  reportStore.loadLatest()
  try {
    const [wRes, zRes] = await Promise.allSettled([
      client.get('/social/wechat/latest'),
      client.get('/social/zsxq/latest'),
    ])
    if (wRes.status === 'fulfilled') socialContent.value.wechat = wRes.value.data?.content || ''
    if (zRes.status === 'fulfilled') socialContent.value.zsxq = zRes.value.data?.content || ''
  } catch {}
  try {
    modelFoundation.value = await fetchModelFoundation()
  } catch {}
})

function copyText(text: string) {
  navigator.clipboard.writeText(text)
  copied.value = true
  setTimeout(() => copied.value = false, 2000)
}

function subscribe() {
  if (alertEmail.value && alertEmail.value.includes('@')) {
    localStorage.setItem('gfcri_alert_email', alertEmail.value)
    subscribed.value = true
  }
}

const nodeNames: Record<string, string> = {
  fed_funds: '美联储利率', ust_10y: '10年美债', ust_2y: '2年美债', dxy: '美元',
  krw_usd: '韩元', kospi: '韩股', vix: '恐慌指数', spx: '标普500',
  hyg: '高收益债', lqd: '投资级债', kre: '银行股', vnq: '房地产',
  oil_wti: '原油', gold: '黄金', copper: '铜', hsi: '恒生',
  eurusd: '欧元', cny_usd: '人民币', jpy_usd: '日元', nikkei: '日经',
  sox: '半导体', stoxx50: '欧股', eem: '新兴市场', emb: '新兴债',
  btc: '比特币', italy_etf: '意大利', kr_cds_5y: '韩国信用',
  consumer_stress: '消费压力', us_recession_prob: '衰退概率',
  ai_capex: 'AI投资', dram_spot: 'DRAM', nand_spot: 'NAND',
  natgas: '天然气', wheat: '小麦', bdry: '干散货',
}

const renderedNarrative = computed(() => {
  const narr = currentJudgmentMarkdown.value
  return narr ? md.render(narr) : ''
})

const truncatedNarrative = computed(() => {
  const narr = currentJudgmentMarkdown.value
  if (!narr) return ''
  const paragraphs = narr.split('\n\n').filter((p: string) => p.trim())
  return md.render(paragraphs.slice(0, 2).join('\n\n'))
})

const renderedMarkdown = computed(() => {
  if (lang.value === 'en') return md.render(englishFullReportMarkdown.value)
  return reportStore.latest ? md.render(reportStore.latest.report_markdown) : ''
})

const englishFullReportMarkdown = computed(() => {
  const risk = riskStore.latest
  if (!risk) return 'No report data available.'

  const lines: string[] = []
  const alert = t(`alert.${risk.alert_level}`)
  const coherence = (risk.coherence_multiplier || 1).toFixed(2)

  lines.push(`# GFCRI Daily Report`)
  lines.push('')
  lines.push(`**Date:** ${risk.index_date}`)
  lines.push(`**Risk Index:** ${risk.gfcri_value.toFixed(1)} / 100 (${alert})`)
  lines.push(`**Coherence Multiplier:** ${coherence}x`)
  lines.push('')

  lines.push(`## Key Judgment`)
  lines.push(currentJudgmentMarkdown.value)
  lines.push('')

  const subDetails = risk.sub_index_details || {}
  const subEntries = Object.entries(subDetails)
    .map(([key, val]: [string, any]) => ({
      name: tx(val?.name || key),
      score: Number(val?.score || 0),
      driver: tx(val?.top_driver || val?.driver || ''),
    }))
    .sort((a, b) => b.score - a.score)
  if (subEntries.length) {
    lines.push(`## Sub-Index Scores`)
    lines.push('')
    lines.push(`| Sub-index | Score | Main Driver |`)
    lines.push(`|---|---:|---|`)
    for (const item of subEntries) {
      lines.push(`| ${item.name} | ${item.score.toFixed(1)} | ${item.driver || '-'} |`)
    }
    lines.push('')
  }

  if (activeChains.value.length) {
    lines.push(`## Active Transmission Chains`)
    lines.push('')
    for (const chain of activeChains.value) {
      const path = (chain.path || []).map((n: string) => tx(nodeNames[n] || n)).join(' -> ')
      lines.push(`- **${tx(chain.name)}** (${Number(chain.stress || 0).toFixed(0)}): ${path}`)
      if (chain.description) lines.push(`  ${tx(chain.description)}`)
    }
    lines.push('')
  } else {
    lines.push(`## Active Transmission Chains`)
    lines.push('')
    lines.push(`No active transmission chains are currently detected.`)
    lines.push('')
  }

  lines.push(`## Anomalous Indicators`)
  lines.push('')
  if (anomalousNodes.value.length) {
    lines.push(`| Indicator | Current | Deviation | Direction | Directional pressure |`)
    lines.push(`|---|---:|---:|---|---:|`)
    for (const node of anomalousNodes.value) {
      const direction = node.zscore > 0 ? 'High' : 'Low'
      const value = typeof node.value === 'number' ? node.value.toFixed(2) : '-'
      lines.push(`| ${tx(node.name)} | ${value} | ${Math.abs(node.zscore).toFixed(1)}x | ${direction} | ${(node.anomalyScore * 100).toFixed(0)} |`)
    }
  } else {
    lines.push(`No indicators are currently outside the anomaly threshold.`)
  }
  lines.push('')

  const history = [...riskStore.history].reverse().slice(-7)
  if (history.length > 1) {
    lines.push(`## Recent GFCRI Trend`)
    lines.push('')
    lines.push(`| Date | GFCRI | Alert |`)
    lines.push(`|---|---:|---|`)
    for (const row of history) {
      lines.push(`| ${row.index_date} | ${Number(row.gfcri_value).toFixed(1)} | ${t(`alert.${row.alert_level}`)} |`)
    }
    lines.push('')
  }

  lines.push(`## Notes`)
  lines.push('')
  lines.push(`This English report is generated from the structured GFCRI data available in the dashboard. It avoids the Chinese social-publishing report format when English mode is selected.`)

  return lines.join('\n')
})

const currentJudgmentMarkdown = computed(() => {
  const risk = riskStore.latest
  if (!risk) return lang.value === 'zh' ? '暂无风险数据。' : 'No risk data is available.'

  const active = activeChains.value.length
  const anomalies = anomalousNodes.value.length
  const driver = topNodeContributions.value[0]
  const chain = activeChains.value[0]
  const hidden = hiddenRisk.value
  const topSub = subIndexRows.value.slice(0, 3)
  const topSubText = topSub.map(s => `${s.name} ${s.score.toFixed(1)}`).join(lang.value === 'zh' ? '、' : ', ')
  const chainName = chain ? tx(chain.name) : (lang.value === 'zh' ? '暂无活跃传导链' : 'no active transmission channel')
  const chainStress = chain ? Number(chain.stress || 0).toFixed(0) : '-'
  const driverName = driver?.name || (lang.value === 'zh' ? '暂无单一主导指标' : 'no dominant single indicator')
  const driverDetail = driver
    ? `${driverName} Z=${driver.zscore.toFixed(2)}, ${t('analysis.absScore')} ${driver.absScoreDisplay}`
    : driverName
  const realizedDamage = currentRealizedDamageLabel.value
  const damageAnchor = currentDamageAnchor.value
  const nextWatch = currentNextWatch.value

  if (lang.value === 'zh') {
    return [
      `**核心判断：当前不是“已经发生危机”的读数，而是“前瞻压力偏高、实际损害尚未充分兑现”的状态。** GFCRI 当前为 **${risk.gfcri_value.toFixed(1)} / 100（${t(`alert.${risk.alert_level}`)}）**，应主要解读为风险压力和传导概率上升，而不是事后损害等级已经升高。`,
      '',
      `**实际损害锚点：${realizedDamage}。** ${damageAnchor} 因此，当前更接近“压力累积/隐藏风险暴露前阶段”，不能简单等同于 2008 或 2020 式已经兑现的系统性损害。`,
      '',
      `**为什么仍需观察：** 当前有 **${active}** 条活跃传导链、**${anomalies}** 个统计异常指标，信号一致性为 **${(risk.coherence_multiplier || 1).toFixed(2)}x**。注意：统计异常不等于风险压力，系统现在只把“朝风险方向移动”的异常计入压力。主要压力来自 **${topSubText || '暂无显著子指数'}**；首要驱动为 **${driverDetail}**；首要传导链为 **${chainName}（压力 ${chainStress}）**。`,
      '',
      `**隐藏风险：${hidden.statusLabel}，暗流加分 +${hidden.undercurrent.toFixed(1)}。** 深层压力 ${hidden.deepAvgDisplay}，表层压力 ${hidden.surfaceAvgDisplay}，缺口 ${hidden.gapDisplay}。这说明部分风险可能被低波动、政策缓冲或市场拥挤交易掩盖，尤其需要关注日元、黄金、AI/半导体和信用/银行链条是否从“估值压力”转化为“现金流/融资损害”。`,
      '',
      `**下一步观察：** ${nextWatch}`,
    ].join('\n')
  }

  return [
    `**Key judgment: this is not a reading that a crisis has already materialized; it is a high forward-pressure state with limited realized damage so far.** GFCRI is **${risk.gfcri_value.toFixed(1)} / 100 (${t(`alert.${risk.alert_level}`)})**, so it should be read as rising pressure and transmission probability, not as proof that realized damage has already reached crisis levels.`,
    '',
    `**Realized-damage anchor: ${realizedDamage}.** ${damageAnchor} The current state is closer to pressure accumulation before full damage realization than to a 2008- or 2020-style systemic damage event.`,
    '',
    `**Why it still matters:** there are **${active}** active transmission channels, **${anomalies}** statistically anomalous indicators, and signal coherence is **${(risk.coherence_multiplier || 1).toFixed(2)}x**. Statistical anomaly is not the same as risk pressure: the model now only adds pressure when the move is in the risk direction. The main pressure pockets are **${topSubText || 'no dominant sub-index'}**. The top driver is **${driverDetail}** and the leading channel is **${chainName} (stress ${chainStress})**.`,
    '',
    `**Hidden risk: ${hidden.statusLabel}, undercurrent boost +${hidden.undercurrent.toFixed(1)}.** Deep stress is ${hidden.deepAvgDisplay}, surface stress is ${hidden.surfaceAvgDisplay}, and the gap is ${hidden.gapDisplay}. This means some risk may be masked by low volatility, policy buffers, or crowded momentum trades. Watch JPY, gold, AI/semiconductors, and credit/banking channels for conversion from valuation pressure into cash-flow or funding damage.`,
    '',
    `**Next watch:** ${nextWatch}`,
  ].join('\n')
})

const sortedChains = computed(() => {
  const chains = riskStore.latest?.chain_details
  if (!chains) return []
  const list = Array.isArray(chains) ? chains : Object.values(chains)
  return [...list].sort((a: any, b: any) => {
    if (a.active !== b.active) return a.active ? -1 : 1
    return b.stress - a.stress
  })
})

const activeChains = computed(() => sortedChains.value.filter((c: any) => c.active))
const dormantChains = computed(() => sortedChains.value.filter((c: any) => !c.active))

const SURFACE_NODE_IDS = new Set(['vix', 'spx', 'kospi', 'hsi', 'sox', 'stoxx50'])
const DEEP_NODE_IDS = new Set(['hyg', 'lqd', 'kre', 'vnq', 'dxy', 'ust_10y', 'oil_wti', 'krw_usd'])

const hiddenRisk = computed(() => {
  const risk = riskStore.latest
  const divergence = risk?.divergence || null
  const fallback = estimateDivergence()
  const status = String(divergence?.status || fallback.status || 'none')
  const surfaceAvg = Number(divergence?.surface_avg ?? fallback.surfaceAvg ?? 0)
  const deepAvg = Number(divergence?.deep_avg ?? fallback.deepAvg ?? 0)
  const gap = Number(divergence?.gap ?? fallback.gap ?? 0)
  const undercurrent = Number(risk?.undercurrent_boost ?? fallback.undercurrent ?? 0)
  const rawDetails = Array.isArray(divergence?.details) ? divergence.details : []
  const items = rawDetails.length ? rawDetails.map(hiddenRiskDetail) : fallback.items
  return {
    status,
    statusLabel: hiddenRiskStatusLabel(status),
    surfaceAvg,
    deepAvg,
    gap,
    undercurrent,
    surfaceAvgDisplay: `${(surfaceAvg * 100).toFixed(0)}`,
    deepAvgDisplay: `${(deepAvg * 100).toFixed(0)}`,
    gapDisplay: `${(gap * 100).toFixed(0)}`,
    primaryDetail: items[0]?.detail || t('analysis.hiddenNone'),
    items,
  }
})

const hiddenRiskColor = computed(() => {
  const status = hiddenRisk.value.status
  if (status === 'critical') return COLORS.red
  if (status === 'significant') return COLORS.orange
  if (status === 'mild') return COLORS.yellow
  return COLORS.green
})

const currentRealizedDamageLabel = computed(() => {
  const risk = riskStore.latest
  if (!risk) return lang.value === 'zh' ? '暂无数据' : 'No data'
  const credit = currentSubIndexScore('SI_CREDIT')
  const banking = currentSubIndexScore('SI_BANKING')
  const stress = Math.max(credit, banking)
  if (stress >= 60) return lang.value === 'zh' ? 'D2-D3 · 信用/金融损害已显著' : 'D2-D3 · material credit/financial damage'
  if (risk.gfcri_value >= 75 && activeChains.value.length >= 5) return lang.value === 'zh' ? 'D2 · 广泛市场损害风险' : 'D2 · broad market-damage risk'
  if (risk.gfcri_value >= 50 || hiddenRisk.value.undercurrent > 0) return lang.value === 'zh' ? 'D0-D1 · 市场压力，实体损害未充分兑现' : 'D0-D1 · market pressure, limited realized damage'
  return lang.value === 'zh' ? 'D0 · 未见显著实际损害' : 'D0 · no material realized damage'
})

const currentDamageAnchor = computed(() => {
  const risk = riskStore.latest
  if (!risk) return ''
  const credit = currentSubIndexScore('SI_CREDIT')
  const banking = currentSubIndexScore('SI_BANKING')
  const sentiment = currentSubIndexScore('SI_SENTIMENT')
  if (lang.value === 'zh') {
    return `当前信用子指数为 ${credit.toFixed(1)}，银行/房产子指数为 ${banking.toFixed(1)}，情绪/风险偏好子指数为 ${sentiment.toFixed(1)}。这些读数说明市场压力存在，但尚未形成类似信用冻结、银行系统连锁损害或就业崩塌的强证据。`
  }
  return `Current credit stress is ${credit.toFixed(1)}, banking/real-estate stress is ${banking.toFixed(1)}, and sentiment/risk-appetite stress is ${sentiment.toFixed(1)}. These readings show pressure, but not yet strong evidence of credit freeze, cascading banking damage, or labor-market collapse.`
})

const currentNextWatch = computed(() => {
  const hidden = hiddenRisk.value
  if (hidden.undercurrent >= 15) {
    return lang.value === 'zh'
      ? '优先观察隐藏压力是否转化为可见损害：信用利差是否扩张、银行/房产链条是否恶化、日元贬值和套利交易是否反转、AI/半导体高位交易是否出现拥挤踩踏。'
      : 'Watch whether hidden pressure converts into visible damage: wider credit spreads, weaker banking/real-estate channels, JPY/carry reversal, or crowded AI/semiconductor unwind.'
  }
  if (activeChains.value.length >= 4) {
    return lang.value === 'zh'
      ? '优先观察活跃传导链是否继续扩散，尤其是从汇率和权益估值扩散到信用、银行融资、企业盈利和贸易需求。'
      : 'Watch whether active channels keep spreading, especially from FX and equity valuation into credit, bank funding, earnings, and trade demand.'
  }
  if (anomalousNodes.value.length >= 6) {
    return lang.value === 'zh'
      ? '优先观察异常指标是快速回归还是同步扩散；同步扩散比单点异常更重要。'
      : 'Watch whether anomalous indicators normalize or spread together; synchronized spread matters more than isolated outliers.'
  }
  return lang.value === 'zh'
    ? '继续观察趋势、传导链和隐藏风险是否出现连续多日恶化。'
    : 'Continue monitoring whether trend, transmission channels, and hidden risk deteriorate for several consecutive observations.'
})

type EvidenceCard = {
  id: string
  kicker: string
  title: string
  value: string
  body: string
  action: string
  target: string
  watchType?: RiskWatchType
  watchId?: string
  watchLabel?: string
  watchReason?: string
}

const todayEvidenceCards = computed<EvidenceCard[]>(() => {
  const risk = riskStore.latest
  const coherence = Number(risk?.coherence_multiplier || 1)
  const topSub = subIndexRows.value.slice(0, 3)
  const driver = topNodeContributions.value[0]
  const chain = activeChains.value[0]
  const hidden = hiddenRisk.value
  const cards: EvidenceCard[] = []
  if (lang.value === 'zh') {
    cards.push({
      id: 'coherence',
      kicker: 'Coherence',
      title: '信号共振',
      value: `${coherence.toFixed(2)}x`,
        body: `今天的 ${coherence.toFixed(2)}x 表示多个方向性风险信号同向出现，基础压力被放大约 ${Math.max(0, (coherence - 1) * 100).toFixed(0)}%。改善型异常不会再被计入压力。`,
      action: '查看传导链',
      target: 'chain-pressure',
    })
    if (topSub.length) {
      cards.push({
        id: 'sub-index',
        kicker: 'Pressure Pockets',
        title: '压力集中领域',
        value: topSub.map(s => `${s.name} ${s.score.toFixed(1)}`).join(' / '),
        body: `这些是当天压力最高的风险领域。分数是 0-100 压力读数：25 附近进入关注，50 以上说明压力明显，75 以上接近历史危机压力区。`,
        action: '查看构成',
        target: 'sub-index-breakdown',
      })
    }
    if (driver) {
      cards.push({
        id: `driver-${driver.id}`,
        kicker: 'Top Driver',
        title: driver.name,
        value: `Z=${driver.zscore.toFixed(2)} · ${t('analysis.absScore')} ${driver.absScoreDisplay}`,
        body: buildIndicatorExplanation(driver.id, driver),
        action: '查看指标',
        target: 'node-contribution',
        watchType: 'indicator',
        watchId: driver.id,
        watchLabel: driver.name,
        watchReason: '今日首要驱动',
      })
    }
    if (hidden.undercurrent > 0) {
      cards.push({
        id: 'hidden-risk',
        kicker: 'Hidden Risk',
        title: `隐藏风险 ${hidden.statusLabel}`,
        value: `+${hidden.undercurrent.toFixed(1)}`,
        body: `深层压力 ${hidden.deepAvgDisplay}，表层压力 ${hidden.surfaceAvgDisplay}，缺口 ${hidden.gapDisplay}。系统会自动提取隐藏风险相关指标，点击下方指标可加入 My Risk Watch。`,
        action: '查看隐藏风险',
        target: 'hidden-risk-section',
      })
    }
    if (chain) {
      cards.push({
        id: `chain-${chain.id}`,
        kicker: 'Leading Chain',
        title: tx(chain.name),
        value: `压力 ${Number(chain.stress || 0).toFixed(0)}`,
        body: `这是当前最强的活跃传导链。链路压力来自路径内节点异常和边权强度，点击可查看节点、路径强度和计算逻辑。`,
        action: '查看链路',
        target: 'chain-pressure',
        watchType: 'chain',
        watchId: chain.id,
        watchLabel: tx(chain.name),
        watchReason: '今日首要传导链',
      })
    }
    return cards.slice(0, 5)
  }
  cards.push({
    id: 'coherence',
    kicker: 'Coherence',
    title: 'Signal resonance',
    value: `${coherence.toFixed(2)}x`,
      body: `Today’s ${coherence.toFixed(2)}x means multiple directional risk signals point in the same direction, amplifying base pressure by about ${Math.max(0, (coherence - 1) * 100).toFixed(0)}%. Improvement-side anomalies are no longer counted as pressure.`,
    action: 'Open chains',
    target: 'chain-pressure',
  })
  if (topSub.length) {
    cards.push({
      id: 'sub-index',
      kicker: 'Pressure Pockets',
      title: 'Where pressure is concentrated',
      value: topSub.map(s => `${s.name} ${s.score.toFixed(1)}`).join(' / '),
      body: 'These are the highest-pressure domains today. Scores are 0-100 pressure readings: around 25 means watch, above 50 means material pressure, and above 75 is close to historical crisis stress.',
      action: 'Open breakdown',
      target: 'sub-index-breakdown',
    })
  }
  if (driver) {
    cards.push({
      id: `driver-${driver.id}`,
      kicker: 'Top Driver',
      title: driver.name,
      value: `Z=${driver.zscore.toFixed(2)} · ${t('analysis.absScore')} ${driver.absScoreDisplay}`,
      body: buildIndicatorExplanation(driver.id, driver),
      action: 'Open indicator',
      target: 'node-contribution',
      watchType: 'indicator',
      watchId: driver.id,
      watchLabel: driver.name,
      watchReason: 'Top driver today',
    })
  }
  if (hidden.undercurrent > 0) {
    cards.push({
      id: 'hidden-risk',
      kicker: 'Hidden Risk',
      title: `Hidden risk: ${hidden.statusLabel}`,
      value: `+${hidden.undercurrent.toFixed(1)}`,
      body: `Deep stress is ${hidden.deepAvgDisplay}, surface stress is ${hidden.surfaceAvgDisplay}, and the gap is ${hidden.gapDisplay}. Related indicators are extracted dynamically below.`,
      action: 'Open hidden risk',
      target: 'hidden-risk-section',
    })
  }
  if (chain) {
    cards.push({
      id: `chain-${chain.id}`,
      kicker: 'Leading Chain',
      title: tx(chain.name),
      value: `Stress ${Number(chain.stress || 0).toFixed(0)}`,
      body: 'This is the strongest active transmission chain today. Chain stress comes from node anomalies and causal path strength.',
      action: 'Open chain',
      target: 'chain-pressure',
      watchType: 'chain',
      watchId: chain.id,
      watchLabel: tx(chain.name),
      watchReason: 'Leading chain today',
    })
  }
  return cards.slice(0, 5)
})

const watchActionItems = computed(() => {
  const ids = new Set<string>()
  const driver = topNodeContributions.value[0]
  if (driver?.id) ids.add(driver.id)
  for (const id of extractHiddenRiskIndicatorIds()) ids.add(id)
  for (const row of subIndexRows.value.slice(0, 4)) {
    const top = (riskStore.latest?.sub_index_details as any)?.[row.id]?.top_driver
    if (top) ids.add(top)
  }
  for (const chain of activeChains.value.slice(0, 2)) {
    for (const id of chain.path || []) ids.add(id)
  }
  for (const id of ['gold', 'jpy_usd', 'sox', 'spx', 'hyg', 'kre', 'vnq', 'dxy', 'krw_usd']) ids.add(id)

  return Array.from(ids)
    .map(id => indicatorWatchItem(id))
    .filter(Boolean)
    .slice(0, 10) as Array<ReturnType<typeof indicatorWatchItem> & { id: string }>
})

const selectedWatchItem = computed(() => {
  const id = selectedWatchIndicatorId.value || watchedIndicatorIds.value[0] || watchActionItems.value[0]?.id || ''
  return id ? indicatorWatchItem(id) : null
})

const selectedWatchTrend = computed(() => {
  const id = selectedWatchItem.value?.id
  if (!id) return []
  return [...riskStore.history].reverse()
    .map((row: any) => {
      const info = row.node_contributions?.[id]
      if (!info) return null
      const abs = info.abs_score === null || info.abs_score === undefined ? 0 : Number(info.abs_score)
      const anomaly = Number(info.anomaly_score || 0)
      return {
        date: row.index_date,
        pressure: Math.max(abs, anomaly) * 100,
        zscore: Number(info.zscore || 0),
      }
    })
    .filter(Boolean) as Array<{ date: string; pressure: number; zscore: number }>
})

const selectedWatchTrendOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    backgroundColor: '#111214',
    borderColor: 'rgba(255,255,255,0.08)',
    textStyle: { color: '#eff1f5', fontSize: 11 },
  },
  grid: { left: 36, right: 14, top: 16, bottom: 24 },
  xAxis: {
    type: 'category',
    data: selectedWatchTrend.value.map(p => p.date),
    axisLabel: { color: '#8a93a3', fontSize: 9 },
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    min: 0,
    max: 100,
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    axisLabel: { color: '#8a93a3', fontSize: 9 },
  },
  series: [{
    type: 'line',
    data: selectedWatchTrend.value.map(p => Number(p.pressure.toFixed(1))),
    smooth: true,
    showSymbol: false,
    lineStyle: { color: COLORS.accent, width: 2 },
    areaStyle: { color: COLORS.accent + '12' },
  }],
}))

const selectedWatchRelatedChains = computed(() => {
  const id = selectedWatchItem.value?.id
  if (!id) return []
  return chainPressureRows.value.filter((chain: any) => {
    const raw = sortedChains.value.find((c: any) => c.id === chain.id)
    return (raw?.path || []).includes(id)
  })
})

const anomalousNodes = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return []
  return Object.entries(nc)
    .filter(([, info]: [string, any]) => info.is_anomalous)
    .map(([id, info]: [string, any]) => ({
      id, name: info.display_name || nodeNames[id] || id,
      zscore: Number(info.zscore || 0),
      value: info.current_value,
      anomalyScore: Number(info.anomaly_score || 0),
      absScore: info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score),
      absScoreDisplay: info.abs_score === null || info.abs_score === undefined ? '-' : (Number(info.abs_score) * 100).toFixed(0),
    }))
    .sort((a, b) => Math.abs(b.zscore) - Math.abs(a.zscore))
})

function estimateDivergence() {
  const nc = riskStore.latest?.node_contributions || {}
  const surface = Object.entries(nc)
    .filter(([id, info]: [string, any]) => SURFACE_NODE_IDS.has(id) && info.abs_score !== null && info.abs_score !== undefined)
    .map(([id, info]: [string, any]) => ({ id, score: Number(info.abs_score || 0), name: tx(info.display_name || nodeNames[id] || id) }))
  const deep = Object.entries(nc)
    .filter(([id, info]: [string, any]) => DEEP_NODE_IDS.has(id) && info.abs_score !== null && info.abs_score !== undefined)
    .map(([id, info]: [string, any]) => ({ id, score: Number(info.abs_score || 0), name: tx(info.display_name || nodeNames[id] || id) }))

  const surfaceAvg = avg(surface.map(x => x.score))
  const deepAvg = avg(deep.map(x => x.score))
  const gap = deepAvg - surfaceAvg
  const stressedDeep = deep.filter(x => x.score > 0.35).sort((a, b) => b.score - a.score)
  const calmSurface = surface.filter(x => x.score < 0.25).sort((a, b) => a.score - b.score)
  const status = gap > 0.25 && deepAvg > 0.4 ? 'critical'
    : gap > 0.15 && deepAvg > 0.3 ? 'significant'
    : gap > 0.08 ? 'mild'
    : 'none'
  const items = stressedDeep.length ? [{
    title: t('analysis.hiddenRisk'),
    detail: lang.value === 'zh'
      ? `${stressedDeep.slice(0, 3).map(x => `${x.name} ${(x.score * 100).toFixed(0)}`).join('、')} 处于高压${calmSurface.length ? '，而表面指标相对平静。' : '。'}`
      : `${stressedDeep.slice(0, 3).map(x => `${x.name} ${(x.score * 100).toFixed(0)}`).join(', ')} ${calmSurface.length ? 'while headline indicators remain calmer.' : ''}`,
  }] : []
  return {
    status,
    surfaceAvg,
    deepAvg,
    gap,
    undercurrent: status === 'critical' ? 12 : status === 'significant' ? 8 : status === 'mild' ? 3 : 0,
    items,
  }
}

function hiddenRiskStatusLabel(status: string): string {
  if (status === 'critical') return 'Critical'
  if (status === 'significant') return 'Significant'
  if (status === 'mild') return 'Mild'
  return 'None'
}

function hiddenRiskDetail(detail: any) {
  const title = tx(detail.title || detail.type || t('analysis.hiddenRisk'))
  if (lang.value === 'zh') {
    return { title, detail: detail.detail || '' }
  }
  if (detail.type === 'policy_mask') {
    const unhealed = (detail.unhealed || []).slice(0, 3).map((x: any) => `${tx(x.label)} ${x.score}`).join(', ')
    const healed = (detail.healed || []).slice(0, 3).map((x: any) => `${tx(x.label)} ${x.score}`).join(', ')
    return {
      title,
      detail: `Policy-sensitive indicators have cooled, but structural stress remains. ${unhealed ? `Structural stress: ${unhealed}.` : ''}${healed ? ` Policy-sensitive calm: ${healed}.` : ''}`,
    }
  }
  if (detail.type === 'surface_calm_deep_stress') {
    const stressed = (detail.stressed_indicators || []).slice(0, 4).map((id: string) => tx(nodeNames[id] || id)).join(', ')
    const calm = (detail.calm_indicators || []).slice(0, 4).map((id: string) => tx(nodeNames[id] || id)).join(', ')
    return {
      title,
      detail: `Headline indicators look calmer than structural indicators. ${stressed ? `Deep-stress indicators: ${stressed}.` : ''}${calm ? ` Calmer headline indicators: ${calm}.` : ''}`,
    }
  }
  if (detail.type === 'zscore_desensitized') {
    const ids = (detail.desensitized_indicators || []).slice(0, 4).map((id: string) => tx(nodeNames[id] || id)).join(', ')
    return {
      title,
      detail: `Some indicators remain dangerous by absolute level even though their recent rate of change has normalized. ${ids ? `Desensitized indicators: ${ids}.` : ''}`,
    }
  }
  return { title, detail: tx(detail.detail || '') }
}

function avg(values: number[]): number {
  return values.length ? values.reduce((s, x) => s + x, 0) / values.length : 0
}

const topNodeContributions = computed(() => {
  const nc = riskStore.latest?.node_contributions
  if (!nc) return []
  return Object.entries(nc)
    .map(([id, info]: [string, any]) => {
      const zscore = Number(info.zscore || 0)
      const anomaly = Number(info.anomaly_score || 0)
      const absScore = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
      return {
        id,
        name: tx(info.display_name || nodeNames[id] || id),
        zscore,
        anomalyScore: anomaly,
        absScore,
        absScoreDisplay: absScore === null ? '-' : (absScore * 100).toFixed(0),
        currentDisplay: formatCurrentValue(info.current_value),
        sortScore: Math.max(Math.abs(zscore) / 4, anomaly, absScore || 0),
      }
    })
    .sort((a, b) => b.sortScore - a.sortScore)
    .slice(0, 8)
})

const subIndexRows = computed(() => {
  const details = riskStore.latest?.sub_index_details || {}
  return Object.entries(details)
    .map(([key, val]: [string, any]) => ({
      id: key,
      name: tx(val?.name || key),
      score: Number(val?.score || 0),
      anomalyStress: Number(val?.mean_stress || 0) * 100,
      absoluteStress: Number(val?.mean_abs_stress || 0) * 100,
      transmission: Number(val?.transmission || 0) * 100,
      topDriver: tx(nodeNames[val?.top_driver] || val?.top_driver || '-'),
    }))
    .sort((a, b) => b.score - a.score)
})

const selectedSubIndexReceipt = computed<SubIndexReceipt | null>(() => {
  const receipts = modelFoundation.value?.sub_index_receipts || {}
  if (receipts[selectedSubIndexId.value]) return receipts[selectedSubIndexId.value]
  const first = Object.keys(receipts)[0]
  return first ? receipts[first] : null
})

function sourceTierSummaryText(summary: Record<string, number>): string {
  return Object.entries(summary || {})
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([tier, count]) => `${tier}:${count}`)
    .join(' · ') || '-'
}

function currentSubIndexScore(key: string): number {
  const details = riskStore.latest?.sub_index_details || {}
  return Number((details as any)[key]?.score || 0)
}

function extractHiddenRiskIndicatorIds(): string[] {
  const details = riskStore.latest?.divergence?.details
  if (!Array.isArray(details)) return []
  const ids = new Set<string>()
  const add = (id: any) => {
    if (typeof id === 'string' && id.trim()) ids.add(id)
  }
  for (const detail of details) {
    ;(detail.desensitized_indicators || []).forEach(add)
    ;(detail.stressed_indicators || []).forEach(add)
    ;(detail.calm_indicators || []).forEach(add)
    ;(detail.indicators || []).forEach((x: any) => add(x?.id || x))
    ;(detail.unhealed || []).forEach((x: any) => add(x?.id))
    ;(detail.healed || []).forEach((x: any) => add(x?.id))
    ;(detail.leading_warnings || []).forEach((x: any) => add(x?.id))
  }
  return Array.from(ids)
}

function indicatorWatchItem(id: string) {
  const info: any = (riskStore.latest?.node_contributions || {})[id] || {}
  const zscore = Number(info.zscore || 0)
  const absScore = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
  return {
    id,
    name: tx(info.display_name || nodeNames[id] || id),
    reason: indicatorReason(id),
    currentDisplay: formatCurrentValue(info.current_value),
    zscore,
    zscoreDisplay: zscore.toFixed(2),
    absScoreDisplay: absScore === null ? '-' : (absScore * 100).toFixed(0),
  }
}

function indicatorReason(id: string): string {
  const hiddenIds = new Set(extractHiddenRiskIndicatorIds())
  const activeChain = activeChains.value.find((chain: any) => (chain.path || []).includes(id))
  if (lang.value === 'zh') {
    if (hiddenIds.has(id)) return '隐藏风险证据'
    if (activeChain) return '活跃传导链节点'
    if (id === topNodeContributions.value[0]?.id) return '首要驱动'
    return '重点观察'
  }
  if (hiddenIds.has(id)) return 'Hidden-risk evidence'
  if (activeChain) return 'Active-chain node'
  if (id === topNodeContributions.value[0]?.id) return 'Top driver'
  return 'Watch item'
}

function isIndicatorWatched(id: string): boolean {
  return riskWatch.isWatched('indicator', id)
}

function isWatched(type: RiskWatchType, id: string): boolean {
  return riskWatch.isWatched(type, id)
}

function toggleIndicatorWatch(id: string) {
  selectedWatchIndicatorId.value = id
  const item = indicatorWatchItem(id)
  riskWatch.toggle({
    type: 'indicator',
    id,
    label: item.name,
    reason: item.reason,
  })
}

function toggleWatchCard(card: EvidenceCard) {
  if (!card.watchType || !card.watchId) return
  if (card.watchType === 'indicator') selectedWatchIndicatorId.value = card.watchId
  riskWatch.toggle({
    type: card.watchType,
    id: card.watchId,
    label: card.watchLabel || card.title,
    reason: card.watchReason || card.kicker,
  })
}

function scrollToSection(id: string) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function openChainDetail(id: string) {
  expandedChainId.value = id
  scrollToSection('chain-pressure')
}

function buildIndicatorExplanation(id: string, node: any): string {
  const name = node?.name || tx(nodeNames[id] || id)
  const z = Number(node?.zscore || 0)
  const absRaw = node?.absScore === null || node?.absScore === undefined ? null : Number(node.absScore)
  const abs = absRaw === null ? null : absRaw * 100
  const zText = Math.abs(z) >= 2
    ? (lang.value === 'zh' ? '近期变化已经明显偏离历史波动' : 'recent movement is materially outside historical volatility')
    : (lang.value === 'zh' ? '近期变化并不极端' : 'recent movement is not extreme')
  const absText = abs === null
    ? (lang.value === 'zh' ? '当前缺少绝对压力阈值' : 'no absolute-stress threshold is available')
    : abs >= 75
      ? (lang.value === 'zh' ? '但当前水平本身已经处在高压区' : 'but the current level itself is in a high-stress zone')
      : abs >= 40
        ? (lang.value === 'zh' ? '当前水平处于中等压力区' : 'the current level is in a medium-stress zone')
        : (lang.value === 'zh' ? '当前水平压力不高' : 'the current level is not highly stressed')
  if (lang.value === 'zh') {
    return `${name} 被选中是因为它在今天的方向性压力排序中贡献较高。Z=${z.toFixed(2)} 表示${zText}；方向性压力分 ${((node?.anomalyScore || 0) * 100).toFixed(0)} 表示该变化是否朝风险方向移动；绝对压力 ${node?.absScoreDisplay || '-'} 表示${absText}。如果它同时处在传导链中，就需要观察是否从单点压力扩散为链式压力。`
  }
  return `${name} is selected because it contributes materially to today’s directional pressure ranking. Z=${z.toFixed(2)} means ${zText}; directional pressure ${((node?.anomalyScore || 0) * 100).toFixed(0)} shows whether the move is in the risk direction; absolute stress ${node?.absScoreDisplay || '-'} means ${absText}. If it is also inside an active chain, watch whether isolated pressure spreads into chain pressure.`
}

const subIndexBreakdownOption = computed(() => ({
  backgroundColor: 'transparent',
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: '#111214',
    borderColor: 'rgba(255,255,255,0.08)',
    textStyle: { color: '#eff1f5', fontSize: 11 },
  },
  legend: {
    top: 0,
    right: 0,
    textStyle: { color: '#8a93a3', fontSize: 10 },
    itemWidth: 9,
    itemHeight: 9,
  },
  grid: { left: 126, right: 18, top: 34, bottom: 18 },
  xAxis: {
    type: 'value',
    max: 100,
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } },
    axisLabel: { color: '#8a93a3', fontSize: 10 },
  },
  yAxis: {
    type: 'category',
    data: subIndexRows.value.map(r => r.name),
    axisLabel: { color: '#d6d9df', fontSize: 10, width: 112, overflow: 'truncate' },
    axisLine: { show: false },
    axisTick: { show: false },
  },
  series: [
    {
      name: t('analysis.anomalyStress'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.anomalyStress, 100)),
      itemStyle: { color: COLORS.yellow },
      barWidth: 12,
    },
    {
      name: t('analysis.absoluteStress'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.absoluteStress, 100)),
      itemStyle: { color: COLORS.orange },
      barWidth: 12,
    },
    {
      name: t('analysis.transmissionAmp'),
      type: 'bar',
      stack: 'stress',
      data: subIndexRows.value.map(r => Math.min(r.transmission, 100)),
      itemStyle: { color: COLORS.blue },
      barWidth: 12,
    },
  ],
}))

const chainPressureRows = computed(() => {
  return sortedChains.value.map((chain: any) => ({
    id: chain.id,
    name: tx(chain.name),
    path: (chain.path || []).map((n: string) => tx(nodeNames[n] || n)).join(' -> '),
    stress: Number(chain.stress || 0),
    pathStrength: Number(chain.path_strength || 0).toFixed(4),
    edgeDetails: (chain.edge_details || []).map((edge: string) => edge),
    nodes: chainDetailNodes(chain),
    stressFormula: buildChainStressFormula(chain),
    pathFormula: buildPathStrengthFormula(chain),
  }))
})

function toggleChainDetail(id: string) {
  expandedChainId.value = expandedChainId.value === id ? '' : id
}

function chainDetailNodes(chain: any) {
  const scores = chain.node_scores || {}
  const nc = riskStore.latest?.node_contributions || {}
  return (chain.path || []).map((id: string) => {
    const info = (nc as any)[id] || {}
    const anomaly = Number(scores[id] ?? info.anomaly_score ?? 0)
    const zscore = Number(info.zscore || 0)
    const absScore = info.abs_score === null || info.abs_score === undefined ? null : Number(info.abs_score)
    return {
      id,
      name: tx(info.display_name || nodeNames[id] || id),
      currentDisplay: formatCurrentValue(info.current_value),
      zscoreDisplay: zscore.toFixed(2),
      anomalyDisplay: (anomaly * 100).toFixed(0),
      absScoreDisplay: absScore === null ? '-' : (absScore * 100).toFixed(0),
      anomaly,
    }
  })
}

function buildChainStressFormula(chain: any): string {
  const nodes = chainDetailNodes(chain)
  if (!nodes.length) return '-'
  const values = nodes.map((n: any) => `${n.name} ${n.anomalyDisplay}`).join(' + ')
  const avg = Number(chain.stress || 0).toFixed(1)
  return `Chain Stress = average(node anomaly scores) x 100 = (${values}) / ${nodes.length} = ${avg}`
}

function buildPathStrengthFormula(chain: any): string {
  const details = chain.edge_details || []
  const strength = Number(chain.path_strength || 0).toFixed(4)
  if (!details.length) return `Path Strength = product(edge causal strengths) = ${strength}`
  return `Path Strength = product(edge causal strengths) = ${details.join(' x ')} = ${strength}`
}

function chainNodeBars(chain: any) {
  const scores = chain.node_scores || {}
  return (chain.path || []).map((id: string) => {
    const score = Number(scores[id] || 0)
    return {
      id,
      name: tx(nodeNames[id] || id),
      score,
      width: Math.min(score * 100, 100),
    }
  })
}

function formatCurrentValue(value: any): string {
  if (value === null || value === undefined) return '-'
  const n = Number(value)
  if (!Number.isFinite(n)) return String(value)
  if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 0 })
  return n.toLocaleString(undefined, { maximumFractionDigits: 2 })
}

function scoreColor(score: number): string {
  if (score >= 70) return COLORS.red
  if (score >= 45) return COLORS.orange
  if (score >= 25) return COLORS.yellow
  return COLORS.green
}

</script>

<style scoped>
.judgment-workbench {
  border-top: 1px solid var(--border);
  margin-top: 22px;
  padding-top: 18px;
}

.explain-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.explain-card,
.action-panel {
  background: rgba(255,255,255,0.014);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px;
}

.explain-card-head,
.action-head {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.explain-card-head p,
.indicator-metrics span {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.explain-card-head strong,
.action-head span {
  color: var(--accent);
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  text-align: right;
}

.explain-card h3,
.action-head h3 {
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
  line-height: 1.35;
  margin-top: 8px;
}

.explain-card > p {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.65;
  margin-top: 8px;
}

.evidence-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.explain-card button,
.plain-link {
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--accent);
  font-size: 11px;
  padding: 6px 9px;
}

.explain-card button:hover,
.plain-link:hover,
.related-chain-list button:hover {
  border-color: rgba(129,140,248,0.45);
  color: var(--text);
}

.action-workbench {
  display: grid;
  gap: 12px;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.9fr);
  margin-top: 12px;
}

.watch-chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.watch-chip {
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--muted);
  display: grid;
  gap: 3px;
  max-width: 210px;
  min-height: 54px;
  padding: 8px 10px;
  text-align: left;
}

.watch-chip span {
  color: var(--text);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.watch-chip small {
  color: var(--muted);
  font-size: 10px;
}

.watch-chip-active {
  background: rgba(129,140,248,0.10);
  border-color: rgba(129,140,248,0.48);
}

.indicator-detail {
  margin-top: 12px;
}

.indicator-metrics {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 10px;
}

.indicator-metrics div {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px;
}

.indicator-metrics strong {
  color: var(--text);
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 14px;
  font-weight: 500;
  margin-top: 5px;
}

.related-chain-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.related-chain-list button {
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 10px;
  padding: 5px 8px;
}

.receipt-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}

.receipt-tabs button {
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 10px;
  padding: 5px 8px;
}

.receipt-tab-active {
  background: rgba(129,140,248,0.12);
  border-color: rgba(129,140,248,0.45) !important;
  color: var(--text) !important;
}

.formula-receipt {
  border: 1px solid var(--border);
  border-radius: 10px;
  margin-top: 12px;
  padding: 14px;
}

.formula-receipt-head {
  align-items: flex-start;
  display: flex;
  gap: 12px;
  justify-content: space-between;
}

.formula-receipt-head p,
.formula-steps span,
.receipt-node-head span {
  color: var(--muted);
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.formula-receipt-head h3 {
  color: var(--text);
  font-size: 13px;
  font-weight: 500;
  margin-top: 4px;
}

.formula-receipt-head > span {
  color: var(--accent);
  flex: 0 0 auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
}

.formula-steps {
  display: grid;
  gap: 8px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-top: 12px;
}

.formula-steps div {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px;
}

.formula-steps strong {
  color: var(--text);
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 15px;
  font-weight: 500;
  margin-top: 4px;
}

.formula-text,
.formula-limit {
  color: var(--muted);
  font-size: 11px;
  line-height: 1.6;
  margin-top: 10px;
}

.receipt-node-table {
  border: 1px solid var(--border);
  border-radius: 8px;
  margin-top: 12px;
  overflow: hidden;
}

.receipt-node-row {
  align-items: center;
  border-top: 1px solid rgba(255,255,255,0.05);
  display: grid;
  gap: 8px;
  grid-template-columns: minmax(0, 1.25fr) 0.75fr 0.55fr 0.55fr 0.45fr;
  min-height: 32px;
  padding: 0 10px;
}

.receipt-node-row:first-child {
  border-top: 0;
}

.receipt-node-row span {
  color: var(--muted);
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.receipt-node-row span:first-child {
  color: var(--text);
  font-family: inherit;
}

.tier-A { color: var(--green) !important; }
.tier-B { color: var(--yellow) !important; }
.tier-C { color: var(--orange) !important; }
.tier-D { color: var(--red) !important; }

.judgment-markdown :deep(h1),
.judgment-markdown :deep(h2),
.judgment-markdown :deep(h3) {
  font-size: 15px;
  line-height: 1.45;
  margin-top: 0.8em;
  margin-bottom: 0.45em;
}

.judgment-markdown :deep(p),
.judgment-markdown :deep(li) {
  color: var(--muted);
  line-height: 1.65;
}

.judgment-markdown :deep(ul),
.judgment-markdown :deep(ol) {
  padding-left: 1.2em;
}

@media (max-width: 1180px) {
  .explain-grid,
  .action-workbench {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 720px) {
  .indicator-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
