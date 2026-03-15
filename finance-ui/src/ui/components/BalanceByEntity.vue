<script setup>
    import { computed } from 'vue'
    import BarChart from '../components/charts/BarChart.vue'
    
    const props = defineProps({
      entities: Array,
      currency: String
    })
    
    const chartData = computed(() => ({
      labels: props.entities.map(e => e.name),
      datasets: [
        {
          data: props.entities.map(e => e.balance),
          borderRadius: 6,

          backgroundColor: props.entities.map(e =>
                e.balance >= 0 ? '#22C55E' : '#EF4444'
            )
        }
      ]
    }))
    
    const chartOptions = {
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx =>
              `${ctx.raw.toLocaleString()} ${props.currency}`
          }
        }
      }
    }
</script>
    
<template>
        <div class="chart-card">
          <h3>Saldo por Entidad</h3>
      
          <div class="chart-wrapper">
            <BarChart
                :chart-data="chartData"
                :chart-options="chartOptions"
            />
          </div>
          
        </div>
</template>
      


<style scoped>
    /* Contenedor raíz del componente */

    .chart-card {
      display: flex;
      flex-direction: column;
      height: 100%; /* ocupar todo el alto del padre */
    }

    .chart-wrapper {
      flex: 1;      /* ocupa todo el espacio disponible dentro del card */
      width: 100%;
    }
    .entity-root {
      display: flex;
      flex-direction: column;
      /*width: 100%;*/
      height: 100%;             /* 👈 clave para igual altura */
      transform: none;
    }
    
    /* Título con margen contenido */
    .entity-root > h3 {
      margin: 0 0 8px;
      line-height: 1.2;
    }
    
    /* Wrapper del gráfico: llena el espacio disponible */
    /*
    .chart-wrapper {
      flex: 1;
  
      height: 100%;
      box-sizing: border-box;
      display: grid;            
      place-items: center;     

    }*/
    
    /* Si tu componente de gráfico monta un contenedor intermedio */
    /*.chart-wrapper .chart-container {
      height: 100%;
      box-sizing: border-box;
    }
    */
    /* Canvas al 100% — sin transform/zoom para mantener tipografía nítida */
    /*.chart-wrapper canvas {
      height: 100%;
      display: block;
    }
    */
    /* Opcional: tarjeta visual */
    .entity-card {
      background: #fff;
      border-radius: 12px;
      padding: 12px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.06);
      display: flex;
      flex-direction: column;
      height: 100%;             /* 👈 si usas esta clase como wrapper adicional */
    }
    
    /* Responsivo: altura mínima en móvil */
    @media (max-width: 920px) {
      .entity-root,
      .entity-card {
        min-height: 300px;
      }
    }
</style>
    