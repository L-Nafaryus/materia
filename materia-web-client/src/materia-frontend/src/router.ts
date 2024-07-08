import { createRouter, createWebHistory } from "vue-router";

import { useUserStore } from "@/stores";
import { api, resources } from "@";

async function check_authorized(): Promise<boolean> {
    const userStore = useUserStore();

    return await api.user.info()
        .then(async user_info => { userStore.info = user_info; })
        .then(async () => {
            if (!userStore.avatar && userStore.info.avatar) {
                await resources.avatars(userStore.info.avatar)
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
            path: "/auth/signin", name: "signin", beforeEnter: [bypass_auth],
            component: () => import("@/views/auth/SignIn.vue")
        },
        {
            path: "/auth/signup", name: "signup", //beforeEnter: [bypass_auth],
            component: () => import("@/views/auth/SignUp.vue")
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
            path: "/:user/repository", name: "repository", beforeEnter: [required_auth],
            component: () => import("@/views/Repository.vue")
        },
        {
            path: "/admin/settings", name: "settings", beforeEnter: [required_auth, required_admin],
            component: () => import("@/views/admin/Settings.vue")
        },
        {
            path: "/:pathMatch(.*)*", name: "not-found", beforeEnter: [bypass_auth],
            component: () => import("@/views/NotFound.vue")
        }
    ]
});

export default router;
