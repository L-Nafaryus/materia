<script setup lang="ts">
import IconDirectory from "@/components/icons/IconDirectory.vue";
import IconFile from "@/components/icons/IconFile.vue";
import ContextMenu from "@/components/ContextMenu.vue";
import CtxMenu from "@/components/CtxMenu.vue";
import Modal from "@/components/Modal.vue";
import { defineProps, ref, defineModel } from "vue";
import { filesize } from "filesize";
import { store, router, api } from "@";
import { useRoute } from "vue-router"

const repoStore = store.useRepository();
const route = useRoute();

const actions = [
    {
        label: "Copy",
        show: () => true,
        event: (data) => { repoStore.copyBufferSelected(); }
    },
    {
        label: "Paste",
        show: () => true,
        event: async (data) => { await repoStore.copyItems(repoStore.buffer, repoStore.currentPath); }
    },
    {
        label: "Move",
        show: () => true,
        event: async (data) => { await repoStore.moveItems(repoStore.buffer, repoStore.currentPath); }
    },
    {
        label: "Delete",
        show: () => true,
        event: async (data) => { await repoStore.deleteItem(data); }
    },
    {
        label: "Delete selected",
        show: () => { return repoStore.content.filter((item) => item.meta.selected).length > 1; },
        event: async (data) => { await repoStore.deleteSelectedItems(); }
    },
];

// Properties
const data = defineModel()
const { onDragOver, onDragLeave, onDrop } = defineProps(["onDragOver", "onDragLeave", "onDrop"]);

// Drag and drop
const onDragOverEvent = (event, value) => {
    event.preventDefault();
    console.log("drag over", JSON.stringify(value));

    if (value.type === "directory") {
        value.meta.dragOvered = true;
    }

    if (onDragOver) {
        onDragOver(event);
    }
};

const onDragLeaveEvent = (event, value) => {
    event.preventDefault();
    console.log("drag leave", JSON.stringify(value));

    if (value.type === "directory") {
        value.meta.dragOvered = false;
    }

};

const onDragBegin = (event, value) => {
    value.meta.selected = true;

    let items = repoStore.content.filter((item) => item.meta.selected);

    let elem = document.createElement("div");
    elem.id = "dragItem";
    elem.className = "min-w-16 h-8 absolute top-[-1000px] bg-ctp-mantle border rounded border-ctp-surface0 px-4 py-1";
    elem.appendChild(document.createTextNode("Move " + items.length + " items"));
    document.body.appendChild(elem);

    event.dataTransfer.setDragImage(elem, 0, 0);
    event.dataTransfer.setData("value", JSON.stringify(items));
};

const onDragEnd = (event) => {
    let elem = document.getElementById("dragItem");
    if (elem.parentNode) {
        elem.parentNode.removeChild(elem);
    }
    deselectAll();
};

const onDropEvent = async (event, item) => {
    if (item.type === "directory") {
        item.meta.dragOvered = false;
        let items = JSON.parse(event.dataTransfer.getData("value"));

        await repoStore.moveItems(items, item.info.path);
    }
    console.log("drop data", JSON.parse(event.dataTransfer.getData("value")));
};

const isDraggable = ref(false);

// Selection
const deselectAll = () => {
    console.log("deselect", data.value);
    for (let item of data.value) {
        item.meta.selected = false;
    }
};

const selectAll = (event) => {
    console.log("select all", event);
    for (let item of data.value) {
        item.meta.selected = true;
    }
};

const onSingleClick = (event: Event, item) => {
    console.log(event);
    if (!event.ctrlKey) {
        deselectAll();
    }
    if (event.shiftKey) {
        selectAll();
    } else {
        item.meta.selected = !item.meta.selected;
    }
};

const onDoubleClick = (item) => {
    if (item.type === "directory") {
        repoStore.changeDirectory(route.path, item.info);
    }
};

const onClickEvent = (event: Event, item) => {
    item.meta.clickCount++;
    if (item.meta.clickCount === 1) {
        onSingleClick(event, item);

        item.meta.clickTimer = setTimeout(() => {
            item.meta.clickCount = 0;
        }, 300);
    } else {
        onDoubleClick(item);
        clearTimeout(item.meta.clickTimer);
        item.meta.clickCount = 0;
    }
};

