<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Entidades Financieras</h1>

    <!-- Add entity form -->
    <div class="glass-card rounded-2xl p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Agregar Nueva Entidad</h2>
      <form @submit.prevent="addEntity" class="flex flex-wrap gap-3 items-end">
        <div class="flex-1 min-w-[200px]">
          <label class="block text-xs font-semibold text-gray-500 mb-1">Nombre</label>
          <input v-model="form.name" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500" placeholder="Ej: Binance, Porvenir..." />
        </div>
        <div class="w-44">
          <label class="block text-xs font-semibold text-gray-500 mb-1">Tipo</label>
          <select v-model="form.type" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
            <option value="bank">Banco</option>
            <option value="investment">Inversión</option>
            <option value="crypto">Crypto</option>
            <option value="payment_processor">Procesador de Pago</option>
            <option value="pension_fund">Fondo de Pensión</option>
            <option value="other">Otro</option>
          </select>
        </div>
        <button type="submit" class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
          + Agregar
        </button>
      </form>
    </div>

    <!-- Entity accordion list -->
    <div class="glass-card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Entidades Registradas</h2>
      <div v-if="entities.length" class="space-y-3">
        <div
          v-for="e in entities"
          :key="e.id"
          class="rounded-xl border border-gray-100 overflow-hidden"
        >
          <!-- Entity header (clickable to expand) -->
          <div
            class="flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 cursor-pointer transition-colors"
            @click="toggleExpand(e.id)"
          >
            <div class="flex items-center gap-3">
              <span class="text-sm transition-transform" :class="expanded[e.id] ? 'rotate-90' : ''">▶</span>
              <div>
                <span class="font-medium text-gray-800">{{ e.name }}</span>
                <p class="text-xs text-gray-400 mt-0.5">{{ typeLabel(e.type) }}</p>
              </div>
            </div>
            <span
              class="px-2 py-0.5 rounded-full text-xs font-medium"
              :class="e.active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >{{ e.active ? 'Activo' : 'Inactivo' }}</span>
          </div>

          <!-- Expanded accounts list -->
          <div v-if="expanded[e.id]" class="border-t border-gray-100">
            <div v-if="e.accounts && e.accounts.length" class="divide-y divide-gray-50">
              <div
                v-for="acct in e.accounts"
                :key="acct.id"
                class="flex items-center justify-between px-6 py-3 hover:bg-blue-50 transition-colors"
              >
                <div class="flex items-center gap-3">
                  <span class="text-lg">{{ accountIcon(acct.account_type) }}</span>
                  <div class="flex items-center gap-2">
                    <!-- Inline editable account type -->
                    <select
                      :value="acct.account_type"
                      @change="updateAccountType(acct.id, ($event.target).value)"
                      class="text-sm font-medium text-gray-700 border border-gray-200 rounded px-1.5 py-0.5 bg-white hover:border-blue-300 focus:ring-2 focus:ring-blue-400 focus:border-blue-400"
                    >
                      <option value="checking">Corriente</option>
                      <option value="savings">Ahorro</option>
                      <option value="cdt">CDT</option>
                      <option value="pension">Pensión</option>
                      <option value="cesantias">Cesantías</option>
                      <option value="spot">Spot</option>
                      <option value="earn">Earn</option>
                      <option value="futures">Futures</option>
                      <option value="investment_fund">Fondo inv.</option>
                      <option value="other">Otro</option>
                    </select>
                    <span class="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">{{ acct.currency }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <router-link
                    :to="`/transactions?account=${acct.id}`"
                    class="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >+ Transacción</router-link>
                  <button
                    @click="deleteAccount(acct.id, e.id)"
                    class="text-xs text-red-400 hover:text-red-600 ml-1"
                    title="Eliminar cuenta"
                  >🗑️</button>
                </div>
              </div>
            </div>
            <div v-else class="px-6 py-4 text-sm text-gray-400 text-center">
              Sin cuentas. Añade una cuenta para esta entidad.
            </div>

            <!-- Add account form -->
            <div class="px-6 py-3 bg-gray-50 border-t border-gray-100">
              <form @submit.prevent="addAccount(e.id)" class="flex flex-wrap gap-2 items-end">
                <div class="w-40">
                  <label class="block text-xs font-semibold text-gray-500 mb-1">Tipo de cuenta</label>
                  <select v-model="accountForms[e.id].account_type" class="w-full border border-gray-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-blue-500">
                    <option value="checking">Corriente</option>
                    <option value="savings">Ahorro</option>
                    <option value="cdt">CDT</option>
                    <option value="pension">Pensión</option>
                    <option value="cesantias">Cesantías</option>
                    <option value="spot">Spot</option>
                    <option value="earn">Earn</option>
                    <option value="futures">Futures</option>
                    <option value="investment_fund">Fondo de inversión</option>
                    <option value="other">Otro</option>
                  </select>
                </div>
                <div class="w-24">
                  <label class="block text-xs font-semibold text-gray-500 mb-1">Moneda</label>
                  <select v-model="accountForms[e.id].currency" class="w-full border border-gray-300 rounded px-2 py-1.5 text-xs focus:ring-2 focus:ring-blue-500">
                    <option value="COP">COP</option>
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="USDT">USDT</option>
                    <option value="USDC">USDC</option>
                  </select>
                </div>
                <button type="submit" class="bg-green-600 text-white px-3 py-1.5 rounded text-xs font-medium hover:bg-green-700 transition-colors">
                  + Añadir cuenta
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
      <p v-else class="text-sm text-gray-400 py-8 text-center">No hay entidades registradas</p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const API_URL = import.meta.env.VITE_API_URL
const entities = ref([])
const expanded = reactive({})
const form = ref({ name: '', type: 'bank' })
const accountForms = reactive({})

const typeLabels = {
  bank: 'Banco',
  investment: 'Inversión',
  crypto: 'Crypto',
  payment_processor: 'Procesador de pago',
  pension_fund: 'Fondo de pensión',
  trading: 'Trading',
  other: 'Otro',
}

const accountTypeLabels = {
  checking: 'Cuenta Corriente',
  savings: 'Cuenta de Ahorro',
  cdt: 'CDT',
  pension: 'Pensión',
  cesantias: 'Cesantías',
  spot: 'Spot',
  earn: 'Earn',
  futures: 'Futures',
  investment_fund: 'Fondo de inversión',
  other: 'Otro',
}

const accountIcons = {
  checking: '🏦', savings: '💰', cdt: '📈', pension: '👴',
  cesantias: '🏖️', spot: '📊', earn: '💎', futures: '⚡',
  investment_fund: '📉', other: '📋',
}

const typeLabel = (t) => typeLabels[t] || t
const accountTypeLabel = (t) => accountTypeLabels[t] || t
const accountIcon = (t) => accountIcons[t] || '📋'

function toggleExpand(id) {
  expanded[id] = !expanded[id]
}

async function fetchEntities() {
  try {
    const res = await fetch(`${API_URL}/entities`)
    const data = await res.json()
    entities.value = data
    // Initialize account forms
    for (const e of data) {
      if (!accountForms[e.id]) {
        accountForms[e.id] = { account_type: 'checking', currency: 'COP' }
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function addEntity() {
  try {
    await fetch(`${API_URL}/entities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: form.value.name, type: form.value.type }),
    })
    form.value = { name: '', type: 'bank' }
    await fetchEntities()
  } catch (e) {
    console.error(e)
  }
}

async function addAccount(entityId) {
  const f = accountForms[entityId]
  if (!f) return
  try {
    await fetch(`${API_URL}/accounts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        entity_id: entityId,
        account_type: f.account_type,
        currency: f.currency,
      }),
    })
    f.account_type = 'checking'
    f.currency = 'COP'
    await fetchEntities()
  } catch (e) {
    console.error(e)
  }
}

async function updateAccountType(accountId, newType) {
  try {
    await fetch(`${API_URL}/accounts/${accountId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ account_type: newType }),
    })
    // Update locally without refetching
    for (const e of entities.value) {
      const acct = e.accounts?.find(a => a.id === accountId)
      if (acct) {
        acct.account_type = newType
        break
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function deleteAccount(accountId, entityId) {
  if (!confirm('¿Eliminar esta cuenta? Se marcará como inactiva.')) return
  try {
    await fetch(`${API_URL}/accounts/${accountId}`, { method: 'DELETE' })
    // Remove locally
    for (const e of entities.value) {
      if (e.id === entityId && e.accounts) {
        e.accounts = e.accounts.filter(a => a.id !== accountId)
        break
      }
    }
  } catch (e) {
    console.error(e)
  }
}

onMounted(fetchEntities)
</script>
