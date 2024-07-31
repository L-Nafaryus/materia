<script setup lang="ts">
import Base from "@/views/Base.vue";

import { ref, onMounted, watch, getCurrentInstance } from "vue";

import router from "@/router";
import { user } from "@/api";
import { useUserStore, useMiscStore } from "@/stores";

const error = ref(null);
const userStore = useUserStore();
const miscStore = useMiscStore();

const login = defineModel("login");
const name = defineModel("name");
const email = defineModel("email");

const image_file = ref(null);
const progress = ref(0);
const avatar_preview = ref(null);

onMounted(async () => {
    miscStore.p_current_tab = 0;

    login.value = userStore.current.login;
});

function uploadFile(event) {
    image_file.value = event.target.files.item(0);
    avatar_preview.value = URL.createObjectURL(image_file.value);
    progress.value = 0;

}

async function submitFile() {
    await user.avatar(image_file.value, (event) => {
        progress.value = Math.round((100 * event.loaded) / event.total);
    })
        .catch(error => { error.value = error });
}

</script>

<template>
    <div class="flex flex-col gap-4 ml-auto mr-auto w-full">
        <div class="border rounded border-zinc-500 w-full flex-col">
            <h1 class="pl-5 pr-5 pt-2 pb-2">Profile Info</h1>
            <div class="border-t border-zinc-500 p-5">
                <form @submit.prevent class="">
                    <div>
                        <label class="block mb-2" for="login">Login</label>
                        <input v-model="login" name="login"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div>
                        <label class="block mb-2" for="name">Username</label>
                        <input v-model="name" name="name"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div>
                        <label class="block mb-2 " for="email">Email</label>
                        <input v-model="email" email="email" disabled
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div class="border-t border-zinc-500 ml-0 mr-0 mt-3 mb-3"></div>
                    <button
                        class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5 ml-auto mr-0 block">Update</button>
                </form>
            </div>
        </div>

        <div class="border rounded border-zinc-500 w-full flex-col">
            <h1 class="pl-5 pr-5 pt-2 pb-2">User avatar</h1>
            <div class="border-t border-zinc-500 p-5">
                <form @submit.prevent class="" enctype="multipart/form-data">
                    <div>
                        <label class="block mb-2 " for="avatar">New avatar</label>
                        <input name="avatar" type="file" ref="file" accept="image/png,image/jpeg,image/jpg"
                            @change="uploadFile"
                            class="w-full bg-zinc-800 pl-3 pr-3 pt-2 pb-2 mb-4 outline-none rounded border border-zinc-500 hover:border-zinc-400 focus:border-green-800">
                    </div>
                    <div class="flex flex-row gap-8 items-center">
                        <div class="max-w-64"><img :src="avatar_preview"></div>
                        <div class="max-w-32"><img :src="avatar_preview"></div>
                        <div class="max-w-16"><img :src="avatar_preview"></div>
                    </div>
                    <div class="border-t border-zinc-500 ml-0 mr-0 mt-3 mb-3"></div>
                    <button @click="submitFile" :disabled="!image_file"
                        class="rounded bg-zinc-500 hover:bg-zinc-400 pb-2 pt-2 pl-5 pr-5 ml-auto mr-0 block">Update
                        avatar</button>
                    <p>{{ progress }}</p>
                </form>
            </div>
        </div>
    </div>
</template>
