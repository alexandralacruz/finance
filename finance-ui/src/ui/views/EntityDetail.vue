<template>
  <div class="p-6">
    <div class="flex items-center gap-3 mb-6">
      <router-link to="/entities" class="text-gray-400 hover:text-gray-600 text-xl">&larr;</router-link>
      <div>
        <h1 class="text-2xl font-bold text-gray-800">{{ name }}</h1>
        <p class="text-sm text-gray-500" v-if="accounts.length">{{ accounts.length }} cuenta(s) · {{ displayCurrency }}</p>
      </div>
    </div>

    <!-- Accounts cards -->
    <div v-if="accounts.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
      <div v-for="acct in accounts" :key="acct.id" class="glass-card rounded-2xl p-5">
        <div class="flex items-center justify-between mb-2">
          <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">{{ accountTypeLabel(acct.account_type) }}</span>
          <span class="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ acct.currency }}</span>
        </div>
        <p class="text-xl font-bold" :class="(acct.balance || 0) >= 0 ? 'text-blue-700' : 'text-red-500'">
          {{ fmtCurrency(acct.balance, acct.currency) }}
        </p>
      </div>
    </div>

    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
    </div>

    <!-- Transactions table -->
    <div class="glass-card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">
        Últimas transacciones
        <span class="text-sm font-normal text-gray-400 ml-2">({{ totalTxCount || transactions.length }})</span>
      </h2>
      <div v-if="transactions.length" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-gray-500">
              <th class="text-left py-2 px-3">Fecha</th>
              <th class="text-left py-2 px-3">Descripción</th>
              <th class="text-right py-2 px-3">Monto</th>
              <th class="text-right py-2 px-3">Balance</th>
              <th class="text-left py-2 px-3">Tipo</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="tx in transactions"
              :key="tx.id"
              class="border-b border-gray-100 hover:bg-gray-50"
            >
              <td class="py-2 px-3 text-gray-500 whitespace-nowrap">{{ tx.date }}</td>
              <td class="py-2 px-3 text-gray-700 max-w-xs truncate">{{ tx.description }}</td>
              <td class="py-2 px-3 text-right font-medium whitespace-nowrap" :class="tx.amount >= 0 ? 'text-green-600' : 'text-red-500'">
                {{ fmtCurrency(tx.amount, displayCurrency) }}
              </td>
              <td class="py-2 px-3 text-right text-gray-500 whitespace-nowrap">
                {{ tx.balance != null ? fmtCurrency(tx.balance, displayCurrency) : '—' }}
              </td>
              <td class="py-2 px-3">
                <span class="text-xs px-1.5 py-0.5 rounded-full" :class="typeBadgeClass(tx.type)">
                  {{ tx.type === 'balance' ? 'saldo' : tx.type }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Load more button -->
        <div v-if="hasMore" class="text-center mt-4">
          <button
            @click="loadMore"
            :disabled="loadingMore"
            class="text-sm text-blue-600 hover:text-blue-800 font-medium disabled:opacity-50"
          >
            {{ loadingMore ? 'Cargando...' : `Cargar más (${pageSize} más)` }}
          </button>
        </div>
      </div>
      <p v-else class="text-sm text-gray-400 py-8 text-center">Sin transacciones</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({ name: String })
const API_URL = import.meta.env.VITE_API_URL

const accounts = ref([])
const transactions = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const displayCurrency = ref('COP')
const pageSize = 10
const currentOffset = ref(0)
const hasMore = ref(false)
const totalTxCount = ref(0)

const accountTypeLabels = {
  checking: 'Corriente', savings: 'Ahorro', cdt: 'CDT',
  pension: 'Pensión', cesantias: 'Cesantías', spot: 'Spot',
  earn: 'Earn', futures: 'Futures', investment_fund: 'Fondo inversión',
  other: 'Otro',
}
const accountTypeLabel = (t) => accountTypeLabels[t] || t

function fmtCurrency(v, currency) {
  if (v == null) return '$0'
  const c = currency || displayCurrency.value || 'COP'
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: c === 'COP' ? 'COP' : 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(v)
}

function typeBadgeClass(type) {
  switch (type) {
    case 'balance': return 'bg-purple-100 text-purple-700'
    case 'income': case 'freelance': case 'deposit': return 'bg-green-100 text-green-700'
    case 'expense': case 'withdrawal': return 'bg-red-100 text-red-700'
    case 'investment': return 'bg-blue-100 text-blue-700'
    default: return 'bg-gray-100 text-gray-600'
  }
}

async function fetchData() {
  loading.value = true
  try {
    // Get entity data
    const entityRes = await fetch(`${API_URL}/entities`)
    const entities = await entityRes.json()
    const entity = entities.find(e => e.name === props.name)
    if (!entity) return

    // Get all balances (includes accounts for this entity)
    const balancesRes = await fetch(`${API_URL}/balances`)
    const balances = await balancesRes.json()
    accounts.value = balances.filter(b => b.entity === props.name)

    // Determine display currency from first account
    if (accounts.value.length > 0) {
      const c = accounts.value[0].currency
      displayCurrency.value = ['COP', 'USD', 'EUR'].includes(c) ? c : 'USD'
    }

    // Load first page of transactions
    await loadTransactions(0)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadTransactions(offset) {
  const fromDate = '2020-01-01'
  const toDate = new Date().toISOString().slice(0, 10)
  try {
    const txRes = await fetch(
      `${API_URL}/entity/${props.name}/range?from=${fromDate}&to=${toDate}&currency=${displayCurrency.value}`
    )
    if (txRes.ok) {
      const data = await txRes.json()
      totalTxCount.value = data.transaction_count || 0
      const allTx = (data.transactions || []).map(tx => ({
        ...tx,
        account_type: '—',
        currency: displayCurrency.value,
      }))
      // Apply pagination
      const end = offset + pageSize
      transactions.value = offset === 0 ? allTx.slice(0, pageSize) : allTx.slice(0, end)
      currentOffset.value = end
      hasMore.value = end < allTx.length
    }
  } catch (e) {
    console.error(e)
  }
}

async function loadMore() {
  loadingMore.value = true
  try {
    const fromDate = '2020-01-01'
    const toDate = new Date().toISOString().slice(0, 10)
    const txRes = await fetch(
      `${API_URL}/entity/${props.name}/range?from=${fromDate}&to=${toDate}&currency=${displayCurrency.value}`
    )
    if (txRes.ok) {
      const data = await txRes.json()
      const allTx = (data.transactions || []).map(tx => ({
        ...tx,
        account_type: '—',
        currency: displayCurrency.value,
      }))
      const end = currentOffset.value + pageSize
      transactions.value = allTx.slice(0, end)
      currentOffset.value = end
      hasMore.value = end < allTx.length
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingMore.value = false
  }
}

onMounted(fetchData)
</script>
