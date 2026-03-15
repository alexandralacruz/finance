<template>
  <div class="card">
    <div class="bg-white p-4 rounded-xl shadow">
      <p class="text-sm text-gray-500">Tasa del día</p>
      <h2 class="text-2xl font-bold">
        1 USD = {{ rate.toLocaleString() }} COP
      </h2>
    </div>
  </div>
  </template>
  
  <script setup>
    const API_URL = import.meta.env.VITE_API_URL;
    import { ref, onMounted } from "vue";

const rate = ref(0);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
  try {
    const response = await fetch(`${API_URL}/exchange-rate`);

    if (!response.ok) {
      throw new Error("Error obteniendo la tasa");
    }

    const data = await response.json();

    rate.value = data.rate; // viene del backend
    date.value = data.date; // fecha real del mercado
  } catch (err) {
    console.error(err);
    error.value = "No se pudo cargar la tasa";
  } finally {
    loading.value = false;
  }
});
  </script>


  <style scoped>
    .card {
      background: white;
      border-radius: 12px;
      padding: 1rem;
      box-shadow: 0 8px 24px rgba(0,0,0,0.06);
    }
    </style>