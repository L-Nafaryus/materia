import { defineStore } from "pinia";
import { ref, type Ref } from "vue";

import { user } from "@/api";

export const useUserStore = defineStore("user", () => {
    const current: Ref<user.User | null> = ref(null);
    const avatar: Ref<Blob | null> = ref(null);

    function clear() {
        current.value = null;
        avatar.value = null;
    }

    return { current, avatar, clear };
});

export const useMiscStore = defineStore("misc", () => {
    // preferencies current tab
    const p_current_tab: Ref<number> = ref(0);

    return { p_current_tab };
});
