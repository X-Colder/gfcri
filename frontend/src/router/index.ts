import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/auth',
      name: 'auth',
      component: () => import('@/views/AuthView.vue'),
    },
    {
      path: '/',
      component: () => import('@/components/layout/AppLayout.vue'),
      children: [
        { path: '', name: 'dashboard', component: () => import('@/views/DashboardView.vue') },
        { path: 'institutional', name: 'institutional', component: () => import('@/views/InstitutionalView.vue') },
        { path: 'analysis', name: 'analysis', component: () => import('@/views/AnalysisView.vue') },
        { path: 'forward', name: 'forward', component: () => import('@/views/ForwardView.vue') },
        { path: 'backtest', name: 'backtest', component: () => import('@/views/BacktestView.vue') },
        { path: 'pricing', name: 'pricing', component: () => import('@/views/PricingView.vue') },
        { path: 'methodology', name: 'methodology', component: () => import('@/views/MethodologyView.vue') },
        // Legacy redirects
        { path: 'briefing', redirect: '/analysis' },
        { path: 'risk-detail', redirect: '/analysis' },
        { path: 'stress-test', redirect: '/forward' },
        { path: 'ehs', redirect: '/forward' },
        { path: 'industries', redirect: '/institutional' },
        { path: 'industry', redirect: '/institutional' },
        { path: 'industry-graph', redirect: '/institutional' },
        { path: 'social', redirect: '/' },
        { path: 'causal-graph', redirect: '/' },
        { path: 'inference', redirect: '/' },
      ],
    },
  ],
})

export default router
