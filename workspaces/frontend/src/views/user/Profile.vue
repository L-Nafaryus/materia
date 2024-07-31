<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/error/Error.vue";

import { ref, onMounted, watch, getCurrentInstance } from "vue";
import { onBeforeRouteUpdate, useRoute } from "vue-router"

import { user } from "@/api";
import { useUserStore } from "@/stores";

const route = useRoute();
const userStore = useUserStore();
const error = ref<string>(null);

const person = ref<user.User>(null);
const avatar = ref<user.Image>(null);

async function profile(login: string) {
    await user.profile(login)
        .then(async user => { person.value = user; })
        .then(async () => {
            if (person.value.avatar?.length) {
                await user.get_avatar(person.value.avatar)
                    .then(async _avatar => { avatar.value = _avatar; })
            }
        })
        .catch(error => { error.value = error; });
};

onMounted(async () => {
    await profile(route.params.user);
});

watch(route, async (to, from) => {
    await profile(to.params.user);
});
</script>

<template>
    <Base>
    <div class="ml-auto mr-auto w-1/2 pt-5 pb-5">
        <Error v-if="error">{{ error }}</Error>
        <p v-if="person">{{ person.name }}</p>
        <div class="max-w-8" v-if="avatar"><img :src="avatar"></div>
    </div>
    </Base>
</template>
