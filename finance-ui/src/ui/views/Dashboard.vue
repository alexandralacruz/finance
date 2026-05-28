<template>
  <div class="p-6">
    <!-- Header -->
    <div class="flex items-center justify-between mb-6">
      <div>
        <h1 class="text-2xl font-bold text-gray-800">Dashboard</h1>
        <p class="text-sm text-gray-500">Resumen financiero consolidado</p>
      </div>

      <div class="flex items-center gap-4">
        <!-- Currency toggle -->
        <div class="flex bg-gray-200 rounded-lg p-0.5">
          <button
            v-for="c in ['USD', 'COP']"
            :key="c"
            @click="currency = c"
            class="px-4 py-1.5 rounded-md text-sm font-medium transition-colors"
            :class="currency === c ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-600 hover:text-gray-800'"
          >{{ c }}</button>
        </div>

        <!-- Year selector -->
        <select
          v-model="selectedYear"
          class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
        </select>

        <!-- Exchange rate -->
        <span class="text-sm text-gray-500 bg-white rounded-lg px-3 py-1.5 border border-gray-200">
          💱 {{ rateLabel }}
        </span>
      </div>
    </div>

    <!-- Summary cards -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-12 w-12 border-4 border-blue-200 border-t-blue-600"></div>
    </div>

    <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
      <div class="glass-card rounded-2xl p-6">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Saldo Total</p>
        <p class="text-2xl font-bold text-blue-700">{{ fmt(summary.totalBalance) }}</p>
      </div>
      <div class="glass-card rounded-2xl p-6">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Entidades Activas</p>
        <p class="text-2xl font-bold text-gray-700">{{ summary.entities }}</p>
      </div>
      <div class="glass-card rounded-2xl p-6">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Ingresos del año</p>
        <p class="text-2xl font-bold text-green-600">{{ fmt(summary.income) }}</p>
      </div>
      <div class="glass-card rounded-2xl p-6">
        <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Egresos del año</p>
        <p class="text-2xl font-bold text-red-500">{{ fmt(summary.expenses) }}</p>
      </div>
    </div>

    <!-- Charts row -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      <!-- Entity balances -->
      <div class="glass-card rounded-2xl p-6">
        <h3 class="text-sm font-semibold text-gray-600 mb-4">Saldo por Entidad</h3>
        <div v-if="entities.length" class="space-y-3">
          <div v-for="e in entities" :key="e.name" class="flex justify-between items-center">
            <span class="text-sm text-gray-700 font-medium">{{ e.name }}</span>
            <span class="text-sm font-bold" :class="e.balance >= 0 ? 'text-green-600' : 'text-red-500'">
              {{ fmt(e.balance) }}
            </span>
          </div>
        </div>
        <p v-else class="text-sm text-gray-400">Sin datos</p>
      </div>

      <!-- Monthly timeline -->
      <div class="glass-card rounded-2xl p-6 lg:col-span-2">
        <h3 class="text-sm font-semibold text-gray-600 mb-4">Evolución Mensual</h3>
        <div v-if="monthly.length" class="h-64">
          <LineChart :chart-data="chartData" :chart-options="chartOptions" />
        </div>
        <p v-else class="text-sm text-gray-400">Sin datos</p>
      </div>
    </div>

    <!-- Entity quick list -->
    <div class="glass-card rounded-2xl p-6">
      <h3 class="text-sm font-semibold text-gray-600 mb-4">Resumen por Entidad</h3>
      <div v-if="entityBalances.length" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        <router-link
          v-for="eb in entityBalances"
          :key="eb.ENTIDAD"
          :to="`/entity/${eb.ENTIDAD}`"
          class="flex justify-between items-center p-4 rounded-xl border border-gray-100 hover:border-blue-200 hover:bg-blue-50/50 transition-colors"
        >
          <span class="font-medium text-gray-700">{{ eb.ENTIDAD }}</span>
          <span class="font-bold text-sm" :class="eb.BALANCE_FINAL >= 0 ? 'text-green-600' : 'text-red-500'">
            {{ fmt(eb.BALANCE_FINAL) }}
          </span>
        </router-link>
      </div>
      <p v-else class="text-sm text-gray-400">Sin entidades con datos para {{ selectedYear }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import LineChart from '../components/charts/LineChart.vue'

const API_URL = import.meta.env.VITE_API_URL

const currency = ref('USD')
const selectedYear = ref(new Date().getFullYear())
const years = ref([])
const rate = ref(4000)
const loading = ref(false)
const summary = ref({ totalBalance: 0, entities: 0, income: 0, expenses: 0 })
const entities = ref([])
const monthly = ref([])
const entityBalances = ref([])

const MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']

const rateLabel = computed(() => {
  return `1 USD = ${rate.value.toLocaleString()} COP`
})

const fmt = (v) => {
  if (v == null) return '$0'
  return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v)
}

// Chart data
const chartData = computed(() => ({
  labels: monthly.value.map(m => MONTHS[Number(m.MES.split('-')[1]) - 1] || ''),
  datasets: [
    {
      label: `Saldo (${currency.value})`,
      data: monthly.value.map(m => m.total_balance),
      borderColor: '#2563EB',
      borderWidth: 3,
      tension: 0.3,
      fill: false,
    },
    {
      label: 'Ingresos',
      data: monthly.value.map(m => m.income),
      borderColor: '#16A34A',
      borderDash: [5, 5],
      tension: 0.3,
      fill: false,
    },
    {
      label: 'Gastos',
      data: monthly.value.map(m => m.expenses),
      borderColor: '#DC2626',
      borderDash: [5, 5],
      tension: 0.3,
      fill: false,
    },
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
  },
  scales: {
    y: { beginAtZero: true },
  },
}

async function fetchRate() {
  try {
    const res = await fetch(`${API_URL}/exchange-rate?target=USD`)
    const data = await res.json()
    // exchangerate-api returns COP→USD; invert to USD→COP
    rate.value = Math.round(1 / data.rate)
  } catch (e) {
    console.error('Rate error:', e)
  }
}

async function fetchYears() {
  try {
    const res = await fetch(`${API_URL}/years`)
    const data = await res.json()
    years.value = Array.isArray(data.years) ? data.years : [selectedYear.value]
  } catch (e) {
    years.value = [selectedYear.value]
  }
}

async function fetchAll() {
  loading.value = true
  try {
    const [sumRes, entRes, monRes] = await Promise.all([
      fetch(`${API_URL}/summary/${selectedYear.value}?currency=${currency.value}`),
      fetch(`${API_URL}/byEntity/${selectedYear.value}?currency=${currency.value}`),
      fetch(`${API_URL}/byMonth/${selectedYear.value}?currency=${currency.value}`),
    ])

    if (sumRes.ok) {
      const data = await sumRes.json()
      summary.value = {
        totalBalance: data.totalBalance || 0,
        entities: data.entities || 0,
        income: data.income || 0,
        expenses: data.expenses || 0,
      }
      entityBalances.value = data.entityBalances || []
    }

    if (entRes.ok) {
      const data = await entRes.json()
      entities.value = (data.entities || []).map(e => ({
        name: e.ENTIDAD,
        balance: e.BALANCE_FINAL,
      }))
    }

    if (monRes.ok) {
      monthly.value = await monRes.json()
    }
  } catch (e) {
    console.error('Fetch error:', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchRate()
  await fetchYears()
  await fetchAll()
})

watch([selectedYear, currency], () => fetchAll())
</script>
