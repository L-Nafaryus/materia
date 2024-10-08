<script setup lang="ts">
import { defineProps } from "vue";

const { data } = defineProps(["data"]);

const onDragBeginEvent = (event) => {
    event.dataTransfer.setData("value", JSON.stringify(data));
};
</script>

<template>
    <tr draggable="true" @dragstart="onDragBeginEvent">
        <slot />
    </tr>
</template>
