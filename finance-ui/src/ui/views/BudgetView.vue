<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-1">Presupuesto Mensual</h1>
    <p class="text-sm text-gray-500 mb-6">
      Control de gastos e ingresos de la cuenta principal
      <span class="text-blue-600 font-medium">{{ primaryEntity }}</span>
    </p>

    <!-- Month / Year selector -->
    <div class="flex items-center gap-3 mb-6">
      <select v-model="month" class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white">
        <option v-for="m in 12" :key="m" :value="m">{{ monthNames[m - 1] }}</option>
      </select>
      <select v-model="budgetYear" class="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white">
        <option v-for="y in availableYears" :key="y" :value="y">{{ y }}</option>
      </select>
      <button @click="fetchBudget" :disabled="loading" class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors disabled:opacity-50">
        {{ loading ? 'Cargando...' : 'Ver presupuesto' }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-4 border-blue-200 border-t-blue-600"></div>
    </div>

    <!-- Error state -->
    <div v-else-if="errorMsg" class="bg-yellow-50 border border-yellow-200 rounded-xl p-6 text-center">
      <p class="text-yellow-700">{{ errorMsg }}</p>
    </div>

    <!-- Empty state -->
    <div v-else-if="!data" class="text-center text-gray-400 py-10">
      Selecciona un mes y haz clic en "Ver presupuesto"
    </div>

    <!-- Budget content -->
    <div v-else>
      <!-- Saldo inicial -->
      <div class="glass-card rounded-2xl p-6 mb-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <span class="text-sm font-semibold text-gray-500 uppercase tracking-wide">Saldo inicial</span>
            <span class="text-2xl font-bold text-blue-700">{{ fmt(data.saldo_inicial) }}</span>
            <span class="text-xs text-gray-400 bg-gray-100 rounded-full px-2 py-0.5" title="Balance de {{ primaryEntity }} al inicio del mes">auto</span>
          </div>
          <div class="text-xs text-gray-400">
            {{ primaryEntity }} · {{ monthNames[month - 1] }} {{ budgetYear }}
          </div>
        </div>
      </div>

      <!-- Notificación / Ahorro -->
      <div
        class="rounded-2xl p-5 mb-6 border-2 transition-all"
        :class="notificationClass"
      >
        <div class="flex items-center gap-4">
          <span class="text-3xl">{{ notificationIcon }}</span>
          <div class="flex-1">
            <p class="font-bold text-lg">{{ data.notificacion }}</p>
            <p class="text-sm opacity-80 mt-1">
              Ahorro este mes: <strong>{{ fmt(data.ahorro_mes) }}</strong>
              <span v-if="data.ahorro_variacion_pct !== null" class="ml-2">
                ·
                <span :class="data.ahorro_variacion_pct >= 0 ? 'text-green-600' : 'text-red-600'">
                  {{ data.ahorro_variacion_pct >= 0 ? '+' : '' }}{{ data.ahorro_variacion_pct }}%
                </span>
                vs mes anterior
              </span>
            </p>
          </div>
        </div>

        <!-- 80/20 bar -->
        <div class="mt-4 grid grid-cols-5 gap-1">
          <div class="col-span-4 bg-indigo-200 rounded-l-lg h-3 relative overflow-hidden">
            <div class="absolute inset-0 bg-indigo-400 rounded-l-lg" :style="{ width: '100%' }"></div>
          </div>
          <div class="col-span-1 bg-amber-200 rounded-r-lg h-3 relative overflow-hidden">
            <div class="absolute inset-0 bg-amber-400 rounded-r-lg" :style="{ width: '100%' }"></div>
          </div>
        </div>
        <div class="flex justify-between mt-1.5 text-xs text-gray-500">
          <span>80% bloqueado: <strong>{{ fmt(data.ahorro_acumulado_80) }}</strong></span>
          <span>20% disponible: <strong>{{ fmt(data.ahorro_acumulado_20) }}</strong></span>
        </div>
        <p class="text-xs text-gray-400 mt-1">Ahorro acumulado total: <strong>{{ fmt(data.ahorro_acumulado) }}</strong></p>
      </div>

      <!-- Saldo Inicial / Saldo Final cards -->
      <div class="grid grid-cols-2 gap-4 mb-6">
        <div class="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Saldo Inicial</p>
          <p class="text-xl font-bold text-gray-700">{{ fmt(data.saldo_inicial) }}</p>
        </div>
        <div class="bg-gray-50 rounded-xl p-4 text-center border border-gray-100">
          <p class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-1">Saldo Final</p>
          <p class="text-xl font-bold" :class="data.saldo_final >= data.saldo_inicial ? 'text-green-600' : 'text-red-600'">
            {{ fmt(data.saldo_final) }}
          </p>
        </div>
      </div>

      <!-- Two-column tables: Gastos | Ganancias -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- GASTOS -->
        <div class="glass-card rounded-2xl p-6">
          <h2 class="text-lg font-bold text-red-600 mb-4">Gastos</h2>

          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="bg-red-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-500">Previsto</p>
              <p class="text-lg font-bold text-gray-700">{{ fmt(data.gastos.previsto_total) }}</p>
            </div>
            <div class="bg-red-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-500">Real</p>
              <p class="text-lg font-bold text-gray-700">{{ fmt(data.gastos.real_total) }}</p>
            </div>
            <div class="rounded-lg p-3 text-center" :class="data.gastos.diferencia_total >= 0 ? 'bg-green-50' : 'bg-red-50'">
              <p class="text-xs text-gray-500">Difer.</p>
              <p class="text-lg font-bold" :class="data.gastos.diferencia_total >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ fmt(data.gastos.diferencia_total) }}
              </p>
            </div>
          </div>

          <!-- Expense table -->
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 text-gray-400 text-xs uppercase tracking-wider">
                  <th class="text-left py-2 font-semibold"></th>
                  <th class="text-right py-2 font-semibold">Previsto</th>
                  <th class="text-right py-2 font-semibold">Real</th>
                  <th class="text-right py-2 font-semibold">Difer.</th>
                  <th class="w-8"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="data.gastos.categorias.length" class="border-b border-gray-200 bg-gray-50 font-bold">
                  <td class="py-2 text-gray-700">Totales</td>
                  <td class="py-2 text-right text-gray-700">{{ fmt(data.gastos.previsto_total) }}</td>
                  <td class="py-2 text-right text-gray-700">{{ fmt(data.gastos.real_total) }}</td>
                  <td class="py-2 text-right" :class="data.gastos.diferencia_total >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ fmt(data.gastos.diferencia_total) }}
                  </td>
                  <td></td>
                </tr>
                <tr
                  v-for="cat in data.gastos.categorias"
                  :key="'exp-' + (cat.category_id || cat.nombre)"
                  class="border-b border-gray-100 hover:bg-gray-50/50 transition-colors"
                  :class="{ 'bg-red-50/30': cat.real > cat.previsto && cat.previsto > 0 }"
                >
                  <td class="py-2 text-gray-700">{{ cat.nombre }}</td>
                  <td class="py-2 text-right">
                    <span
                      v-if="cat.editable"
                      @click="startEditGasto(cat)"
                      class="cursor-pointer border-b border-dashed border-gray-300 hover:border-blue-400 px-1"
                      :title="'Click para editar límite de ' + cat.nombre"
                    >
                      <template v-if="editingGasto === cat.category_id">
                        <input
                          :ref="el => { if (el) el.focus() }"
                          v-model.number="editGastoValue"
                          type="number"
                          step="1"
                          class="w-24 text-right border border-blue-400 rounded px-1 py-0.5 text-sm"
                          @blur="saveGasto(cat)"
                          @keydown.enter="saveGasto(cat)"
                          @keydown.escape="cancelEditGasto"
                        />
                      </template>
                      <template v-else>{{ fmt(cat.previsto) }}</template>
                    </span>
                    <span v-else class="text-gray-400">{{ fmt(cat.previsto) }}</span>
                  </td>
                  <td class="py-2 text-right" :class="cat.real > 0 ? 'text-red-600' : 'text-gray-400'">
                    {{ fmt(cat.real) }}
                  </td>
                  <td class="py-2 text-right" :class="cat.diferencia >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ fmt(Math.abs(cat.diferencia)) }}
                  </td>
                  <td class="py-2 text-center">
                    <button
                      v-if="cat.category_id"
                      @click="deleteCategory(cat.category_id, 'expense')"
                      class="text-gray-300 hover:text-red-500 text-xs transition-colors"
                      title="Eliminar categoría"
                    >×</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Add expense category -->
          <div class="mt-3 flex gap-2">
            <input
              v-model="newExpenseCat"
              placeholder="Nueva categoría de gasto..."
              class="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
              @keydown.enter="addCategory('expense')"
            />
            <button @click="addCategory('expense')" class="bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg text-sm transition-colors">
              + Añadir
            </button>
          </div>
        </div>

        <!-- GANANCIAS -->
        <div class="glass-card rounded-2xl p-6">
          <h2 class="text-lg font-bold text-green-600 mb-4">Ganancias</h2>

          <div class="grid grid-cols-3 gap-3 mb-4">
            <div class="bg-green-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-500">Previsto</p>
              <p class="text-lg font-bold text-gray-700">
                {{ fmt(data.ganancias.previsto_total) }}
                <span v-if="data.ganancias.previsto_total === 0" class="text-xs text-gray-400 block" title="Sin datos de nómina reciente. Puedes editar manualmente.">sin nómina</span>
              </p>
            </div>
            <div class="bg-green-50 rounded-lg p-3 text-center">
              <p class="text-xs text-gray-500">Real</p>
              <p class="text-lg font-bold text-gray-700">{{ fmt(data.ganancias.real_total) }}</p>
            </div>
            <div class="rounded-lg p-3 text-center" :class="data.ganancias.diferencia_total >= 0 ? 'bg-green-50' : 'bg-red-50'">
              <p class="text-xs text-gray-500">Difer.</p>
              <p class="text-lg font-bold" :class="data.ganancias.diferencia_total >= 0 ? 'text-green-600' : 'text-red-600'">
                {{ fmt(data.ganancias.diferencia_total) }}
              </p>
            </div>
          </div>

          <!-- Income table -->
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-gray-200 text-gray-400 text-xs uppercase tracking-wider">
                  <th class="text-left py-2 font-semibold"></th>
                  <th class="text-right py-2 font-semibold">Previsto</th>
                  <th class="text-right py-2 font-semibold">Real</th>
                  <th class="text-right py-2 font-semibold">Difer.</th>
                  <th class="w-8"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="data.ganancias.categorias.length" class="border-b border-gray-200 bg-gray-50 font-bold">
                  <td class="py-2 text-gray-700">Totales</td>
                  <td class="py-2 text-right text-gray-700">{{ fmt(data.ganancias.previsto_total) }}</td>
                  <td class="py-2 text-right text-gray-700">{{ fmt(data.ganancias.real_total) }}</td>
                  <td class="py-2 text-right" :class="data.ganancias.diferencia_total >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ fmt(data.ganancias.diferencia_total) }}
                  </td>
                  <td></td>
                </tr>
                <tr
                  v-for="cat in data.ganancias.categorias"
                  :key="'inc-' + (cat.category_id || cat.nombre)"
                  class="border-b border-gray-100 hover:bg-gray-50/50 transition-colors"
                >
                  <td class="py-2 text-gray-700">{{ cat.nombre }}</td>
                  <td class="py-2 text-right">
                    <span v-if="data.ganancias.previsto_total === 0 && cat.nombre === 'Sueldo'" class="relative group">
                      <span
                        @click="startEditIngreso(cat)"
                        class="cursor-pointer border-b border-dashed border-gray-300 hover:border-blue-400 px-1"
                        title="Sin nómina automática. Click para establecer manualmente."
                      >
                        <template v-if="editingIngreso === cat.category_id">
                          <input
                            :ref="el => { if (el) el.focus() }"
                            v-model.number="editIngresoValue"
                            type="number"
                            step="1"
                            class="w-24 text-right border border-blue-400 rounded px-1 py-0.5 text-sm"
                            @blur="saveIngreso(cat)"
                            @keydown.enter="saveIngreso(cat)"
                            @keydown.escape="cancelEditIngreso"
                          />
                        </template>
                        <template v-else>{{ fmt(cat.previsto) }}</template>
                      </span>
                    </span>
                    <span v-else class="text-gray-400">{{ fmt(cat.previsto) }}</span>
                  </td>
                  <td class="py-2 text-right" :class="cat.real > 0 ? 'text-green-600' : 'text-gray-400'">
                    {{ fmt(cat.real) }}
                  </td>
                  <td class="py-2 text-right" :class="cat.diferencia >= 0 ? 'text-green-600' : 'text-red-600'">
                    {{ fmt(cat.diferencia) }}
                  </td>
                  <td class="py-2 text-center">
                    <button
                      v-if="cat.category_id"
                      @click="deleteCategory(cat.category_id, 'income')"
                      class="text-gray-300 hover:text-red-500 text-xs transition-colors"
                      title="Eliminar categoría"
                    >×</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Add income category -->
          <div class="mt-3 flex gap-2">
            <input
              v-model="newIncomeCat"
              placeholder="Nueva categoría de ingreso..."
              class="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
              @keydown.enter="addCategory('income')"
            />
            <button @click="addCategory('income')" class="bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg text-sm transition-colors">
              + Añadir
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const API_URL = import.meta.env.VITE_API_URL

const now = new Date()
const budgetYear = ref(now.getFullYear())
const month = ref(now.getMonth() + 1)
const availableYears = [now.getFullYear(), now.getFullYear() - 1]

const loading = ref(false)
const data = ref(null)
const errorMsg = ref(null)
const primaryEntity = ref('BC')

// Inline editing state
const editingGasto = ref(null)
const editGastoValue = ref(0)
const editingIngreso = ref(null)
const editIngresoValue = ref(0)

// New category inputs
const newExpenseCat = ref('')
const newIncomeCat = ref('')

const monthNames = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
]

