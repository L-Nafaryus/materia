import App from "@/App.vue";

import { createApp } from "vue";
import { createPinia } from "pinia";
import { plugins, router, client, style } from "@";


const debug = import.meta.hot;

client.setConfig({
    baseURL: debug ? "http://localhost:54601" : "/",
    withCredentials: true,
});

createApp(App)
    .use(createPinia())
    .use(router)
    .directive("click-outside", plugins.clickOutside)
    .directive("tooltip", plugins.tooltip)
    .mount('#app');

