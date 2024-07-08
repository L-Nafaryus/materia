<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/Error.vue";

import { ref, onMounted, watch } from "vue";
import { onBeforeRouteUpdate, useRoute } from "vue-router"

import { repository } from "@/api";
import { useUserStore } from "@/stores";
import router from "@/router";

const route = useRoute();
const userStore = useUserStore();
const error = ref<string>(null);

const repository_info = ref(null);
const is_created = ref(null);

onMounted(async () => {
    await repository.info()
        .then(async _repository_info => {
            is_created.value = true;
            repository_info.value = _repository_info;
        })
        .catch(err => {
            is_created.value = false;
        });
});

async function create_repository() {
    await repository.create()
        .then(async () => {
            await repository.info()
                .then(async _repository_info => {
                    repository_info.value = _repository_info;
                })
                .catch(err => {
                    error.value = err;
                });

            is_created.value = true;
        })
        .catch(err => {
            error.value = err;
        })
}

function round_size(size: number, mesure: string) {
    if (mesure == "GB") {
        return size / 8 / 1024 / 1024;
    } else if (mesure == "MB") {
        return size / 8 / 1024;
    }
}

function size_procent() {
    return Math.round(repository_info.value.used / repository_info.value.capacity) * 100;
}

</script>

<template>
    <Base>
    <Error v-if="error">{{ error }}</Error>
    <section v-if="is_created">
        <div class="flex items-center">
            <div class="w-full rounded-full h-2.5 bg-ctp-surface0">
                <div class="bg-ctp-lavender h-2.5 rounded-full" :style="{ width: size_procent() + '%' }"></div>
            </div>
            <span class="min-w-32 text-center">{{ round_size(repository_info.used, "GB") }} / {{
                round_size(repository_info.capacity, "GB") }} GB</span>
        </div>
    </section>
    <section v-else>
        <p>It looks like you don't have a repository yet...</p>
        <div class="flex justify-center mt-8">
            <button @click="create_repository" class="button">+ Create repository</button>
        </div>
    </section>
    </Base>
</template>
