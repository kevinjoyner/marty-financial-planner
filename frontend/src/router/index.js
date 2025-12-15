import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'
import IncomeView from '../views/IncomeView.vue'
import AccountsView from '../views/AccountsView.vue'
import TransactionsView from '../views/TransactionsView.vue'
import AutomationView from '../views/AutomationView.vue'
import ScenariosView from '../views/ScenariosView.vue'
import TaxLimitsView from '../views/TaxLimitsView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/income', name: 'income', component: IncomeView },
    { path: '/accounts', name: 'accounts', component: AccountsView },
    { path: '/transactions', name: 'transactions', component: TransactionsView },
    { path: '/expenses', redirect: '/transactions' }, 
    { path: '/automation', name: 'automation', component: AutomationView },
    { path: '/tax', name: 'tax', component: TaxLimitsView },
    { path: '/scenarios', name: 'scenarios', component: ScenariosView }
  ]
})

export default router
