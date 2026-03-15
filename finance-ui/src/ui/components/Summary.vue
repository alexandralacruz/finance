<template>
  <div class="summary-wrapper">
    <!-- Loading state elegante -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Cargando resumen financiero...</p>
    </div>

    <!-- No data state elegante -->
    <div v-else-if="!summary || Object.keys(summary).length === 0" class="empty-state">
      <div class="empty-icon">📊</div>
      <p class="empty-title">Sin datos</p>
      <p class="empty-subtitle">No hay información para este período</p>
    </div>

    <!-- Cards principales -->
    <div v-else class="summary-container">
      <div class="card balance">
        <div class="icon">💰</div>
        <div class="card-content">
          <h4>Saldo Total</h4>
          <p class="amount">{{ formatCurrency(summary.totalBalance) }}</p>
        </div>
      </div>

      <div class="card entities">
        <div class="icon">🏦</div>
        <div class="card-content">
          <h4>Entidades Activas</h4>
          <p class="amount">{{ summary.activeEntities || 0 }}</p>
        </div>
      </div>

      <div class="card income">
        <div class="icon">📈</div>
        <div class="card-content">
          <h4>Ingresos del año</h4>
          <p class="amount">{{ formatCurrency(summary.monthlyIncome) }}</p>
        </div>
      </div>

      <div class="card expense">
        <div class="icon">📉</div>
        <div class="card-content">
          <h4>Egresos del año</h4>
          <p class="amount">{{ formatCurrency(summary.monthlyExpenses) }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { defineProps, computed } from 'vue'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      totalBalance: 0,
      activeEntities: 0,
      monthlyIncome: 0,
      monthlyExpenses: 0
    })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const formatCurrency = (value) => {
  if (!value && value !== 0) return '$0'
  return new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(value)
}
</script>

<style scoped>
.summary-wrapper {
  padding: 32px 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  min-height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Contenedor principal */
.summary-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 32px;
  padding: 32px;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(255, 255, 255, 0.2);
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  width: 100%;
  max-width: 1400px;
}

/* Tarjetas individuales */
.card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 24px;
  padding: 28px 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent);
}

.card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.icon {
  font-size: 24px;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.1));
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  min-width: 0;
}

.card-content h4 {
  font-size: 10px;
  font-weight: 600;
  color: #64748b;
  margin: 0 0 12px 0;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.card-content .amount {
  font-size: 24px;
  font-weight: 800;
  margin: 0;
  line-height: 1;
  font-feature-settings: 'tnum' 1, 'lnum' 1;
}

/* Colores específicos por tarjeta */
.card.balance .amount   { color: #1e40af; }
.card.entities .amount  { 
  color: #475569; 
  font-size: 20px;
  font-variation-settings: 'wght' 900;
}
.card.income .amount    { color: #059669; }
.card.expense .amount   { color: #dc2626; }

/* Estados especiales */
.loading-state, .empty-state {
  text-align: center;
  padding: 48px 24px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 3px solid rgba(59, 130, 246, 0.2);
  border-top: 3px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-title {
  font-size: 20px;
  font-weight: 700;
  color: #64748b;
  margin: 0 0 8px 0;
}

.empty-subtitle {
  color: #94a3b8;
  margin: 0;
  font-size: 16px;
}

/* Responsive perfecto */
@media (max-width: 1200px) {
  .summary-container {
    grid-template-columns: repeat(2, 1fr);
    gap: 20px;
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .summary-wrapper {
    padding: 24px 16px;
  }
  
  .summary-container {
    grid-template-columns: 1fr;
    padding: 20px;
  }
  
  .card-content .amount {
    font-size: 32px;
  }
  
  .icon {
    font-size: 40px;
  }
}

@media (max-width: 480px) {
  .summary-container {
    padding: 16px;
    gap: 16px;
  }
  
  .card {
    padding: 20px 16px;
  }
}
</style>