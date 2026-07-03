import { computed, ref } from 'vue'

export type RiskWatchType = 'indicator' | 'chain' | 'theme'

export type RiskWatchItem = {
  type: RiskWatchType
  id: string
  label?: string
  reason?: string
  addedAt: string
}

const STORAGE_KEY = 'gfcri_risk_watch_v1'
const LEGACY_CHAIN_KEY = 'gfcri_watched_chains'
const LEGACY_INDICATOR_KEY = 'gfcri_watched_indicators'

const items = ref<RiskWatchItem[]>(loadItems())

function loadItems(): RiskWatchItem[] {
  if (typeof window === 'undefined') return []
  const now = new Date().toISOString()
  const parsed = safeParse<RiskWatchItem[]>(localStorage.getItem(STORAGE_KEY), [])
  const merged = new Map<string, RiskWatchItem>()

  for (const item of parsed) {
    if (item?.type && item?.id) {
      merged.set(keyOf(item.type, item.id), {
        ...item,
        addedAt: item.addedAt || now,
      })
    }
  }

  for (const id of safeParse<string[]>(localStorage.getItem(LEGACY_CHAIN_KEY), [])) {
    if (id) merged.set(keyOf('chain', id), { type: 'chain', id, addedAt: now })
  }
  for (const id of safeParse<string[]>(localStorage.getItem(LEGACY_INDICATOR_KEY), [])) {
    if (id) merged.set(keyOf('indicator', id), { type: 'indicator', id, addedAt: now })
  }

  const result = Array.from(merged.values())
  persistItems(result)
  return result
}

function safeParse<T>(raw: string | null, fallback: T): T {
  if (!raw) return fallback
  try {
    return JSON.parse(raw) as T
  } catch {
    return fallback
  }
}

function keyOf(type: RiskWatchType, id: string): string {
  return `${type}:${id}`
}

function persistItems(next: RiskWatchItem[]) {
  if (typeof window === 'undefined') return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  localStorage.setItem(LEGACY_CHAIN_KEY, JSON.stringify(next.filter(x => x.type === 'chain').map(x => x.id)))
  localStorage.setItem(LEGACY_INDICATOR_KEY, JSON.stringify(next.filter(x => x.type === 'indicator').map(x => x.id)))
}

export function useRiskWatch() {
  function isWatched(type: RiskWatchType, id: string): boolean {
    return items.value.some(x => x.type === type && x.id === id)
  }

  function add(item: Omit<RiskWatchItem, 'addedAt'>) {
    if (isWatched(item.type, item.id)) return
    items.value = [...items.value, { ...item, addedAt: new Date().toISOString() }]
    persistItems(items.value)
  }

  function remove(type: RiskWatchType, id: string) {
    items.value = items.value.filter(x => !(x.type === type && x.id === id))
    persistItems(items.value)
  }

  function toggle(item: Omit<RiskWatchItem, 'addedAt'>) {
    if (isWatched(item.type, item.id)) remove(item.type, item.id)
    else add(item)
  }

  return {
    items,
    watchedChainIds: computed(() => items.value.filter(x => x.type === 'chain').map(x => x.id)),
    watchedIndicatorIds: computed(() => items.value.filter(x => x.type === 'indicator').map(x => x.id)),
    isWatched,
    add,
    remove,
    toggle,
  }
}
