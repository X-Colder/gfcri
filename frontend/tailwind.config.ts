/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: '#08090a',
        card: '#111214',
        border: 'rgba(255,255,255,0.06)',
        muted: '#6b7280',
        'alert-green': '#34d399',
        'alert-yellow': '#fbbf24',
        'alert-orange': '#f97316',
        'alert-red': '#ef4444',
        accent: '#818cf8',
        purple: '#a78bfa',
      },
      fontFamily: {
        sans: ['DM Sans', 'Noto Sans SC', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
