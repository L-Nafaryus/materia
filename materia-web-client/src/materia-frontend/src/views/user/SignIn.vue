<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/error/Error.vue";

import { ref, onMounted } from "vue";

import router from "@/router";
import { user } from "@/api";
import { useUserStore } from "@/stores";

const email_or_username = defineModel("email_or_username");
const password = defineModel("password");

const userStore = useUserStore();
const error = ref(null);

onMounted(async () => {
    if (userStore.current) {
        router.replace({ path: "/" });
    }
});

async function signin() {
    const body: user.UserCredentials = {
        name: null,
        password: password.value,
        email: null
    };

    if (/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email_or_username.value)) {
        body.name = "";
        body.email = email_or_username.value;
    } else {
        body.name = email_or_username.value;
    }

    await user.signin(body)
        .then(async () => {
            //userStore.current = user;
            router.push({ path: "/" });
        })
        .catch(error => { error.value = error; });
};
</script>

<template>
    <Base>
    <div class="ml-auto mr-auto w-1/2 pt-5 pb-5">
        <h1 class="text-center pt-5 pb-5 border-b border-zinc-500">Sign In</h1>
        <form @submit.prevent class="m-auto pt-5 pb-5">
            <div class="mb-5 ml-auto mr-auto">
                <label for="email_or_login" class="text-right w-64 inline-block mr-5">Email or Username</label>
                <input v-model="email_or_username" placeholder="" name="email_or_login" required
                    class="w-1/2 bg-zinc-800 pl-3 pr-3 pt-2 pb-2 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
            </div>
            <div class="mb-5 ml-auto mr-auto">
                <label for="password" class="text-right w-64 inline-block mr-5">Password</label>
                <input v-model="password" placeholder="" type="password" name="password" required
                    class="w-1/2 bg-zinc-800 pl-3 pr-3 pt-2 pb-2 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
            </div>
            <div class="mb-5 ml-auto mr-auto">
                <label class="text-right w-64 inline-block mr-5"></label>
                <div class="flex justify-between items-center w-1/2 m-auto">
                    <button @click="signin" class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5">Sign
                        In</button>
                    <p>or</p>
                    <button @click="$router.push('/user/register')"
                        class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5">Sign
                        Up</button>
                </div>
            </div>
        </form>
        <Error v-if="error">{{ error }}</Error>
    </div>
    </Base>
</template>
