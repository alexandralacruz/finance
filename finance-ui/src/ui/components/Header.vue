  <template>
    <header class="header">
      <div class="header-left">
        <span class="fx">
          💱 Tasa del día:
          <strong v-if="!loading">
            {{ rate.toLocaleString() }} COP/USD
          </strong>
          <span v-else>Cargando...</span>
        </span>

        <span class="separator">|</span>

        <span class="ccurrency">
          Moneda:
          <select
            :value="props.currency || 'USD'"
            @change="onCurrencyChange"
          >
            <option value="USD">USD</option>
            <option value="COP">COP</option>
          </select>
        </span>
      </div>

      <div class="header-center">
        📅 Fecha: <strong>{{ rateDate }}</strong>

        <div class="year-selector">
          Año:
          <select v-model="localYear">
            <option
              v-for="year in years"
              :key="year"
              :value="year"
            >
              {{ year }}
            </option>
          </select>
        </div>
      </div>

      <div class="header-right">
        <button class="update-btn" @click="$emit('refresh-rate')">
          🔄 Actualizar
        </button>
      </div>
    </header>
  </template>

  <script setup>
  import { ref, watch } from 'vue'

const props = defineProps({
  rate: Number,
  rateDate: String,
  loading: Boolean,
  years: Array,
  modelValue: Number,
  currency: String
})

const emit = defineEmits(['update:modelValue', 'update:currency', 'refresh-rate'])

const localYear = ref(props.modelValue)

watch(localYear, (val) => {
  emit('update:modelValue', val)
})

function onCurrencyChange(e) {
  emit('update:currency', e.target.value)
}
  </script>

  <style scoped>
    .header-center { 
      background: #e9ecef;
      padding: 10px;
      display: flex; /* Activa flexbox */ 
      justify-content: space-between;
      align-items: center; /* Centra verticalmente */ 
      font-size: 14px;
      gap: 1rem; /* Espacio entre fecha y selector */ 
    } 

  .year-selector { 
      display: flex; 
      align-items: center; /* Centra el texto "Año:" con el select */ 
      gap: 0.5rem; 
    }
  
  </style>
