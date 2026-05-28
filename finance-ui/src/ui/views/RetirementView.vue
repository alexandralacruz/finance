<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Plan de retiro</h1>
    <p class="text-sm text-gray-500 mb-6">Proyección de ahorro para el retiro</p>

    <!-- Plan config -->
    <div class="glass-card rounded-2xl p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Configuración del Plan</h2>
      <form @submit.prevent="savePlan" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Nombre del plan</label>
          <input v-model="form.name" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Meta en COP</label>
          <input v-model.number="form.target_amount_cop" type="number" step="1" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Ej: 500000000" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Meta en USD</label>
          <input v-model.number="form.target_amount_usd" type="number" step="1" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" placeholder="Ej: 120000" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Años para el retiro</label>
          <input v-model.number="form.target_years" type="number" min="1" max="60" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Rendimiento anual estimado (%)</label>
          <input v-model.number="form.annual_return_pct" type="number" step="0.1" min="0" max="50" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div>
          <label class="block text-xs font-semibold text-gray-500 mb-1">Ahorro actual en COP</label>
          <input v-model.number="form.current_savings_cop" type="number" step="1" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
        <div class="md:col-span-2 lg:col-span-3">
          <button type="submit" class="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
            💾 Guardar Plan
          </button>
        </div>
      </form>
    </div>

    <!-- Entity savings selection -->
    <div v-if="entitySavings.length" class="glass-card rounded-2xl p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-2">Ahorro mensual por entidad</h2>
      <p class="text-xs text-gray-400 mb-4">Selecciona las entidades a incluir en el cálculo (últimos 12 meses)</p>

      <div class="space-y-2 mb-4">
        <div
          v-for="es in entitySavings"
          :key="es.entity_name"
          class="flex items-center justify-between p-3 rounded-lg border border-gray-100 hover:bg-gray-50 transition-colors"
        >
          <label class="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              :checked="selectedEntities[es.entity_name]"
              @change="toggleEntity(es.entity_name)"
              class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span class="text-sm font-medium text-gray-700">{{ es.entity_name }}</span>
            <span class="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ es.currency }}</span>
          </label>
          <div class="flex items-center gap-4 text-sm">
            <span class="text-green-600">+{{ fmt(es.monthly_income) }}</span>
            <span class="text-red-500">-{{ fmt(es.monthly_expenses) }}</span>
            <span class="font-bold" :class="es.monthly_savings >= 0 ? 'text-blue-700' : 'text-red-600'">
              {{ es.monthly_savings >= 0 ? '+' : '' }}{{ fmt(es.monthly_savings) }}
            </span>
          </div>
        </div>
      </div>

      <!-- Totals -->
      <div class="flex justify-end items-center gap-3 pt-3 border-t border-gray-200">
        <span class="text-sm text-gray-600">Ahorro mensual seleccionado:</span>
        <span class="text-lg font-bold" :class="selectedMonthlySavings >= 0 ? 'text-green-700' : 'text-red-600'">
          {{ fmt(selectedMonthlySavings) }}
        </span>
      </div>
    </div>

    <!-- Projection -->
    <div v-if="plan" class="glass-card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Proyección</h2>

      <!-- Key metrics -->
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div class="bg-gray-50 rounded-xl p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">Ahorro mensual seleccionado</p>
          <p class="text-xl font-bold text-blue-700">{{ fmt(selectedMonthlySavings) }}</p>
          <p class="text-xs text-gray-400 mt-1">{{ selectedCount }} de {{ entitySavings.length }} entidades</p>
        </div>
        <div class="bg-gray-50 rounded-xl p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">Proyección final</p>
          <p class="text-xl font-bold text-green-700">{{ fmt(customProjection?.final_projection) }}</p>
        </div>
        <div class="bg-gray-50 rounded-xl p-4 text-center">
          <p class="text-xs text-gray-500 mb-1">Meta</p>
          <p class="text-xl font-bold text-gray-700">{{ fmt(plan.target_amount_cop) }}</p>
        </div>
        <div class="rounded-xl p-4 text-center" :class="customProjection?.on_track ? 'bg-green-100' : 'bg-red-100'">
          <p class="text-xs font-semibold mb-1" :class="customProjection?.on_track ? 'text-green-700' : 'text-red-700'">
            {{ customProjection?.on_track ? '✅ En camino' : '⚠️ Necesita ajuste' }}
          </p>
          <p class="text-sm font-bold" :class="customProjection?.on_track ? 'text-green-700' : 'text-red-700'">
            {{ customProjection?.on_track ? 'Vas bien' : `Faltan ${fmt(customProjection?.monthly_gap)}/mes` }}
          </p>
        </div>
      </div>

      <!-- Yearly table -->
      <h3 class="text-md font-semibold text-gray-600 mb-3">Proyección Anual</h3>
      <div v-if="customProjection?.yearly?.length" class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-gray-500">
              <th class="text-left py-2 px-3">Año</th>
              <th class="text-right py-2 px-3">Ahorro Proyectado (COP)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="y in customProjection.yearly" :key="y.year" class="border-b border-gray-100 hover:bg-gray-50">
              <td class="py-2 px-3 font-medium text-gray-700">{{ y.year }}</td>
              <td class="py-2 px-3 text-right font-bold text-gray-800">{{ fmt(y.projected_savings) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-else class="text-center text-gray-400 py-10">
      Cargando plan...
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted } from 'vue'

const API_URL = import.meta.env.VITE_API_URL
const plan = ref(null)
const projection = ref(null)
const entitySavings = ref([])
const selectedEntities = reactive({})

const form = ref({
  name: 'Plan de retiro',
  target_amount_cop: 500000000,
  target_amount_usd: null,
  target_years: 20,
  annual_return_pct: 5,
  current_savings_cop: 0,
  current_savings_usd: 0,
})

const fmt = (v) => {
  if (v == null || v === 0) return '$0'
  return '$' + new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v)
}

