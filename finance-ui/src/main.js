import { createApp } from "vue";
import App from "./ui/App.vue";
import router from './router'
import "./style.css";


createApp(App)
  .use(router)   // 👈 ahora sí existe router-view
  .mount('#app')