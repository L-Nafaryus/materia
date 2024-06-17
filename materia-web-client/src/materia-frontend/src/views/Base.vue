<script setup lang="ts">
import NavBar from "@/components/NavBar.vue";
import DropdownMenu from "@/components/DropdownMenu.vue";

import { ref, onMounted } from "vue";

import router from "@/router";
import { user } from "@/api";
import { useUserStore } from "@/stores";

const userStore = useUserStore();
const error = ref(null);

async function signout() {
    await user.logout()
        .then(async () => {
            userStore.clear();
            router.push({ path: "/" });
        })
        .catch(error => { error.value = error; });
}

</script>

<template>
    <div class="flex-grow pb-20">
        <NavBar>
            <template #left>
                <!-- TODO: logo -->
            </template>
            <template #right>
                <DropdownMenu v-if="userStore.current">
                    <template #button>
                        <div class="pl-3 pr-3 flex gap-2 items-center rounded hover:bg-zinc-600 cursor-pointer">
                            <div class="max-w-8" v-if="userStore.avatar"><img :src="userStore.avatar"></div>
                            <span class="flex min-w-9 min-h-9 items-center">{{userStore.current.login }}</span>
                        </div>
                    </template>
                    <template #content>
                        <div
                            class="absolute z-20 flex flex-col left-auto right-0 mt-4 bg-zinc-700 border rounded border-zinc-500 mr-3">
                            <RouterLink :to="{ name: 'profile', params: { user: userStore.current.login } }"
                                class="flex min-w-7 pl-5 pr-5 pt-1 pb-1 hover:bg-zinc-600">
                                Profile</RouterLink>
                            <RouterLink :to="{ name: 'prefs' }"
                                class="flex min-w-7 pl-5 pr-5 pt-1 pb-1 hover:bg-zinc-600">
                                Preferencies</RouterLink>
                            <div class="border-t border-zinc-500 ml-0 mr-0"></div>
                            <RouterLink v-if="userStore.current.is_admin" :to="{ name: 'settings' }"
                                class="flex min-w-7 pl-5 pr-5 pt-1 pb-1 hover:bg-zinc-600">
                                Settings</RouterLink>
                            <div class="border-t border-zinc-500 ml-0 mr-0"></div>
                            <div @click="signout"
                                class="flex min-w-7 pl-5 pr-5 pt-1 pb-1 hover:bg-zinc-600 cursor-pointer">
                                Sign Out</div>
                        </div>
                    </template>
                </DropdownMenu>

                <RouterLink v-if="!userStore.current"
                    class="flex min-w-9 min-h-9 pt-1 pb-1 pl-3 pr-3 rounded hover:bg-zinc-600" to="/user/login">
                    Sign In</RouterLink>
            </template>
        </NavBar>

        <main>
            <slot></slot>

        </main>
    </div>

    <div class="relative overflow-hidden h-full ">
    </div>
    <footer
        class="flex justify-between pb-2 pt-2 pl-5 pr-5 bg-gradient-to-b from-zinc-800 to-zinc-900 border-t border-t-zinc-500">
        <a href="/">Made with glove</a>
        <a href="/api/docs">API</a>
    </footer>
</template>

<style></style>
