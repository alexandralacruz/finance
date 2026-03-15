<template>
  <aside class="sidebar">
    <ul>
      <li :class="{ active: activeMenu === 'upload' }" @click="activeMenu = 'upload'">
        <span>📁</span> Cargar Archivo
      </li>
      <li :class="{ active: activeMenu === 'entities' }" @click="activeMenu = 'entities'">
        <span>🏦</span> Gestionar Entidades
      </li>
      <li :class="{ active: activeMenu === 'categories' }" @click="activeMenu = 'categories'">
        <span>📂</span> Categorías
      </li>
      <li :class="{ active: activeMenu === 'fx' }" @click="activeMenu = 'fx'">
        <span>💱</span> Tasa FX
      </li>
      <li :class="{ active: activeMenu === 'export' }" @click="activeMenu = 'export'">
        <span>📤</span> Exportar
      </li>
    </ul>
  </aside>
</template>

<script setup>
defineProps(['modelValue'])
defineEmits(['update:modelValue'])

const activeMenu = defineModel('modelValue')
</script>

<style scoped>
.sidebar {
  width: 240px;
  background: linear-gradient(180deg, #1f2937, #111827);
  color: #e5e7eb;
  padding: 24px 16px;
  box-shadow: 2px 0 6px rgba(0, 0, 0, 0.15);
}

ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

li {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  transition: all 0.2s ease;
}

li:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

li.active {
  background: rgba(59, 130, 246, 0.25);
  color: #93c5fd;
  font-weight: 600;
}

li span {
  font-size: 20px;
}
</style>