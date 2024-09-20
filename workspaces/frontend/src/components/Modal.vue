<script setup lang="ts">
import { defineProps, defineEmits, ref } from "vue";

const props = defineProps({
    isOpen: Boolean,
});

const emit = defineEmits(["close-modal"]);

const closeModal = (action) => {
    emit("close-modal", action);
};

</script>

<template>
    <div v-if="isOpen" class="modal-mask">
        <div class="modal-wrapper">
            <div class="modal-container">
                <div class="flex mb-4">
                    <slot name="header"></slot>
                    <button class="mr-0 ml-auto button" @click="closeModal">x</button>
                </div>
                <div>
                    <slot name="content"></slot>
                </div>
                <div class="flex mt-4">
                    <slot name="footer"></slot>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.modal-mask {
    @apply fixed z-[666] top-0 left-0 w-full h-full;
    @apply bg-ctp-crust bg-opacity-50;
}

.modal-wrapper {}

.modal-container {
    @apply flex-grow w-full lg:w-[calc(100%-100px)] max-w-[1000px] ml-auto mr-auto lg:mt-20 lg:mb-20 p-5;
    @apply bg-ctp-crust shadow-ctp-overlay0 border rounded border-ctp-surface1 text-ctp-text;
    @apply h-screen lg:h-full;
}
</style>
