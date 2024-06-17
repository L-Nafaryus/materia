<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/error/Error.vue";

import { ref } from "vue";

import router from "@/router";
import { user } from "@/api";

const login = defineModel("login");
const email = defineModel("email");
const password = defineModel("password");

const error = ref(null);

async function signup() {
    await user.register({ login: login.value, password: password.value, email: email.value })
        .then(async user => { router.push({ path: "/user/login" }); })
        .catch(error => { error.value = error; });
};
</script>

<template>
    <Base>
    <div class="ml-auto mr-auto w-1/2 pt-5 pb-5">
        <h4 class="text-center pt-5 pb-5 border-b border-zinc-500">Sign Up</h4>
        <form @submit.prevent class="m-auto pt-5 pb-5">
            <div class="mb-5 ml-auto mr-auto">
                <label for="login" class="text-right w-64 inline-block mr-5">Login</label>
                <input v-model="login" type="" placeholder="" name="login" required
                    class="w-1/2 bg-zinc-800 pl-3 pr-3 pt-2 pb-2 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
            </div>
            <div class="mb-5 ml-auto mr-auto">
                <label for="email" class="text-right w-64 inline-block mr-5">Email Address</label>
                <input v-model="email" type="email" placeholder="" name="email" required
                    class="w-1/2 bg-zinc-800 pl-3 pr-3 pt-2 pb-2 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
            </div>
            <div class="mb-5 ml-auto mr-auto">
                <label for="password" class="text-right w-64 inline-block mr-5">Password</label>
                <input v-model="password" placeholder="" type="password" name="password" required
                    class="w-1/2 bg-zinc-800 pl-3 pr-3 pt-2 pb-2 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
            </div>
            <div class="mb-5 ml-auto mr-auto">
                <label class="text-right w-64 inline-block mr-5"></label>
                <button @click="signup" class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5">Sign
                    Up</button>
            </div>
        </form>
        <Error v-if="error">{{ error.message }}</Error>
    </div>
    </Base>
</template>
