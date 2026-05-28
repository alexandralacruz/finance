<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold text-gray-800 mb-2">Subir Extractos</h1>
    <p class="text-sm text-gray-500 mb-6">Carga archivos de extractos bancarios o de inversión</p>

    <!-- Upload form -->
    <div class="glass-card rounded-2xl p-6 mb-6">
      <div class="flex flex-wrap gap-4 items-end mb-4">
        <div class="w-48">
          <label class="block text-xs font-semibold text-gray-500 mb-1">Entidad</label>
          <select v-model="selectedEntity" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500">
            <option value="">Seleccionar...</option>
            <option v-for="e in entities" :key="e.name" :value="e.name">{{ e.name }}</option>
          </select>
        </div>

        <label class="cursor-pointer bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors inline-block" :class="{ 'opacity-50 pointer-events-none': !selectedEntity }">
          <input type="file" multiple accept=".csv,.xls,.xlsx" @change="onFilesSelected" class="hidden" :disabled="!selectedEntity" />
          📎 Seleccionar archivos
        </label>

        <button
          @click="upload"
          :disabled="!files.length || uploading"
          class="bg-green-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ uploading ? 'Subiendo...' : '⬆️ Subir' }}
        </button>
      </div>

      <!-- Selected files -->
      <div v-if="files.length" class="mb-4">
        <p class="text-xs text-gray-500 mb-2">{{ files.length }} archivo(s) seleccionado(s):</p>
        <div v-for="(f, i) in files" :key="i" class="flex items-center gap-2 text-sm text-gray-700 py-1">
          <span>📄</span>
          <span>{{ f.name }}</span>
          <span class="text-gray-400 text-xs">({{ (f.size / 1024).toFixed(1) }} KB)</span>
        </div>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="glass-card rounded-2xl p-6">
      <h2 class="text-lg font-semibold text-gray-700 mb-4">Resultados</h2>

      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-green-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-green-600">{{ results.total?.new || 0 }}</p>
          <p class="text-xs text-green-700 mt-1">Nuevas transacciones</p>
        </div>
        <div class="bg-yellow-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-yellow-600">{{ results.total?.duplicates || 0 }}</p>
          <p class="text-xs text-yellow-700 mt-1">Duplicadas</p>
        </div>
        <div class="bg-red-50 rounded-xl p-4 text-center">
          <p class="text-2xl font-bold text-red-600">{{ results.total?.errors || 0 }}</p>
          <p class="text-xs text-red-700 mt-1">Errores</p>
        </div>
      </div>

      <!-- File details -->
      <div v-if="results.files?.length" class="space-y-2">
        <div v-for="(f, i) in results.files" :key="i" class="flex justify-between items-center p-3 rounded-lg border border-gray-100 text-sm">
          <span class="text-gray-700">📄 {{ f.file }}</span>
          <div class="flex gap-3">
            <span v-if="f.error" class="text-red-500">Error: {{ f.error }}</span>
            <template v-else>
              <span class="text-green-600">{{ f.new }} nuevas</span>
              <span class="text-yellow-600">{{ f.duplicates }} dup</span>
              <span class="text-red-500">{{ f.errors }} err</span>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const API_URL = import.meta.env.VITE_API_URL
const entities = ref([])
const selectedEntity = ref('')
const files = ref([])
const uploading = ref(false)
const results = ref(null)

onMounted(async () => {
  try {
    const res = await fetch(`${API_URL}/entities`)
    entities.value = await res.json()
  } catch (e) {
    console.error(e)
  }
})

function onFilesSelected(e) {
  files.value = Array.from(e.target.files || [])
}

async function upload() {
  if (!selectedEntity.value || !files.value.length) return
  uploading.value = true
  results.value = null

  try {
    const formData = new FormData()
    files.value.forEach(f => formData.append('files', f))

    const res = await fetch(`${API_URL}/upload/${selectedEntity.value}`, {
      method: 'POST',
      body: formData,
    })
    results.value = await res.json()
    files.value = []
  } catch (e) {
    results.value = { total: { errors: 1 }, files: [{ file: 'error', error: e.message }] }
  } finally {
    uploading.value = false
  }
}
</script>
