<template>
    <div class="relative h-12">
        <nav
            class="absolute w-full h-full flex justify-between items-center m-0 pl-3 pr-3 bg-ctp-mantle">
            <div class="items-center m-0 flex">
                <slot name="left"></slot>
            </div>
            <div class="items-center m-0 flex">
                <slot name="right"></slot>
            </div>
        </nav>
    </div>
</template>
