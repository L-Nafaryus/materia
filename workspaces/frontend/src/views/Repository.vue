<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/Error.vue";
import IconDirectory from "@/components/icons/IconDirectory.vue";
import IconFile from "@/components/icons/IconFile.vue";
import ContextMenu from "@/components/ContextMenu.vue";

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
const repository_content = ref(null);

onMounted(async () => {
    await repository.info()
        .then(async _repository_info => {
            is_created.value = true;
            repository_info.value = _repository_info;
        })
        .catch(err => {
            is_created.value = false;
        });

    if (is_created.value) {
        await repository.content()
            .then(async _repository_content => {
                repository_content.value = _repository_content;
            })
            .catch(err => {
                error.value = err;
            })
    }
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

function format_creation_time(timestamp: number): string {
    const date = new Date(timestamp * 1000);

    return `${date.getDate()}-${date.getMonth()}-${date.getFullYear()} ${date.getHours()}:${date.getMinutes()}`;
}

const showMenu = ref(false);
const ctxMenuPosX = ref(0);
const ctxMenuPosY = ref(0);
const targetRow = ref({});
const contextMenuActions = ref([
    { label: 'Edit', action: 'edit' },
    { label: 'Delete', action: 'delete' },
]);

const showContextMenu = (event, user) => {
    event.preventDefault();
    showMenu.value = true;
    targetRow.value = user;
    ctxMenuPosX.value = event.clientX;
    ctxMenuPosY.value = event.clientY;
};

const closeContextMenu = () => {
    showMenu.value = false;
};

function handleActionClick(action) {
    console.log(action);
    console.log(targetRow.value);
}

function close_menu() {
    showMenu.value = false;
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
            <span class="min-w-48 text-center">{{ round_size(repository_info.used, "MB").toFixed(2) }} MB / {{
                round_size(repository_info.capacity, "GB") }} GB</span>

        </div>

        <table v-if="repository_content" class="table-auto w-full mt-8 mb-8 pl-8 pr-8 text-ctp-text">
            <tbody>
                <tr class="hover:bg-ctp-surface0" v-for="directory in repository_content.directories"
                    @contextmenu.prevent="showContextMenu($event, directory)">
                    <td>
                        <IconDirectory />
                        <div class="inline ml-4">{{ directory.name }}</div>
                    </td>
                    <td class="text-right">-</td>
                    <td class="text-right w-48">
                        {{ format_creation_time(directory.created) }}
                    </td>
                </tr>
                <tr class="hover:bg-ctp-surface0" v-for="file in repository_content.files">
                    <td>
                        <IconFile />
                        <div class="inline ml-4">{{ file.name }}</div>
                    </td>
                    <td class="text-right">{{ round_size(file.size, "MB").toFixed(2) }} MB</td>
                    <td class="text-right w-48">
                        {{ format_creation_time(file.created) }}
                    </td>
                </tr>
            </tbody>
        </table>

        <ContextMenu v-if="showMenu" :actions="contextMenuActions" @action-clicked="handleActionClick" :x="ctxMenuPosX"
            :y="ctxMenuPosY" v-click-outside="close_menu" />
    </section>
    <section v-else>
        <p>It looks like you don't have a repository yet...</p>
        <div class="flex justify-center mt-8">
            <button @click="create_repository" class="button">+ Create repository</button>
        </div>
    </section>
    </Base>
</template>
