<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/Error.vue";

import { ref, onMounted } from "vue";

import router from "@/router";
import { api } from "@";
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
    if (!email_or_username.value || !password.value) {
        return;
    }

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

    await api.auth.signin(body)
        .then(async () => {
            //userStore.current = user;
            router.push({ path: "/" });
        })
        .catch(err => { error.value = err.message; });
};
</script>

<template>
    <Base>
    <div class="ml-auto mr-auto w-1/2 pt-5 pb-5">
        <h1 class="text-center text-ctp-text pt-5 pb-5 border-b border-ctp-overlay0 mb-5">Sign In</h1>
        <form @submit.prevent>
            <div class="mb-5">
                <label for="email_or_login">Email or Username</label>
                <input v-model="email_or_username" placeholder="" name="email_or_login" required class="input">
            </div>
            <div class="mb-5">
                <label for="password">Password</label>
                <input v-model="password" placeholder="" type="password" name="password" required class="input">
            </div>
            <div class="mb-5 flex justify-between items-center">
                <button @click="signin" class="button">Sign In</button>
                <button @click="$router.push('/user/register')" class="button">Sign Up</button>
            </div>
        </form>
        <Error v-if="error">{{ error }}</Error>
    </div>
    </Base>
</template>