const selectedMonthlySavings = computed(() => {
  return entitySavings.value
    .filter(es => selectedEntities[es.entity_name])
    .reduce((sum, es) => sum + es.monthly_savings, 0)
})

const selectedCount = computed(() => {
  return entitySavings.value.filter(es => selectedEntities[es.entity_name]).length
})

function toggleEntity(name) {
  selectedEntities[name] = !selectedEntities[name]
}

// Client-side projection calculation (mirrors backend logic)
function calcProjection(monthlySavings) {
  const p = plan.value
  if (!p) return null
  const monthlyRate = (1 + (p.annual_return_pct || 5) / 100) ** (1 / 12) - 1
  const months = (p.target_years || 20) * 12
  const contribution = monthlySavings || 0
  const initial = p.current_savings_cop || 0

  let fv = initial
  const yearly = []

  for (let m = 1; m <= months; m++) {
    fv = fv * (1 + monthlyRate) + contribution
    if (m % 12 === 0) {
      yearly.push({ year: m / 12, projected_savings: Math.round(fv * 100) / 100 })
    }
  }

  const target = p.target_amount_cop || 0
  const onTrack = target > 0 ? fv >= target : null
  let monthlyNeeded = 0
  if (target > 0 && monthlyRate > 0) {
    monthlyNeeded = (target - initial * (1 + monthlyRate) ** months) * monthlyRate / ((1 + monthlyRate) ** months - 1)
  }

  return {
    final_projection: Math.round(fv * 100) / 100,
    target,
    on_track: onTrack,
    monthly_needed_to_reach_target: Math.round(Math.max(0, monthlyNeeded) * 100) / 100,
    monthly_gap: Math.round(Math.max(0, monthlyNeeded - contribution) * 100) / 100,
    yearly,
  }
}

const customProjection = computed(() => calcProjection(selectedMonthlySavings.value))

async function fetchPlan() {
  try {
    const res = await fetch(`${API_URL}/retirement/plan`)
    if (res.ok) {
      const data = await res.json()
      plan.value = data
      projection.value = data.projection
      entitySavings.value = data.entity_savings || []

      // Auto-select entities that have positive savings
      for (const es of entitySavings.value) {
        if (!(es.entity_name in selectedEntities)) {
          selectedEntities[es.entity_name] = es.monthly_savings > 0
        }
      }

      // Sync form
      form.value = {
        name: data.name || '',
        target_amount_cop: data.target_amount_cop,
        target_amount_usd: data.target_amount_usd,
        target_years: data.target_years,
        annual_return_pct: data.annual_return_pct,
        current_savings_cop: data.current_savings_cop,
        current_savings_usd: data.current_savings_usd,
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function savePlan() {
  try {
    await fetch(`${API_URL}/retirement/plan`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value),
    })
    await fetchPlan()
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchPlan)
</script>
