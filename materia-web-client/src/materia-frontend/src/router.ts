import { createRouter, createWebHistory } from "vue-router";

import { user } from "@/api";
import { useUserStore } from "@/stores";


async function check_authorized(): Promise<boolean> {
    const userStore = useUserStore();

    // TODO: add timer
    return await user.current()
        .then(async user => { userStore.current = user; })
        .then(async () => {
            if (userStore.current.avatar?.length) {
                await user.get_avatar(userStore.current.avatar)
                    .then(async avatar => { userStore.avatar = avatar; })
            }
        })
        .then(async () => { return true; })
        .catch(() => {
            return false;
        });
}

async function bypass_auth(to: any, from: any) {
    if (await check_authorized() && (to.name === "signin" || to.name === "signup")) {
        return from;
    }
}

async function required_auth(to: any, from: any) {
    if (!await check_authorized()) {
        return { name: "signin" };
    }
}

async function required_admin(to: any, from: any) {
    const userStore = useUserStore();
    return userStore.current.is_admin;
}

const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/", name: "home", beforeEnter: [bypass_auth],
            component: () => import("@/views/Home.vue"),
        },
        {
            path: "/user/login", name: "signin", beforeEnter: [bypass_auth],
            component: () => import("@/views/user/SignIn.vue")
        },
        {
            path: "/user/register", name: "signup", //beforeEnter: [bypass_auth],
            component: () => import("@/views/user/SignUp.vue")
        },
        {
            path: "/user/preferencies", name: "prefs", redirect: { name: "prefs-profile" }, beforeEnter: [required_auth],
            component: () => import("@/views/user/Preferencies.vue"),
            children: [
                {
                    path: "profile", name: "prefs-profile", beforeEnter: [required_auth],
                    component: () => import("@/views/user/preferencies/Profile.vue")
                },
                {
                    path: "account", name: "prefs-account", beforeEnter: [required_auth],
                    component: () => import("@/views/user/preferencies/Account.vue")
                },
            ]
        },
        {
            path: "/:user", name: "profile", beforeEnter: [bypass_auth],
            component: () => import("@/views/user/Profile.vue")
        },
        {
            path: "/admin/settings", name: "settings", beforeEnter: [required_auth, required_admin],
            component: () => import("@/views/admin/Settings.vue")
        },
        {
            path: "/:pathMatch(.*)*", name: "not-found", beforeEnter: [bypass_auth],
            component: () => import("@/views/error/NotFound.vue")
        }
    ]
});

export default router;
