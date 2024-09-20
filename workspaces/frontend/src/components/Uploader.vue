<script setup lang="ts">
import Modal from "@/components/Modal.vue";
import Tooltip from "@/components/Tooltip.vue";
import IconDelete from "@/components/icons/IconDelete.vue";
import IconRemove from "@/components/icons/IconRemove.vue";
import IconUpload from "@/components/icons/IconUpload.vue";
import IconAccept from "@/components/icons/IconAccept.vue";
import { filesize } from "filesize";
import { ref, shallowRef } from "vue";
import { store } from "@";

const props = defineProps({
    isOpen: Boolean,
});

const emit = defineEmits(["close-uploader"]);

const closeUploader = (action) => {
    emit("close-uploader", action);
};

const inputFileRef = shallowRef();
const uploaderStore = store.useUploader();

</script>

<template>
    <Modal :isOpen="isOpen" @close-modal="closeUploader">
        <template #header>
            <h2>Uploader</h2>
        </template>
        <template #content>
            <div class="flex mb-8">
                <input type="file" multiple ref="inputFileRef" @change="uploaderStore.loadFiles($event)"
                    class="input-file" />

                <button class="button ml-2" :disabled="uploaderStore.files.length === 0"
                    @click="uploaderStore.uploadFiles">Upload</button>
                <button class="button ml-2 text-ctp-red" @click="uploaderStore.removeFiles()">Clear</button>
            </div>
            <div v-if="uploaderStore.files.length > 0" class="flex flex-col h-full">
                <div class="flex w-full mb-2">
                    <span class="text-left w-1/2">Name</span>
                    <span class="hidden lg:inline w-1/4 text-right">Size</span>
                    <span class="w-1/2 lg:w-1/4 text-right"></span>
                </div>
                <div class="hline"></div>
                <div class="flex flex-col overflow-y-auto h-[480px]">
                    <div class="flex hover:bg-ctp-surface0 mt-1 mb-1" v-for="(item, index) in uploaderStore.files">
                        <div class="w-3/5 lg:w-1/2 flex items-center text-ellipsis whitespace-nowrap overflow-hidden">
                            <Tooltip :text="item.content.name">
                                <span class="pl-2">{{ item.content.name }}</span>
                            </Tooltip>
                        </div>
                        <div class="hidden lg:flex w-1/4 items-center justify-end">
                            <span>{{ filesize(item.content.size) }}</span>
                        </div>
                        <div class="w-2/5 lg:w-1/4 flex items-center justify-end pr-4">
                            <Tooltip :text="'Stop'" v-if="item.status === 'transfer'">
                                <button class="button" @click="item.cancel()">
                                    {{ Math.round(item.progress * 100) }}%
                                </button>
                            </Tooltip>
                            <button class="button" v-if="item.status === 'success'">
                                <IconAccept class="stroke-ctp-green" />
                            </button>
                            <Tooltip :text="item.error" v-if="item.status === 'fail'">
                                <button class="button" @click="uploaderStore.uploadFile(item)">
                                    <IconUpload class="stroke-ctp-red" />
                                </button>
                            </Tooltip>
                            <Tooltip :text="'Upload'" v-if="item.status === 'idle'">
                                <button class="button" @click="uploaderStore.uploadFile(item)">
                                    <IconUpload class="stroke-ctp-blue" />
                                </button>
                            </Tooltip>

                            <Tooltip :text="'Remove'">
                                <button class="button ml-2" @click="uploaderStore.removeFile(item)">
                                    <IconDelete class="stroke-ctp-peach" />
                                </button>
                            </Tooltip>
                        </div>
                    </div>
                </div>
                <div class="hline"></div>
            </div>
        </template>
    </Modal>
</template>
