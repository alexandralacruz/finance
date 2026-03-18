<template>
  <div class="dashboard">
    <Header
      v-model="selectedYear"
      :rate="rate"
      :rateDate="rateDate"
      :loading="loading"
      :years="availableYears"
      :currency="balanceCurrency"
      @update:currency="updateCurrency"
      @refresh="fetchExchangeRate"
    />


    <Summary 
      :summary="summary" 
      :loading="loadingSummary"
      :currency="balanceCurrency"
    />
    
    <Balance
      :year="selectedYear"
      :currency="balanceCurrency"
      :rate="rate"
        />
    
  </div>
</template>

<script setup>

import { ref, onMounted, watch } from 'vue'
import Header from '../components/Header.vue'
import Summary from '../components/Summary.vue'
import Balance from '../components/Balance.vue'


const API_URL = import.meta.env.VITE_API_URL

//const balanceByEntity = ref([])
const balanceCurrency = ref('USD')

const rate = ref(0)
const rateDate = ref('')
const loading = ref(false)

const currentYear = new Date().getFullYear()
const selectedYear = ref(currentYear)
const availableYears = ref([])

//const activeMenu = ref('upload')
const hasData = ref(false)
const summary = ref({
  totalBalance: 0,
  activeEntities: 0,
  monthlyIncome: 0,
  monthlyExpenses: 0
})

const fetchExchangeRate = async () => {
  loading.value = true
  const res = await fetch(`${API_URL}/exchange-rate`)
  const data = await res.json()
  rate.value = data.rate
  rateDate.value = data.date
  loading.value = false
}

const fetchYears = async () => {
  const res = await fetch(`${API_URL}/years`)
  const data = await res.json()
  availableYears.value = data.years
}



const loadingSummary = ref(false)

async function fetchSummary(year, currency = 'USD') {
  loadingSummary.value = true

  try {
    const res = await fetch(`${API_URL}/summary/${year}?currency=${currency}&usd_to_cop=${rate.value}`)
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`)
    const data = await res.json()

    // Si tu API devuelve algo tipo { hasData: true, totalBalance: 123, ... }
    hasData.value = data.hasData ?? false
    summary.value = {
      totalBalance: data.totalBalance ?? 0,
      activeEntities: data.entities ?? 0,
      monthlyIncome: data.income ?? 0,
      monthlyExpenses: data.expenses ?? 0
    }
  } catch (err) {
    console.error("Error fetching summary:", err)
    hasData.value = false
    summary.value = {
      totalBalance: 0,
      activeEntities: 0,
      monthlyIncome: 0,
      monthlyExpenses: 0
    }
  } finally {
    loadingSummary.value = false
  }
}

function updateCurrency(newCurrency) {
  balanceCurrency.value = newCurrency
}

// Observa cambios en el año

watch(
  [selectedYear, balanceCurrency],
  ([year, currency]) => {
    fetchSummary(year, currency)
  }
)

// Al cargar
onMounted(() => {
  fetchExchangeRate()
  fetchYears()
  fetchSummary(selectedYear.value, balanceCurrency.value)
  
  
})

</script>


<style scoped>
.dashboard {
  font-family: Arial, sans-serif;
  background: #f0f2f5;
  min-height: 100vh;
}

.header {
  background: #e9ecef;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.summary {
  display: flex;
  gap: 20px;
  padding: 20px;
  flex-wrap: wrap;
}

.card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  text-align: center;
  min-width: 200px;
  flex: 1;
}

.card h3 {
  margin: 0 0 10px;
  font-size: 14px;
  color: #666;
}

.card p {
  font-size: 24px;
  margin: 0;
  font-weight: bold;
}

.main-content {
  display: flex;
}



.empty-state {
background: white;
padding: 40px;
border-radius: 8px;
text-align: center;
color: #666;
box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.empty-state.big {
margin-top: 40px;
font-size: 18px;
}

.year-selector select {
margin-left: 8px;
padding: 4px 8px;
}

.sidebar {
width: 220px;
background: linear-gradient(180deg, #1f2933, #111827);
color: #e5e7eb;
padding: 20px 15px;
min-height: calc(100vh - 60px); /* descuenta el header */
box-shadow: 2px 0 6px rgba(0, 0, 0, 0.15);
}

.sidebar ul {
list-style: none;
padding: 0;
margin: 0;
}

.sidebar li {
display: flex;
align-items: center;
gap: 12px;
padding: 12px 14px;
margin-bottom: 6px;
border-radius: 8px;
cursor: pointer;
font-size: 14px;
transition: background 0.2s ease, transform 0.1s ease;
}

.sidebar li:hover {
background: rgba(255, 255, 255, 0.08);
transform: translateX(4px);
}

.sidebar li.active {
background: rgba(59, 130, 246, 0.2);
color: #93c5fd;
font-weight: 600;
}

.sidebar li span {
font-size: 16px;
}


.content {
  flex: 1;
  padding: 20px;
}

.charts-row {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.chart-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  flex: 1;
  height: 380px;                /* Altura fija - ¡esto soluciona el estiramiento infinito! */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-card h3 {
  margin: 0 0 8px 0;
  flex-shrink: 0;
}

.filters {
  margin-bottom: 10px;
  font-size: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  flex-shrink: 0;
}

.table-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.table-filters {
  margin-bottom: 15px;
  display: flex;
  gap: 10px;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: left;
}

th {
  background: #f8f9fa;
}

/* El canvas del gráfico ocupa todo el espacio disponible */
.chart-card :deep(canvas) {
  flex: 1 !important;
  width: 100% !important;
  height: 100% !important;
}

/* Responsivo para móviles */
@media (max-width: 768px) {
  .charts-row {
    flex-direction: column;
  }
  .chart-card {
    height: 300px;
  }
}

.year-selector {
margin-top: 4px;
font-size: 13px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr; /* dos columnas */
  gap: 20px;
  padding: 20px;
}

.year-selector select {
margin-left: 6px;
padding: 4px 8px;
border-radius: 6px;
border: 1px solid #ccc;
}
</style>