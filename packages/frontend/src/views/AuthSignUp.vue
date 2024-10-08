<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/Error.vue";

import { ref, onMounted } from "vue";
import { router, api, schemas, store } from "@";


const login = defineModel("login");
const email = defineModel("email");
const password = defineModel("password");

const userStore = store.useUser();
const error = ref(null);

onMounted(async () => {
    if (userStore.current) {
        router.replace({ name: "home" });
    }
});

const signup = async () => {
    if (!login.value || !email.value || !password.value) {
        return;
    }
    await api.authSignup({ body: { name: login.value, password: password.value, email: email.value }, throwOnError: true })
        .then(async () => { router.replace({ name: "signin" }); })
        .catch(err => { error.value = err; });
};
</script>

<template>
    <Base>
    <div class="ml-auto mr-auto w-1/2 pt-5 pb-5">
        <h1 class="text-center">Sign Up</h1>
        <form @submit.prevent>
            <div class="mb-5">
                <label for="login">Login</label>
                <input v-model="login" type="" placeholder="" name="login" required class="input">
            </div>
            <div class="mb-5">
                <label for="email">Email Address</label>
                <input v-model="email" type="email" placeholder="" name="email" required class="input">
            </div>
            <div class="mb-5">
                <label for="password">Password</label>
                <input v-model="password" placeholder="" type="password" name="password" required class="input">
            </div>
            <div class="mb-5 flex justify-between items-center">
                <button @click="signup" class="button">Sign Up</button>
            </div>
        </form>
        <Error :value="error" />
    </div>
    </Base>
</template>
