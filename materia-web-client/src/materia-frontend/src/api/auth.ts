import { client, type ResponseError, handle_error } from "@/api/client";

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


export async function signout(): Promise<null | ResponseError> {
    return await client.post("/auth/signout")
        .catch(handle_error);
}
