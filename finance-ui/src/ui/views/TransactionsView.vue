<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Transacciones Manuales</h1>
    <p class="text-sm text-gray-500 mb-6">Registra ingresos, gastos o saldos de tus cuentas</p>

    <!-- Add transaction form -->
    <div class="glass-card rounded-2xl p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Nueva Transacción</h2>
      <form @submit.prevent="addTransaction" class="space-y-4">
        <!-- Row 1: Entity → Account -->
        <div class="flex flex-wrap gap-3 items-end">
          <div class="w-44">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Entidad</label>
            <select v-model="form.entity_id" @change="onEntityChange" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
              <option value="">Seleccionar...</option>
              <option v-for="e in entities" :key="e.id" :value="e.id">{{ e.name }}</option>
            </select>
          </div>
          <div class="w-48">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Cuenta</label>
            <select v-model="form.account_id" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" :disabled="!form.entity_id">
              <option value="">Seleccionar...</option>
              <option v-for="acct in filteredAccounts" :key="acct.id" :value="acct.id">
                {{ accountTypeLabel(acct.account_type) }} · {{ acct.currency }}
              </option>
            </select>
          </div>
          <div class="w-36">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Fecha</label>
            <input v-model="form.date" type="date" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="w-36">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Tipo</label>
            <select v-model="form.type" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
              <option value="freelance">Freelance</option>
              <option value="income">Ingreso</option>
              <option value="expense">Gasto</option>
              <option value="investment">Inversión</option>
              <option value="deposit">Depósito</option>
              <option value="withdrawal">Retiro</option>
              <option value="balance">💡 Balance (saldo)</option>
            </select>
          </div>
        </div>

        <!-- Row 2: Conditional fields -->
        <div class="flex flex-wrap gap-3 items-end">
          <div class="flex-1 min-w-[200px]">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Descripción</label>
            <input v-model="form.description" :required="form.type !== 'balance'" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" :placeholder="form.type === 'balance' ? 'Ej: Saldo a mayo 2026' : 'Ej: Proyecto Web - Cliente X'" />
          </div>

          <!-- Balance mode: ask for new total balance -->
          <div v-if="form.type === 'balance'" class="w-44">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Nuevo saldo total</label>
            <input v-model.number="form.balance" type="number" step="0.01" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" placeholder="Ej: 5000" />
            <p class="text-xs text-gray-400 mt-1">El monto se calcula automáticamente</p>
          </div>

          <!-- Non-balance mode: ask for amount -->
          <div v-else class="w-44">
            <label class="block text-xs font-semibold text-gray-500 mb-1">Monto (+ ingreso, - gasto)</label>
            <input v-model.number="form.amount" type="number" step="0.01" required class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500" placeholder="Ej: 1500" />
          </div>

          <button type="submit" class="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors" :disabled="submitting">
            {{ submitting ? 'Guardando...' : '+ Registrar' }}
          </button>
        </div>
      </form>

      <div v-if="message" class="mt-3 text-sm font-medium" :class="messageType === 'ok' ? 'text-green-600' : 'text-red-600'">
        {{ message }}
      </div>
    </div>

    <!-- Quick links -->
    <div class="text-center text-sm text-gray-400 space-x-4">
      <router-link to="/upload" class="text-blue-600 hover:underline">Subir Extractos</router-link>
      <span>·</span>
      <router-link to="/entities" class="text-blue-600 hover:underline">Gestionar Entidades</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const API_URL = import.meta.env.VITE_API_URL
const entities = ref([])
const accounts = ref([])  // all accounts: { id, entity_id, account_type, currency }
const submitting = ref(false)
const message = ref('')
const messageType = ref('ok')

const form = ref({
  entity_id: '',
  account_id: '',
  date: new Date().toISOString().slice(0, 10),
  description: '',
  amount: 0,
  balance: null,
  type: 'freelance',
})

const accountTypeLabels = {
  checking: 'Corriente', savings: 'Ahorro', cdt: 'CDT',
  pension: 'Pensión', cesantias: 'Cesantías', spot: 'Spot',
  earn: 'Earn', futures: 'Futures', investment_fund: 'Fondo inversión',
  other: 'Otro',
}
const accountTypeLabel = (t) => accountTypeLabels[t] || t

const filteredAccounts = computed(() => {
  if (!form.value.entity_id) return []
  return accounts.value.filter(a => a.entity_id === Number(form.value.entity_id))
})

function onEntityChange() {
  form.value.account_id = ''
  // If entity has only one account, auto-select it
  const entityAccounts = filteredAccounts.value
  if (entityAccounts.length === 1) {
    form.value.account_id = entityAccounts[0].id
  }
}

async function fetchData() {
  try {
    const [entRes, accRes] = await Promise.all([
      fetch(`${API_URL}/entities`),
      fetch(`${API_URL}/balances`),
    ])
    entities.value = await entRes.json()
    const balances = await accRes.json()
    // Build accounts list from balances response
    accounts.value = balances.map(b => ({
      id: b.account_id,
      entity_id: entities.value.find(e => e.name === b.entity)?.id,
      account_type: b.account_type,
      currency: b.currency,
      balance: b.balance,
    })).filter(a => a.entity_id != null)

    // If navigated with ?account= param, pre-select
    const accountParam = route.query.account
    if (accountParam) {
      const target = accounts.value.find(a => a.id === Number(accountParam))
      if (target) {
        form.value.entity_id = target.entity_id
        form.value.account_id = target.id
      }
    }
  } catch (e) {
    console.error(e)
  }
}

async function addTransaction() {
  submitting.value = true
  message.value = ''
  try {
    const body = {
      account_id: Number(form.value.account_id),
      date: form.value.date,
      description: form.value.description || (form.value.type === 'balance' ? 'Actualización de saldo' : ''),
      type: form.value.type,
    }
    if (form.value.type === 'balance') {
      body.balance = form.value.balance
    } else {
      body.amount = form.value.amount
    }

    const res = await fetch(`${API_URL}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (res.ok) {
      const data = await res.json()
      if (form.value.type === 'balance') {
        message.value = `✅ Saldo registrado. Variación: ${data.amount >= 0 ? '+' : ''}${data.amount}`
      } else {
        message.value = '✅ Transacción registrada correctamente'
      }
      messageType.value = 'ok'
      form.value.description = ''
      form.value.amount = 0
      form.value.balance = null
    } else {
      const err = await res.json()
      message.value = '❌ ' + (err.detail || 'Error al guardar')
      messageType.value = 'err'
    }
  } catch (e) {
    message.value = '❌ Error de conexión'
    messageType.value = 'err'
  } finally {
    submitting.value = false
  }
}

onMounted(fetchData)
</script>
