import { defineStore } from "pinia";
import { ref, type Ref } from "vue";

import { user } from "@/api";
import { resources } from "@";

export const useUserStore = defineStore("user", () => {
    const info: Ref<user.UserInfo | null> = ref(null);
    const avatar: Ref<resources.Image | null> = ref(null);

    function clear() {
        info.value = null;
        avatar.value = null;
    }

    return { info, avatar, clear };
});

export const useMiscStore = defineStore("misc", () => {
    // preferencies current tab
    const p_current_tab: Ref<number> = ref(0);

    return { p_current_tab };
});
