<script setup lang="ts">
import { ref } from "vue";

const { text } = defineProps(["text"]);
const isShow = ref(false);
const posX = ref(0);
const posY = ref(0);
const anchor = ref(null);

const showTooltip = (event, value) => {
    event.preventDefault();

    if (isShow.value)
        return;

    posX.value = anchor.value.getBoundingClientRect().left;
    posY.value = anchor.value.getBoundingClientRect().top;
    isShow.value = true;
};

const closeTooltip = () => {
    isShow.value = false;
};
</script>

<template>
    <div ref="anchor" @mouseover="showTooltip" @mouseleave="closeTooltip" style="display: unset">
        <slot></slot>
        <div class="tooltip" :style="{ top: posY + 32 + 'px', left: posX + 16 + 'px' }" v-if="isShow">
            {{
                text
            }}
        </div>
    </div>

</template>

<style>
.tooltip {
    @apply hidden sm:inline z-[666] absolute bg-ctp-mantle rounded p-2 border border-ctp-surface0 max-w-[600px];
    overflow-wrap: break-all;
    word-break: break-all;
    white-space: pre-wrap;
}
</style>
