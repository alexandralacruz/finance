<template>
  <header class="header">
    
    <!-- LEFT -->
    <div class="header-left">
      <span class="fx">
        💱 Tasa del día:
        <strong v-if="!loading">
          {{ rate?.toLocaleString() }} COP/USD
        </strong>
        <span v-else>Cargando...</span>
      </span>

      <span class="separator">|</span>

      <span class="ccurrency">
        Moneda:
        <select
          :value="currency || 'USD'"
          @change="onCurrencyChange"
        >
          <option value="USD">USD</option>
          <option value="COP">COP</option>
        </select>
      </span>
    </div>

    <!-- CENTER -->
    <div class="header-center">
      📅 Fecha: <strong>{{ rateDate || '--' }}</strong>

      <div class="year-selector">
        Año:

        <!-- Si hay años -->
        <select v-if="years && years.length" v-model="localYear">
          <option
            v-for="year in years"
            :key="year"
            :value="year"
          >
            {{ year }}
          </option>
        </select>

        <!-- Si no hay años -->
        <span v-else>Cargando años...</span>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="header-right">
      <button class="update-btn" @click="$emit('refresh-rate')">
        🔄 Actualizar
      </button>
    </div>

  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rate: Number,
  rateDate: String,
  loading: Boolean,
  years: {
    type: Array,
    default: () => []
  },
  modelValue: Number,
  currency: String
})

const emit = defineEmits([
  'update:modelValue',
  'update:currency',
  'refresh-rate'
])

// 🔥 v-model limpio y reactivo
const localYear = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// Cambio de moneda
function onCurrencyChange(e) {
  emit('update:currency', e.target.value)
}
</script>

<style scoped>
.header {
  background: #e9ecef;
  padding: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

/* LEFT */
.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.separator {
  color: #999;
}

/* CENTER */
.header-center {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.year-selector {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* RIGHT */
.header-right {
  display: flex;
  align-items: center;
}

.update-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
}

.update-btn:hover {
  background: #2563eb;
}
</style>