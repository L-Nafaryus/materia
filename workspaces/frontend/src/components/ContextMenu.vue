<script setup lang="ts">
import { ref, defineProps, defineEmits } from 'vue';

const { actions, x, y } = defineProps(['actions', 'x', 'y']);
const emit = defineEmits(['action-clicked']);

const emitAction = (action) => {
    emit('action-clicked', action);
};
</script>

<template>
    <div class="absolute z-50 context-menu bg-ctp-mantle border rounded border-ctp-overlay0"
        :style="{ top: y + 'px', left: x + 'px' }">
        <div v-for="action in actions" :key="action.action" @click="emitAction(action.action)"
            class="hover:bg-ctp-base text-ctp-blue">
            {{ action.label }}
        </div>
    </div>
</template>

<style scoped>
.context-menu {
    position: absolute;
    box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
    min-width: 150px;
}

.context-menu div {
    padding: 10px;
    cursor: pointer;
}
</style>
