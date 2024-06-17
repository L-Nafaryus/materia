import { client, upload_client, resources_client, type ResponseError, handle_error } from "@/api/client";

export interface UserCredentials {
    name: string,
    password: string,
    email?: string
}

export async function signup(body: UserCredentials): Promise<null | ResponseError> {
    return await client.post("/auth/signup", JSON.stringify(body))
        .catch(handle_error);
}

export async function signin(body: UserCredentials): Promise<null | ResponseError> {
    return await client.post("/auth/signin", JSON.stringify(body))
        .catch(handle_error);
}

export type Image = string | ArrayBuffer;

export async function register(body: NewUser): Promise<User | ResponseError> {
    return await client.post("/user/register", JSON.stringify(body))
        .then(async response => { return Promise.resolve<User>(response.data); })
        .catch(handle_error);
}

export async function login(body: LoginUser): Promise<User | ResponseError> {
    return await client.post("/user/login", JSON.stringify(body))
        .then(async response => { return Promise.resolve<User>(response.data); })
        .catch(handle_error);
}

export async function remove(body: RemoveUser): Promise<null | ResponseError> {
    return await client.post("/user/remove", JSON.stringify(body))
        .then(async () => { return Promise.resolve(null); })
        .catch(handle_error);
}

export async function logout(): Promise<null | ResponseError> {
    return await client.get("/user/logout")
        .then(async () => { return Promise.resolve(null); })
        .catch(handle_error);
}

export async function current(): Promise<User | ResponseError> {
    return await client.get("/user/current")
        .then(async response => { return Promise.resolve<User>(response.data); })
        .catch(handle_error);
}

export async function avatar(file: FormData, progress?: any): Promise<null | ResponseError> {
    return await upload_client.post("/user/avatar", file, {
        onUploadProgress: progress ?? null,
        //headers: { "Accept-Encoding": "gzip" }
    })
        .then(async () => { return Promise.resolve(null); })
        .catch(handle_error);
}

export async function get_avatar(avatar: string): Promise<Image | null | ResponseError> {
    return await resources_client.get("/avatars/".concat(avatar))
        .then(async response => {
            return new Promise<Image | null>((resolve, reject) => {
                let reader = new FileReader();

                reader.onload = () => {
                    resolve(reader.result);
                };
                reader.onerror = (e) => {
                    reject(e);
                };
                reader.readAsDataURL(response.data);
            })
        })
        .catch(handle_error);
}

export async function profile(login: string): Promise<User | ResponseError> {
    return await client.get("/user/".concat(login))
        .then(async response => { return Promise.resolve<User>(response.data); })
        .catch(handle_error);
}
