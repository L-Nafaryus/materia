<template>
    <div class="relative h-12 border-b border-b-zinc-500">
        <nav
            class="absolute w-full h-[calc(100%-1px)] flex justify-between items-center m-0 pl-3 pr-3 bg-gradient-to-t from-zinc-800 to-zinc-900">
            <div class="items-center m-0 flex">
                <slot name="left"></slot>
            </div>
            <div class="items-center m-0 flex">
                <slot name="right"></slot>
            </div>
        </nav>
    </div>
</template>
