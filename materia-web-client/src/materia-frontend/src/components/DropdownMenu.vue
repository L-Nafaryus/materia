<script setup lang="ts">
import { ref } from "vue";

const active = ref<bool>(false);

function activate() {
    active.value = !active.value;
}

function deactivate() {
    active.value = false;
}
</script>

<template>
    <div @click="activate" v-click-outside="deactivate">
        <slot name="button"></slot>
        <div v-if="active">
            <slot name="content"></slot>
        </div>
    </div>
</template>
