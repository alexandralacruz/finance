
<script setup>
    import { reactive, watchEffect } from 'vue'
    import LineChart from '../components/charts/LineChart.vue'
    
    const props = defineProps({
      monthlyBalances: { type: Array, default: () => [] },
      currency: { type: String, default: 'USD' },
      loading: { type: Boolean, default: false }
    })
    
    const MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    function labelFromMES(mes) {
      if (!mes || !mes.includes('-')) return ''
      const monthIndex = Number(mes.split('-')[1]) - 1
      return MONTHS[monthIndex] || ''
    }
    
    /* ===== CHART DATA ===== */
    const chartData = reactive({
      labels: [],
      datasets: [
        {
          label: `Saldo (${props.currency})`,
          data: [],
          borderColor: '#2563EB',
          backgroundColor: '#2563EB',
          borderWidth: 3,
          tension: 0.3,
          fill: false
        },
        {
          label: 'Ingresos',
          data: [],
          borderColor: '#16A34A',
          backgroundColor: 'rgba(22,163,74,0.2)',
          borderDash: [5,5],
          tension: 0.3,
          fill: true
        },
        {
          label: 'Gastos',
          data: [],
          borderColor: '#DC2626',
          backgroundColor: 'rgba(220,38,38,0.2)',
          borderDash: [5,5],
          tension: 0.3,
          fill: true
        }
      ]
    })
    
    watchEffect(() => {
      const vals = Array.isArray(props.monthlyBalances) ? props.monthlyBalances : []
      chartData.labels = vals.map(m => labelFromMES(m?.MES))
      chartData.datasets[0].data = vals.map(m => m?.total_balance ?? 0)
      chartData.datasets[1].data = vals.map(m => m?.income ?? 0)
      chartData.datasets[2].data = vals.map(m => m?.expenses ?? 0)
    })
    
    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: ctx =>
              `${ctx.dataset.label}: ${ctx.raw?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${props.currency}`
          }
        }
      },
      interaction: { mode: 'index', intersect: false },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            // Por si Chart.js te pasa valores numéricos grandes
            callback: val => Number(val).toLocaleString()
          }
        }
      }
    }
    </script>
    
   <template>
  <div class="chart-card timeline-card">
    <h3 class="card-title">Evolución mensual</h3>

    <div v-if="props.loading">Cargando…</div>
    <div v-else-if="!props.monthlyBalances.length">Sin datos</div>

    <div class="chart-wrapper" v-else>
      <LineChart :chart-data="chartData" :chart-options="chartOptions" />
    </div>
  </div>
</template>
    

    <style scoped>
      .timeline-card {
          display: flex;
          flex-direction: column;
          height: 100%; /* ocupar todo el alto del padre */
          padding: 20px;

        }

        .chart-wrapper {
          flex: 1;      /* ocupa todo el espacio disponible dentro del card */
          width: 100%;
        }
       .card-title {
        margin-top: 0;
        margin-bottom: 8px;
        line-height: 1.2;
        }
       
        
        h3 {
          margin-bottom: 8px;
        }
        /* Título con margen contenido */
       .entity-root > h3 {
        margin: 0 0 8px;
        line-height: 1.2;
        }
</style>
        