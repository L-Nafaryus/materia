<script setup lang="ts">
import Base from "@/views/Base.vue";

import { ref, onMounted, watch, getCurrentInstance } from "vue";

import router from "@/router";
import { useUserStore, useMiscStore } from "@/stores";

const password = defineModel("password");
const new_password = defineModel("new-password");
const confirm_new_password = defineModel("confirm-new-password");

const email = defineModel("email");
const new_email = defineModel("new-email");

const confirm_password = defineModel("confirm-password");

const error = ref(null);
const userStore = useUserStore();
const miscStore = useMiscStore();

onMounted(async () => {
    miscStore.p_current_tab = 1;

});
</script>

<template>
    <div class="flex flex-col gap-4 ml-auto mr-auto w-full">
        <div class="border rounded border-zinc-500 w-full flex-col bg-zinc-800 bg-opacity-95">
            <h1 class="pl-5 pr-5 pt-2 pb-2">Password</h1>
            <div class="border-t border-zinc-500 p-5">
                <form @submit.prevent class="">
                    <div>
                        <label class="block mb-2" for="password">Current password</label>
                        <input v-model="password" name="password" type="password"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div>
                        <label class="block mb-2" for="new-password">New password</label>
                        <input v-model="new_password" name="new-password" type="password"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div>
                        <label class="block mb-2" for="confirm-new-password">Confirm new password</label>
                        <input v-model="confirm_new_password" name="confirm-new-password" type="password"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div class="border-t border-zinc-500 ml-0 mr-0 mt-3 mb-3"></div>
                    <button class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5 ml-auto mr-0 block">Update
                        password</button>
                </form>
            </div>
        </div>

        <div class="border rounded border-zinc-500 w-full flex-col bg-zinc-800 bg-opacity-95">
            <h1 class="pl-5 pr-5 pt-2 pb-2">Email</h1>
            <div class="border-t border-zinc-500 p-5">
                <form @submit.prevent class="">
                    <div>
                        <label class="block mb-2" for="email">Email</label>
                        <strong class="block w-full mb-4">{{ email }}</strong>
                    </div>
                    <div>
                        <label class="block mb-2" for="new-email">New email</label>
                        <input v-model="new_email" name="new-email" type="email"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div class="border-t border-zinc-500 ml-0 mr-0 mt-3 mb-3"></div>
                    <button class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5 ml-auto mr-0 block">Update
                        email</button>
                </form>
            </div>
        </div>

        <div class="border rounded border-red-500 w-full flex-col bg-zinc-800 bg-opacity-95">
            <h1 class="pl-5 pr-5 pt-2 pb-2">Delete account</h1>
            <div class="border-t border-red-500 p-5">
                <form @submit.prevent class="">
                    <div>
                        <label class="block mb-2" for="confirm-password">Password</label>
                        <input v-model="confirm_password" name="confirm-password" type="password"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div class="border-t border-zinc-500 ml-0 mr-0 mt-3 mb-3"></div>
                    <button
                        class="rounded bg-red-500 hover:bg-red-400 pb-2 pt-2 pl-5 pr-5 ml-auto mr-0 block">Confirm</button>
                </form>
            </div>
        </div>
    </div>
</template>
