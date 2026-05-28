<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <aside class="w-64 bg-gray-900 text-gray-300 flex flex-col shadow-xl">
      <!-- Logo / Brand -->
      <div class="p-5 border-b border-gray-700">
        <h1 class="text-xl font-bold text-white tracking-tight">💰 Finance</h1>
        <p class="text-xs text-gray-500 mt-1">Control total de activos</p>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 overflow-y-auto py-4 px-3">
        <p class="px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Principal</p>

        <router-link
          v-for="item in mainLinks"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors"
          :class="$route.path === item.to
            ? 'bg-blue-600/30 text-blue-300 font-semibold'
            : 'hover:bg-gray-800 text-gray-400 hover:text-white'"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>

        <p class="px-3 mt-6 mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Gestión</p>

        <router-link
          v-for="item in manageLinks"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors"
          :class="$route.path === item.to
            ? 'bg-blue-600/30 text-blue-300 font-semibold'
            : 'hover:bg-gray-800 text-gray-400 hover:text-white'"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>

        <p class="px-3 mt-6 mb-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Planificación</p>

        <router-link
          v-for="item in planLinks"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors"
          :class="$route.path === item.to
            ? 'bg-blue-600/30 text-blue-300 font-semibold'
            : 'hover:bg-gray-800 text-gray-400 hover:text-white'"
        >
          <span class="text-lg">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <!-- Footer -->
      <div class="p-4 border-t border-gray-700 text-xs text-gray-500">
        Finance v2.0
      </div>
    </aside>

    <!-- Main content -->
    <main class="flex-1 overflow-y-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
const mainLinks = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/entities', label: 'Entidades', icon: '🏦' },
]

const manageLinks = [
  { to: '/upload', label: 'Subir Extractos', icon: '📤' },
  { to: '/transactions', label: 'Transacciones', icon: '💳' },
]

const planLinks = [
  { to: '/budget', label: 'Presupuesto', icon: '🎯' },
  { to: '/retirement', label: 'Plan de retiro', icon: '🌅' },
]
</script>
