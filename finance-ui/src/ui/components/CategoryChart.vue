<template>
  <div class="card">
    <div class="bg-white p-4 rounded-xl shadow">
      <h3 class="font-semibold mb-3">Gastos por categoría</h3>
      <canvas ref="canvas"></canvas>
    </div>
  </div>
  </template>
  
  <script setup>
  import { onMounted, ref } from "vue";
  import Chart from "chart.js/auto";
  
  const canvas = ref(null);
  
  onMounted(() => {
    new Chart(canvas.value, {
      type: "doughnut",
      data: {
        labels: ["Supermercado", "Servicios", "Transferencias", "Otros"],
        datasets: [
          {
            data: [1200, 900, 700, 400],
            backgroundColor: ["#2563eb", "#16a34a", "#f59e0b", "#dc2626"]
          }
        ]
      }
    });
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