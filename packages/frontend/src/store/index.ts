import { defineStore } from "pinia";
import { ref, type Ref } from "vue";
import { useRoute } from "vue-router";
import axios, { CancelToken } from "axios";

import { schemas, types, api, router, check_auth } from "@";

export const useUser = defineStore("user", () => {
    const info: Ref<schemas.UserInfoSchema | null> = ref(null);
    const avatar: Ref<string | ArrayBuffer | null> = ref(null);
    const isAccessTokenAlive: Ref<boolean> = ref(false);
    const isRefreshTokenAlive: Ref<boolean> = ref(false);
    const _accessTokenTimer: object | null = ref(null);
    const _refreshTokenTimer: object | null = ref(null);
    const _route = useRoute();

    const clear = () => {
        info.value = null;
        avatar.value = null;
        isAccessTokenAlive.value = false;
        isRefreshTokenAlive.value = false;
        _accessTokenTimer.value = null;
        _refreshTokenTimer.value = null;
    };

    const refreshInfo = async (error?: Ref<object> | null = null) => {
        await api.userInfo()
        .then(async res => { 
            info.value = res.data; 

        })
        .then(async () => {
            if (!avatar.value && info.value.avatar) {
                await api.avatarAvatar(info.value.avatar)
                    .then(async res => { avatar.value = res.data; })
            }
        })
        .catch(err => {
            if (error) {
                error.value = err;
            }
        });
    };

    const isAuthorized = async (): boolean => {
        if (!isAccessTokenAlive.value) {
            await refreshInfo();
        }
        if (!info.value) {
            clear();
            return false;
        }
        return true;
    };

    const isAdmin = (): boolean | null => {
        return info.value?.is_admin;
    };

    const checkAuthorizationRedirect = async (path: string) => {
        if (!(await isAuthorized())) {
            router.push({ name: "signin", query: {redirect: path}});
        }
    };

    return { info, avatar, clear, refreshInfo, isAuthorized, isAdmin, checkAuthorizationRedirect };
});

export const useMisc = defineStore("misc", () => {
    // preferencies current tab
    const p_current_tab: Ref<number> = ref(0);

    return { p_current_tab };
});

export const useUploader = defineStore("uploader", () => {
    const files: Ref<types.UploadFile[]> = ref([]);
    const _repoStore = useRepository();

    const loadFiles = (event: Event) => {
        for (let file of event.target.files) {
            let uploadFile: types.UploadFile ={
                content: file,
                status: "idle",
                progress: 0
            };

            files.value.push(uploadFile);
        }
    };

    const removeFile = (item: types.UploadFile) => {
        item.status === "transfer" && item.cancel();

        const index = files.value.indexOf(item);
        files.value.splice(index, 1);
    };
    const removeFiles = () => {
        for (let file of files.value) {
            file.status === "transfer" && file.cancel();
        }
        files.value = [];
    };
    const _uploadFile = async (item: types.UploadFile) => {
        item.status = "transfer";

        await api.fileCreate({
            body: {
                file: item.content,
                path: "/"
            },
            throwOnError: true,
            onUploadProgress: (progressEvent) => {
                item.progress = progressEvent.progress;
            },
            cancelToken: new CancelToken((c) => {
                item.cancel = c;
            })
        })
            .then(async () => {
                item.status = "success";
                await _repoStore.refreshInfo();
            })
            .catch(err => {
                item.status = "fail";
                if (err.response?.data) {
                    item.error = err.response.data?.detail || err.response.data;
                }
            });
    };
    const uploadFile = async (item: types.UploadFile) => {
        await check_auth();
        await _uploadFile(item);
    };
    const uploadFiles = async () => {
        await check_auth();
        let promises = [];

        for (let item of files.value) {
            if (item.status === "idle" || item.status === "fail") {
                promises.push(_uploadFile(item));
            }
        }

        await axios.all(promises);
    };

    return { files, loadFiles, removeFile, removeFiles, uploadFile, uploadFiles };
});

