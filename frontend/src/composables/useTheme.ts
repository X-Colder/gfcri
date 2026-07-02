export const COLORS = {
  bg: '#08090a',
  card: '#111214',
  border: 'rgba(255,255,255,0.06)',
  text: '#eff1f5',
  muted: '#6b7280',
  green: '#34d399',
  yellow: '#fbbf24',
  orange: '#f97316',
  red: '#ef4444',
  blue: '#60a5fa',
  accent: '#818cf8',
  purple: '#a78bfa',
} as const

export const ALERT_COLORS: Record<string, string> = {
  green: COLORS.green,
  yellow: COLORS.yellow,
  orange: COLORS.orange,
  red: COLORS.red,
}

export const ALERT_LABELS: Record<string, string> = {
  green: '正常',
  yellow: '关注',
  orange: '警告',
  red: '危险',
}

export const ASSET_CLASS_COLORS: Record<string, string> = {
  FX: '#60a5fa',
  RATES: '#f97316',
  EQUITY: '#34d399',
  CREDIT: '#ef4444',
  COMMODITY: '#fbbf24',
  MACRO: '#a78bfa',
  SENTIMENT: '#f97316',
}

export function getAlertColor(level: string): string {
  return ALERT_COLORS[level] || COLORS.muted
}

export function getAlertLabel(level: string): string {
  return ALERT_LABELS[level] || level
}
