<script setup lang="ts">
import { ref, onMounted } from "vue";
import { router, api, store } from "@";
import NavBar from "@/components/NavBar.vue";
import DropdownMenu from "@/components/DropdownMenu.vue";

const userStore = store.useUser();
const error = ref(null);

const signout = async () => {
    await api.authSignout()
        .then(async () => {
            userStore.clear();
            router.push({ path: "/" });
        })
        .catch(err => { error.value = err; });
};

</script>

<template>
    <div class="flex-grow sm:pb-20">
        <NavBar>
            <template #left>
                <RouterLink class="link-button" to="/">Home</RouterLink>
            </template>
            <template #right v-if="userStore.info">
                <RouterLink v-if="userStore.info.is_admin" :to="{ name: 'settings' }" class="link-button">Settings
                </RouterLink>
                <DropdownMenu>
                    <template #button>
                        <div class="link-button flex">
                            <span>{{ userStore.info.name }}</span>
                            <div class="max-w-6 ml-4" v-if="userStore.avatar">
                                <img :src="userStore.avatar">
                            </div>
                        </div>
                    </template>
                    <template #content>
                        <div
                            class="absolute z-20 flex flex-col left-auto right-0 mt-4 mr-3 bg-ctp-mantle border rounded border-ctp-overlay0">
                            <RouterLink :to="{ name: 'repository', params: { user: userStore.info.lower_name } }"
                                class="button">
                                Repository</RouterLink>
                            <RouterLink :to="{ name: 'prefs' }" class="button">
                                Preferencies</RouterLink>

                            <div class="hline"></div>
                            <div @click="signout" class="button">
                                Sign Out</div>
                        </div>
                    </template>
                </DropdownMenu>
            </template>
            <template #right v-else>
                <RouterLink class="link-button" to="/auth/signin">Sign In</RouterLink>
            </template>
        </NavBar>

        <main class="w-full max-w-[1000px] ml-auto mr-auto">
            <slot></slot>
        </main>
    </div>


    <footer class="flex justify-between pb-2 pt-2 pl-5 pr-5 bg-ctp-mantle">
        <a href="/">Made with glove by Elnafo, 2024</a>
        <div>

        </div>
        <a href="/api/docs">API</a>
    </footer>
</template>

<style></style>