export const useRepository = defineStore("repository", () => {
    const info: Ref<api_types.RepositoryInfo> = ref(null);
    const content: Ref<types.RepositoryContent> = ref([]);
    const isCreated: Ref<boolean> = ref(false);
    const currentPath: Ref<string> = ref("/");
    const buffer: Ref<types.RepositoryContent> = ref([]);

    const clear = () => {
        info.value = null;
        content.value = [];
        isCreated.value = false;
        currentPath.value = "/";
    };

    const refreshInfo = async (path: string | null = null, error?: Ref<object> | null) => {
        if (path) {
           currentPath.value = path;
        }

        await api.repositoryInfo({ throwOnError: true })
        .then(async res => {
            isCreated.value = true;
            info.value = res.data;
        })
        .then(async () => {
            await refreshContent(error);
        })
        .catch(err => {
            if (err.response.status === 404) {
                clear();
            }
            if (error) {
                error.value = err;
            }
        });
    };

    const _processContent = (_content: api_types.RepositoryContent | api_types.DirectoryContent) => {
        content.value = [];
        const item_meta: types.RepositoryItemMeta = {
            selected: false,
            clickCount: 0,
            clickTimer: null,
            dragOvered: false
        };

        for (let directory of _content.directories) {
            content.value.push({ info: directory, meta: { ...item_meta }, type: "directory" });
        }

        for (let file of _content.files) {
            content.value.push({ info: file, meta: { ...item_meta }, type: "file" });
        }

    };

    const refreshContent = async (error?: Ref<object> | null = null) => {
        let promise = null;

        if (isRoot()) {
            promise = api.repositoryContent({ throwOnError: true });
        } else {
            promise = api.directoryContent({ query: { path: currentPath.value }, throwOnError: true });
        }

        await promise.then(async res => {
            _processContent(res.data);
        })
        .catch(err => {
            if (error) {
                error.value = err;
            }
        });
    };

    const create = async () => {
        await api.repositoryCreate({ throwOnError: true })
        .catch(err => {
            if (error) {
                error.value = err;
            }
        });
    };

    const sizePercent = (): number => {
        return Math.round(info.value.used / info.value.capacity * 100);
    };

    const isRoot = (): boolean => {
        return currentPath.value === "/";
    };

    const changeDirectory = (current_path: string, directory: api_types.DirectoryInfo) => {
        router.push({ path: [current_path, directory.name].join("/") });
    };

    const previousDirectory = (current_path: string) => {
        let path = current_path.split("/");
        path.splice(path.length - 1, 1);
        router.push({ path: path.join("/") });
    };

    const makeDirectory = async (name: string, error?: Ref<object> | null = null) => {
        if (name === "") {
            return;
        }
        let path = currentPath.value;
        if (isRoot()) {
            path = path + name;
        } else {
            path = [path, name].join("/");
        }
        await api.directoryCreate({ body: { path: path }, throwOnError: true })
        .then(async () => {
            await refreshInfo(currentPath.value, error);
        })
        .catch(err => {
            if (error) {
                error.value = err;
            }
        });
    };

    const deleteItem = async (item: types.RepositoryItemInfo, error?: Ref<object> | null = null) => {
        let query = { query: { path: item.info.path }, throwOnError: true };
        let promise = null;

        if (item.type === "directory") {
            promise = api.directoryRemove(query);
        }
        if (item.type === "file") {
            promise = api.fileRemove(query);
        }

        await promise.then(async () => {
            await refreshInfo(null, error);
        })
            .catch(err => {
                if (error) {
                    error.value = err;
                }
            });
    };

    const deleteSelectedItems = async (error?: Ref<object> | null = null) => {
        let items = content.value.filter((item) => item.meta.selected);
        let promises = [];

        items.forEach((item) => {
            let query = { query: { path: item.info.path }, throwOnError: true };
            let callback = async () => {
                await refreshInfo(null, error);
            };
            if (item.type === "directory") {
                promises.push(api.directoryRemove(query).then(callback));
            }
            if (item.type === "file") {
                promises.push(api.fileRemove(query).then(callback));
            }
        });

        await axios.all(promises);
    };

    const moveItems = async (items: types.RepositoryContent, path: string, error?: Ref<object | null> = null) => {
        let promises = [];

        items.forEach((item) => {
            let query = { body: { path: item.info.path, target: path }, throwOnError: true };
            let callback = async () => {
                await refreshInfo(null, error);
            };
            if (item.type === "directory") {
                promises.push(api.directoryMove(query).then(callback));
            }
            if (item.type === "file") {
                promises.push(api.fileMove(query).then(callback));
            }
        });

        await axios.all(promises);
    };

    const copyBuffer = (items: types.RepositoryContent) => {
        buffer.value = items;
    };

    const copyBufferSelected = () => {
        let items = content.value.filter((item) => item.meta.selected);
        copyBuffer(items);
    };

    const copyItems = async (items: types.RepositoryContent, path: string, error?: Ref<object | null> = null) => {
        let promises = [];

        items.forEach((item) => {
            let query = { body: { path: item.info.path, target: path }, throwOnError: true };
            let callback = async () => {
                await refreshInfo(null, error);
            };
            if (item.type === "directory") {
                promises.push(api.directoryCopy(query).then(callback));
            }
            if (item.type === "file") {
                promises.push(api.fileCopy(query).then(callback));
            }
        });

        await axios.all(promises);
    };

    return { info, content, currentPath, buffer, isCreated, clear, refreshInfo, refreshContent, create, sizePercent, isRoot, changeDirectory, previousDirectory, makeDirectory, deleteItem, deleteSelectedItems, moveItems, copyBuffer, copyBufferSelected, copyItems };
});
