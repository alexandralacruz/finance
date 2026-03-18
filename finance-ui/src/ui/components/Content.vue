<template>
    <div class="content">
      <div class="charts-grid">
        <!-- Gráfico 1: Saldo por Entidad (Barras horizontales para mejor visual) -->
        <div class="chart-card">
          <h3>Saldo por Entidad</h3>
          <canvas ref="barChart"></canvas>
        </div>
  
        <!-- Gráfico 2: Evolución del Saldo -->
        <div class="chart-card">
          <h3>Evolución del Saldo</h3>
          <div class="filters">
            <span>Entidad:</span>
            <select v-model="selectedEntity">
              <option value="all">Todas</option>
              <option value="BC">BC</option>
              <option value="Amerant">Amerant</option>
            </select>
            <span>Rango:</span>
            <select v-model="selectedRange">
              <option value="6">Últimos 6 meses</option>
              <option value="12">Últimos 12 meses</option>
            </select>
          </div>
          <canvas ref="lineChart"></canvas>
        </div>

        <div class="chart-card">
            <h3>Saldo por Entidad</h3>
            <h3>Evolución del Saldo</h3>
        </div>
  
        <!-- Puedes agregar aquí los otros 2 del grid 2x2 más adelante -->
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, watch, nextTick } from 'vue'
  import Chart from 'chart.js/auto'
  
  defineProps(['year', 'rate'])
  
  // Datos de ejemplo (reemplazar después con fetch real)
  const balancesByEntity = ref({
    BC: 12430 * 0.75,     // ~9300 aprox
    Amerant: 12430 * 0.25  // ~3100 aprox
  })
  
  const monthlyEvolution = ref([
    { month: 'Ago 2025', value: 11800 },
    { month: 'Sep', value: 12050 },
    { month: 'Oct', value: 12400 },
    { month: 'Nov', value: 12100 },
    { month: 'Dic', value: 11900 },
    { month: 'Ene 2026', value: 12430 }
  ])
  
  const selectedEntity = ref('all')
  const selectedRange = ref('6')
  
  const barChart = ref(null)
  const lineChart = ref(null)
  
  let barInstance = null
  let lineInstance = null
  
  const createBarChart = () => {
    if (barInstance) barInstance.destroy()
    const ctx = barChart.value.getContext('2d')
  
    barInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: Object.keys(balancesByEntity.value),
        datasets: [{
          label: 'Saldo (USD)',
          data: Object.values(balancesByEntity.value),
          backgroundColor: '#1e40af',
          borderRadius: 6,
          barThickness: 60
        }]
      },
      options: {
        indexAxis: 'y', // ¡Barras horizontales como en la imagen!
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { display: false }, ticks: { display: false } },
          y: { grid: { display: false } }
        }
      }
    })
  }
  
  const createLineChart = () => {
    if (lineInstance) lineInstance.destroy()
    const ctx = lineChart.value.getContext('2d')
  
    const dataToShow = selectedRange.value === '6'
      ? monthlyEvolution.value.slice(-6)
      : monthlyEvolution.value
  
    lineInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dataToShow.map(d => d.month),
        datasets: [{
          label: 'Saldo Total',
          data: dataToShow.map(d => d.value),
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          tension: 0.4,
          fill: true,
          pointRadius: 4,
          pointBackgroundColor: '#3b82f6'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            ticks: {
              callback: value => '$' + value.toLocaleString()
            }
          }
        }
      }
    })
  }
  
  onMounted(async () => {
    await nextTick()
    createBarChart()
    createLineChart()
  })
  
  watch([selectedEntity, selectedRange], () => {
    createLineChart()
  })
  </script>
  
  <style scoped>
  .content {
    flex: 1;
    padding: 20px;
    background: #f0f2f5;
    overflow: auto;
  }
  
  .charts-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .chart-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-direction: column;
    height: 420px;
    
  }
  
  .chart-card h3 {
    margin: 0 0 16px 0;
    text-align: center;
    font-size: 16px;
    color: #333;
  }
  
  .filters {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 12px;
    font-size: 14px;
  }
  
  .filters select {
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid #ccc;
    background: white;
  }
  
  canvas {
    flex: 1;
  }
  
  /* Responsive: en móvil, uno debajo del otro */
  @media (max-width: 1024px) {
    .charts-grid {
      grid-template-columns: 1fr;
    }
    .chart-card {
      height: 380px;
    }
  }
  </style>