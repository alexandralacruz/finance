<template>
    <div class="empty-state">
      <p class="icon">📭</p>
      <p class="message">
        <slot />
      </p>
    </div>
  </template>
  
  <style scoped>
  .empty-state {
    text-align: center;
    padding: 2rem;
    color: #6b7280;
  }
  
  .icon {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }
  
  .message {
    font-size: 1rem;
  }
  </style>
  