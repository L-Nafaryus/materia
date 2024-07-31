<script setup lang="ts">
import Base from "@/views/Base.vue";

import { ref, onMounted, watch, getCurrentInstance } from "vue";

import { useMiscStore } from "@/stores";

const miscStore = useMiscStore();

</script>

<template>
    <Base>
    <div class="flex gap-4 mt-4 ml-auto mr-auto content ">
        <Router-View />
        <div>
            <div class="border rounded border-zinc-500 flex-col w-64 side-nav">
                <h1 class="pl-5 pr-5 pt-2 pb-2">User Preferencies</h1>
                <RouterLink :to="{ name: 'prefs-profile' }" :class="{ 'bg-zinc-600': miscStore.p_current_tab === 0 }"
                    class="flex min-w-7 pl-5 pr-5 pt-2 pb-2 hover:bg-zinc-600 border-t border-zinc-500">
                    Profile</RouterLink>
                <RouterLink :to="{ name: 'prefs-account' }" :class="{ 'bg-zinc-600': miscStore.p_current_tab === 1 }"
                    class="flex min-w-7 pl-5 pr-5 pt-2 pb-2 hover:bg-zinc-600 border-t border-zinc-500">
                    Account</RouterLink>
            </div>
        </div>
    </div>
    </Base>
</template>

<style>
.content {
    width: 1280px;
    max-width: calc(100% - 64px);
}

.side-nav {
    transform: perspective(300px) rotateY(-8deg) scaleY(1.05);
}
</style>
