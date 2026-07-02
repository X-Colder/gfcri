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
        { path: 'analysis', name: 'analysis', component: () => import('@/views/AnalysisView.vue') },
        { path: 'forward', name: 'forward', component: () => import('@/views/ForwardView.vue') },
        { path: 'backtest', name: 'backtest', component: () => import('@/views/BacktestView.vue') },
        { path: 'industries', name: 'industries', component: () => import('@/views/IndustryView.vue') },
        { path: 'methodology', name: 'methodology', component: () => import('@/views/MethodologyView.vue') },
        // Legacy redirects
        { path: 'briefing', redirect: '/analysis' },
        { path: 'risk-detail', redirect: '/analysis' },
        { path: 'stress-test', redirect: '/forward' },
        { path: 'ehs', redirect: '/forward' },
        { path: 'industry', redirect: '/industries' },
        { path: 'industry-graph', redirect: '/industries' },
        { path: 'social', redirect: '/' },
        { path: 'causal-graph', redirect: '/' },
        { path: 'inference', redirect: '/' },
      ],
    },
  ],
})

export default router
