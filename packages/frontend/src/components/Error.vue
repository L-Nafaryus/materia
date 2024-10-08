<script setup lang="ts">
import { computed } from "vue";
const { value } = defineProps(["value"]);

const handleError = (e) => {
    let entries = [];
    let titlecase = (str: string) => {
        if (!str) return str;
        return str.charAt(0).toUpperCase() + str.slice(1);
    };

    if (e?.response) {
        if (e.response.status == 422) {
            for (let detail of e.response.data.detail) {
                entries.push(titlecase(detail.msg));
            }
        } else {
            if (e.response.data?.detail) {
                entries.push(e.response.data.detail);
            } else {
                entries.push(e.response.data);
            }
        }
    } else {
        entries.push(e);
    }

    return entries;
};

</script>

<template>
    <section v-if="value" class="mt-1 mb-1">
        <p v-for="entry in handleError(value)"
            class="text-center pt-3 pb-3 bg-ctp-red/25 rounded border border-ctp-red text-ctp-red">
            {{ entry }}
        </p>
    </section>
</template>
