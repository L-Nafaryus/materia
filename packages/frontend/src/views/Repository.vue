<script setup lang="ts">
import Base from "@/views/Base.vue";
import Error from "@/components/Error.vue";
import IconDirectory from "@/components/icons/IconDirectory.vue";
import IconFile from "@/components/icons/IconFile.vue";
import ContextMenu from "@/components/ContextMenu.vue";
import DragItem from "@/components/DragItem.vue";
import DropItem from "@/components/DropItem.vue";
import RepositoryBrowser from "@/components/RepositoryBrowser.vue";
import Modal from "@/components/Modal.vue";
import Uploader from "@/components/Uploader.vue";

import { ref, shallowRef, onMounted, watch } from "vue";
import { onBeforeRouteUpdate, useRoute } from "vue-router"
import { filesize } from "filesize";
import { router, api, store, types, api_types, check_auth } from "@";


const route = useRoute();
const userStore = store.useUser();
const repoStore = store.useRepository();
const error = ref<object>(null);

onMounted(async () => {
    let path = route.params.pathMatch ? "/" + route.params.pathMatch.join("/") : "/";
    await repoStore.refreshInfo(path, error);
    console.log(route);
});

onBeforeRouteUpdate(async (to, from) => {
    let path = to.params.pathMatch ? "/" + to.params.pathMatch.join("/") : "/";
    userStore.checkAuthorizationRedirect(to.path);
    await repoStore.refreshInfo(path, error);
    console.log("route", route);
    console.log("store", repoStore);
});


const isUploaderOpen = ref(false);

const openUploader = () => {
    isUploaderOpen.value = true;
};
const closeUploader = () => {
    isUploaderOpen.value = false;
};

const isMakeDirectoryOpen = ref(false);
const makeDirectoryName = ref(null);

const openMakeDirectory = () => {
    isMakeDirectoryOpen.value = true;
};

const closeMakeDirectory = () => {
    isMakeDirectoryOpen.value = false;
    makeDirectoryName.value = null;
};

const makeDirectory = async () => {
    await repoStore.makeDirectory(makeDirectoryName.value.value, error);
    closeMakeDirectory();
};

// repoStore.makeDirectory('test', error)
</script>

<template>
    <Base>
    <Error :value="error" />

    <Uploader v-if="repoStore.isCreated" :isOpen="isUploaderOpen" @close-uploader="closeUploader()" />

    <Modal :isOpen="isMakeDirectoryOpen" @close-modal="closeMakeDirectory()">
        <template #header>
            <h2>Create directory</h2>
        </template>
        <template #content>
            <div class="flex mb-8">
                <input ref="makeDirectoryName" class="input mr-2">
                <button class="button" @click="makeDirectory()">Create</button>
            </div>
        </template>
    </Modal>
    <section v-if="repoStore.isCreated">
        <div
            class="flex items-center justify-center fixed bottom-4 bg-ctp-surface0 sm:bg-ctp-crust opacity-90 sm:opacity-100 w-full sm:w-auto sm:relative sm:bottom-auto sm:right-auto my-2">
            <span class="min-w-48 text-center">{{ filesize(repoStore.info.used)
                }}
                / {{ filesize(repoStore.info.capacity)
                }}</span>
            <div class="hidden sm:inline ml-4 mr-4 w-full rounded-full h-2.5 bg-ctp-surface0">
                <div class="bg-ctp-lavender h-2.5 rounded-full" :style="{ width: repoStore.sizePercent() + '%' }"></div>
            </div>

            <button @click="openMakeDirectory" class="button justify-end mr-2">Create</button>
            <button @click="openUploader" class="button justify-end">Upload</button>
        </div>

        <RepositoryBrowser v-if="!error" v-model="repoStore.content" />

    </section>
    <section v-else>
        <p>It looks like you don't have a repository yet...</p>
        <div class="flex justify-center mt-8">
            <button @click="repoStore.create(error)" class="button">+ Create repository</button>
        </div>
    </section>
    </Base>
</template>
