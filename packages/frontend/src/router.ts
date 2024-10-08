import { createRouter, createWebHistory, useRoute } from "vue-router";
import { store, api, schemas } from "@";


export const is_authorized = async (): Promise<boolean> => {
    const userStore = store.useUser();
    
    return await api.userInfo({ throwOnError: true })
        .then(async res => { userStore.info = res.data; })
        .then(async () => {
            if (!userStore.avatar && userStore.info.avatar) {
                await api.avatarAvatar(userStore.info.avatar)
                    .then(async res => { userStore.avatar = res.data; })
            }
        })
        .then(async () => { return true; })
        .catch(() => {
            userStore.clear();
            return false;
        });
};

const bypass_auth = async (to: any, from: any): any => {
    if (await is_authorized() && (to.name === "signin" || to.name === "signup")) {
        return from;
    }
};

const required_auth = async (to: any, from: any): any => {
    if (!await is_authorized()) {
        return { name: "signin", query: {redirect: to.path } };
    }
};

const required_admin = async (to: any, from: any): boolean => {
    const userStore = store.useUser();
    return userStore.current.is_admin;
};

export const check_auth = async () => {
    const route = useRoute();
    if (!await is_authorized()) {
        router.push({ name: "signin", query: {redirect: route.path} });
    }
};

export const router = createRouter({
    history: createWebHistory(),
    routes: [
        {
            path: "/", name: "home", beforeEnter: [bypass_auth],
            component: () => import("@/views/Home.vue"),
        },
        {
            path: "/auth/signin", name: "signin", beforeEnter: [bypass_auth],
            component: () => import("@/views/AuthSignIn.vue")
        },
        {
            path: "/auth/signup", name: "signup", beforeEnter: [bypass_auth],
            component: () => import("@/views/AuthSignUp.vue")
        },
        {
            path: "/user/preferencies", name: "prefs", redirect: { name: "prefs-profile" }, beforeEnter: [required_auth],
            component: () => import("@/views/UserPrefs.vue"),
            children: [
                {
                    path: "profile", name: "prefs-profile", beforeEnter: [required_auth],
                    component: () => import("@/views/UserPrefsProfile.vue")
                },
                {
                    path: "account", name: "prefs-account", beforeEnter: [required_auth],
                    component: () => import("@/views/UserPrefsAccount.vue")
                },
            ]
        },
        {
            path: "/:user/repository/:pathMatch(.*)*", name: "repository", beforeEnter: [required_auth],
            component: () => import("@/views/Repository.vue"),
        },
        {
            path: "/admin/settings", name: "settings", beforeEnter: [required_auth, required_admin],
            component: () => import("@/views/AdminSettings.vue")
        },
        {
            path: "/:pathMatch(.*)*", name: "not-found", beforeEnter: [bypass_auth],
            component: () => import("@/views/NotFound.vue")
        }
    ]
});

export default router;
