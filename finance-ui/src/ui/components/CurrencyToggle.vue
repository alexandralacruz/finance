<template>
    <div class="flex gap-2">
      <button
        v-for="c in ['USD', 'COP']"
        :key="c"
        @click="$emit('update:modelValue', c)"
        :class="[
          'px-4 py-2 rounded',
          modelValue === c ? 'bg-blue-600 text-white' : 'bg-gray-200'
        ]"
      >
        {{ c }}
      </button>
    </div>
  </template>
  
  <script setup>
  defineProps({
    modelValue: String
  });
  </script>
  