const onCtrlClickEvent = (event: Event, item) => {
    //console.log("ctrl click", event);
    //item.meta.selected = !item.meta.selected;
};

// TODO: ctrl+a select all, ctrl-left-mouse select one more item, shift-left-mouse select range of items

// Misc

function timeAgo(timestamp: number) {
    const seconds = Math.floor((new Date().getTime() - new Date(timestamp * 1000).getTime()) / 1000)
    let interval = seconds / 31536000
    const rtf = new Intl.RelativeTimeFormat("en", { numeric: 'auto' })
    if (interval > 1) { return rtf.format(-Math.floor(interval), 'year') }
    interval = seconds / 2592000
    if (interval > 1) { return rtf.format(-Math.floor(interval), 'month') }
    interval = seconds / 86400
    if (interval > 1) { return rtf.format(-Math.floor(interval), 'day') }
    interval = seconds / 3600
    if (interval > 1) { return rtf.format(-Math.floor(interval), 'hour') }
    interval = seconds / 60
    if (interval > 1) { return rtf.format(-Math.floor(interval), 'minute') }
    return rtf.format(-Math.floor(interval), 'second')
}

</script>

<template>
    <div class="flex flex-col h-full border-y lg:border rounded border-ctp-surface0 select-none my-2"
        @contextmenu.prevent>
        <div class="flex w-full py-2 px-4">
            <span class="text-left w-1/2">Name</span>
            <span class="hidden lg:inline w-1/4 text-right">Size</span>
            <span class="w-1/2 lg:w-1/4 text-right">Created</span>
        </div>
        <div class="hline"></div>
        <div class="flex flex-col overflow-y-auto" v-click-outside="deselectAll">
            <div class="flex hover:bg-ctp-surface0 py-2 px-4" v-if="!repoStore.isRoot()"
                @click="repoStore.previousDirectory(route.path)">
                <div class="w-3/5 lg:w-1/2 flex items-center">
                    <IconDirectory />

                    <span class="ml-4 text-ellipsis whitespace-nowrap overflow-auto">
                        ..
                    </span>
                </div>
                <div class="hidden lg:flex w-1/4 items-center justify-end">
                    <span>-</span>
                </div>
                <div class="w-2/5 lg:w-1/4 flex items-center justify-end">
                    <span>-</span>
                </div>
            </div>

            <div class="flex hover:bg-ctp-surface0 py-2 px-4"
                v-if="repoStore.isRoot() && repoStore.content.length === 0">
                <div class="flex items-center ml-auto mr-auto">
                    Empty
                </div>
            </div>

            <div class="flex hover:bg-ctp-surface1 py-2 px-4" v-for="(item, index) in repoStore.content"
                :class="{ 'bg-ctp-surface0': item.meta.selected, 'bg-ctp-lavender': item.meta.dragOvered }"
                @click="onClickEvent($event, item)" @keypress.ctrl.65="selectAll" draggable="true"
                @dragstart="onDragBegin($event, item)" @dragover="onDragOverEvent($event, item)"
                @dragend="onDragEnd($event)" @dragleave="onDragLeaveEvent($event, item)"
                @drop="onDropEvent($event, item)">
                <CtxMenu :data="item" :actions="actions" @onEvent="onSingleClick($event, item)">
                    <div class="w-3/5 lg:w-1/2 flex items-center">
                        <IconDirectory v-if="item.type == 'directory'" />
                        <IconFile v-else />

                        <span class="ml-4 text-ellipsis whitespace-nowrap overflow-hidden">
                            {{ item.info.name }}
                        </span>
                    </div>
                    <div class="hidden lg:flex w-1/4 items-center justify-end">
                        <span v-if="item.type == 'directory'">-</span>
                        <span v-else>{{ filesize(item.info.size) }}</span>
                    </div>
                    <div class="w-2/5 lg:w-1/4 flex items-center justify-end">
                        <span>{{ timeAgo(item.info.created) }}</span>
                    </div>
                </CtxMenu>
            </div>
        </div>
    </div>

</template>
