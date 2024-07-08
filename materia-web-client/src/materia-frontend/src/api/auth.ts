import { api_client, type ResponseError, handle_error } from "@/client";

export interface UserCredentials {
    name: string,
    password: string,
    email?: string
}

export async function signup(body: UserCredentials): Promise<null | ResponseError> {
    return await api_client.post("/auth/signup", JSON.stringify(body))
        .catch(handle_error);
}

export async function signin(body: UserCredentials): Promise<null | ResponseError> {
    return await api_client.post("/auth/signin", JSON.stringify(body))
        .catch(handle_error);
}

export async function signout(): Promise<null | ResponseError> {
    return await api_client.get("/auth/signout")
        .catch(handle_error);
}
