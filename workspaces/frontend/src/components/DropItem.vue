<script setup lang="ts">
import { defineProps } from "vue";

const { onDragOver, onDragLeave, onDrop } = defineProps(["onDragOver", "onDragLeave", "onDrop"]);

const onDragOverEvent = (event) => {
    event.preventDefault();
    if (onDragOver) {
        onDragOver(event);
    }
};
</script>

<template>
    <tr @dragover="onDragOverEvent" @dragleave="onDragLeave" @drop="onDrop">
        <slot />
    </tr>
</template>
