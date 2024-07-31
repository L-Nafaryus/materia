import App from "@/App.vue";

import { createApp } from "vue";
import { createPinia } from "pinia";

import router from "@/router";
import { click_outside } from "@/directives/click-outside";
import "@/assets/style.css";

createApp(App)
    .use(createPinia())
    .use(router)
    .directive("click-outside", click_outside)
    .mount('#app');