const fmt = (v) => {
  if (v == null || isNaN(v)) return '0'
  return new Intl.NumberFormat('es-CO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(v)
}

// Notifications
const notificationClass = computed(() => {
  if (!data.value) return ''
  const t = data.value.notificacion_tipo
  if (t === 'felicitacion') return 'bg-green-50 border-green-300'
  if (t === 'bien') return 'bg-blue-50 border-blue-200'
  if (t === 'alarma') return 'bg-red-50 border-red-400 animate-pulse'
  if (t === 'advertencia') return 'bg-yellow-50 border-yellow-300'
  return 'bg-gray-50 border-gray-200'
})

const notificationIcon = computed(() => {
  if (!data.value) return ''
  const t = data.value.notificacion_tipo
  if (t === 'felicitacion') return '🎉'
  if (t === 'bien') return '✅'
  if (t === 'alarma') return '🔴'
  if (t === 'advertencia') return '⚠️'
  return 'ℹ️'
})

// ── API calls ──────────────────────────────────────────────────────

async function fetchBudget() {
  loading.value = true
  errorMsg.value = null
  data.value = null
  try {
    const res = await fetch(`${API_URL}/budgets/${budgetYear.value}/${month.value}/full`)
    if (!res.ok) throw new Error('Error al cargar presupuesto')
    const json = await res.json()
    if (json.error) {
      errorMsg.value = json.error + (json.hint ? ' ' + json.hint : '')
      data.value = null
    } else {
      data.value = json
      primaryEntity.value = json.primary_entity || 'BC'
    }
  } catch (e) {
    console.error(e)
    errorMsg.value = 'Error de conexión al cargar el presupuesto.'
  } finally {
    loading.value = false
  }
}

// ── Gasto inline editing ───────────────────────────────────────────

function startEditGasto(cat) {
  editingGasto.value = cat.category_id
  editGastoValue.value = cat.previsto
}

async function saveGasto(cat) {
  const val = Math.max(0, editGastoValue.value || 0)
  try {
    await fetch(`${API_URL}/budgets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        year: budgetYear.value,
        month: month.value,
        category_id: cat.category_id,
        limit_amount: val,
        currency: 'COP',
      }),
    })
    cat.previsto = val
    // Update total
    const total = data.value.gastos.categorias.reduce((s, c) => s + c.previsto, 0)
    data.value.gastos.previsto_total = Math.round(total * 100) / 100
    data.value.gastos.diferencia_total = Math.round((total - data.value.gastos.real_total) * 100) / 100
  } catch (e) {
    console.error(e)
  }
  editingGasto.value = null
}

function cancelEditGasto() {
  editingGasto.value = null
}

// ── Ingreso manual edit (when no nomina) ──────────────────────────

function startEditIngreso(cat) {
  editingIngreso.value = cat.category_id
  editIngresoValue.value = cat.previsto
}

function saveIngreso(cat) {
  const val = Math.max(0, editIngresoValue.value || 0)
  cat.previsto = val
  const total = data.value.ganancias.categorias.reduce((s, c) => s + c.previsto, 0)
  data.value.ganancias.previsto_total = Math.round(total * 100) / 100
  data.value.ganancias.diferencia_total = Math.round((data.value.ganancias.real_total - total) * 100) / 100
  editingIngreso.value = null
}

function cancelEditIngreso() {
  editingIngreso.value = null
}

// ── Categories CRUD ────────────────────────────────────────────────

async function addCategory(type) {
  const name = type === 'expense' ? newExpenseCat.value.trim() : newIncomeCat.value.trim()
  if (!name) return

  try {
    const res = await fetch(`${API_URL}/categories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, type }),
    })
    const json = await res.json()
    if (json.ok) {
      const target = type === 'expense' ? data.value.gastos.categorias : data.value.ganancias.categorias
      target.push({
        category_id: json.id,
        nombre: json.name,
        previsto: 0,
        real: 0,
        diferencia: 0,
        editable: type === 'expense',
      })
      if (type === 'expense') newExpenseCat.value = ''
      else newIncomeCat.value = ''
    }
  } catch (e) {
    console.error(e)
  }
}

async function deleteCategory(categoryId, type) {
  if (!confirm('¿Eliminar esta categoría? Las transacciones existentes la conservarán pero no aparecerá en el presupuesto.')) return

  try {
    await fetch(`${API_URL}/categories/${categoryId}`, { method: 'DELETE' })
    const target = type === 'expense' ? data.value.gastos.categorias : data.value.ganancias.categorias
    const idx = target.findIndex(c => c.category_id === categoryId)
    if (idx >= 0) target.splice(idx, 1)
  } catch (e) {
    console.error(e)
  }
}
</script>
