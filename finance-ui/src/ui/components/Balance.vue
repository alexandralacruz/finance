<template>
    <div class="charts-row">
      <BalanceByEntity
        :entities="entities"
        :currency="currency"
        :loading="loadingEntities"
      />
  
      <BalanceTimeLine
        :monthly-balances="monthlyBalances"
        :currency="currency"
        :loading="loadingMonthly"
      />
    </div>
  </template>
  
  <script setup>
  import { ref, watch } from 'vue'
  import BalanceByEntity from '../components/BalanceByEntity.vue'
  import BalanceTimeLine from '../components/BalanceTimeLine.vue'
  
  const props = defineProps({
    year: {
      type: Number,
      required: true
    },
    currency: {
      type: String,
      default: 'USD'
    },
    rate: {
      type: Number,
      required: true
    }
  })
  
  const API_URL = import.meta.env.VITE_API_URL
  
  /* ===== STATE ===== */
  const entities = ref([])
  const monthlyBalances = ref([])
  
  const loadingEntities = ref(false)
  const loadingMonthly = ref(false)
  
  /* ===== FETCH: barras ===== */
  async function fetchBalanceByEntity() {
    loadingEntities.value = true
  
    try {
        const url = `${API_URL}/byEntity/${props.year}?currency=${props.currency}&usd_to_cop=${props.rate}`
        console.log('Fetching URL:', url)
        
        const res = await fetch(url)
        console.log('fetch result:', res)
      
        if (!res.ok) throw new Error('Error fetching balance by entity')
  
        const data = await res.json()
        // console.log('------------------------------Balance by Entiry data:', data.entities)
        entities.value = data.entities.map(e => ({
            name: e.ENTIDAD,
            balance: e.BALANCE_FINAL
        }))
    } catch (err) {
      console.error(err)
      entities.value = []
    } finally {
      loadingEntities.value = false
    }
  }
  
  /* ===== FETCH: línea ===== */
  async function fetchMonthly() {
  loadingMonthly.value = true

  try {
    const res = await fetch(
      `${API_URL}/byMonth/${props.year}?currency=${props.currency}&usd_to_cop=${props.rate}`
    )
    const data = await res.json()
    //console.log('------------------------------Balance by Month data:', data) 

    // Asegúrate de usar la propiedad correcta que devuelve tu API
    //monthlyBalances.value = Array.isArray(data.monthlyBalances) ? data.monthlyBalances : []
    monthlyBalances.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error(err)
    monthlyBalances.value = []
  } finally {
    loadingMonthly.value = false
  }
}
  
  /* ===== REACTIVITY ===== */
  watch(
    () => [props.year, props.currency, props.rate],
    () => {
      fetchBalanceByEntity()
      fetchMonthly()
    },
    { immediate: true }
  )
  </script>
  
  
<style scoped>
/* El contenedor principal ocupa todo el ancho y usa grid */
/*
.charts-row {
  display: flex;
  grid-template-columns: 1fr 1.5fr; 
  gap: 16px;
  width: 100%;
  align-items: stretch;
  min-height: 360px;    
  
}*/

.charts-row {
  display: flex;
  gap: 16px;
  width: 100%;
  /* altura mínima para que los charts sean visibles */
  min-height: 420px; 
  align-items: stretch; /* 🔑 fuerza a que los hijos ocupen toda la altura */
}

/* Si tus componentes hijos renderizan una "card", te conviene asegurarte que crezcan */
/* Para dar más ancho a la línea, por ejemplo 1:1.5 */
.charts-row > *:first-child {
  flex: 0.5; /* BalanceByEntity */
}
.charts-row > *:nth-child(2) {
  flex: 3; /* BalanceTimeLine */
}/*
.charts-row > * {
  flex: 1;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  // sombra opcional para look consistente 
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  min-height: 360px; // altura mínima para que el canvas se note 
}
  */

/* Responsivo: en móvil, una sola columna */
@media (max-width: 920px) {
  .charts-row {
    grid-template-columns: 1fr; /* stack */
  }
  .charts-row > * {
    min-height: 300px;
  }
}
</style>
