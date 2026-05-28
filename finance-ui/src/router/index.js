import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../ui/views/Dashboard.vue'
import EntitiesView from '../ui/views/EntitiesView.vue'
import UploadView from '../ui/views/UploadView.vue'
import TransactionsView from '../ui/views/TransactionsView.vue'
import BudgetView from '../ui/views/BudgetView.vue'
import RetirementView from '../ui/views/RetirementView.vue'
import EntityDetail from '../ui/views/EntityDetail.vue'

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: Dashboard
  },
  {
    path: '/entities',
    name: 'entities',
    component: EntitiesView
  },
  {
    path: '/entity/:name',
    name: 'entity-detail',
    component: EntityDetail,
    props: true
  },
  {
    path: '/upload',
    name: 'upload',
    component: UploadView
  },
  {
    path: '/transactions',
    name: 'transactions',
    component: TransactionsView
  },
  {
    path: '/budget',
    name: 'budget',
    component: BudgetView
  },
  {
    path: '/retirement',
    name: 'retirement',
    component: RetirementView
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
