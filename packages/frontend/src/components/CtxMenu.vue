<script setup lang="ts">
import { ref } from "vue";

const { data, actions } = defineProps(["data", "actions"]);
const isShow = ref(false);
const posX = ref(0);
const posY = ref(0);
const anchor = ref(null);

const emit = defineEmits(["onEvent"]);

const showMenu = (event) => {
    event.preventDefault();
    console.log("pos", event);
    posX.value = event.pageX;
    posY.value = event.pageY;
    isShow.value = true;

    emit("onEvent", event);
};

const closeMenu = () => {
    isShow.value = false;
};
</script>

<template>
    <div ref="anchor" @contextmenu="showMenu($event)" style="display: contents" v-click-outside="closeMenu">
        <slot></slot>
    </div>
    <div v-if="isShow" class="absolute z-50 min-w-40 bg-ctp-mantle border rounded border-ctp-surface0"
        :style="{ top: posY + 'px', left: posX + 'px' }">
        <div v-for="action in actions" v-show="action.show()" :key="action.event" @click="action.event(data)"
            class="hover:bg-ctp-base text-ctp-blue select-none pl-4 pr-4 pt-2 pb-2">
            {{ action.label }}
        </div>
    </div>
</template>
