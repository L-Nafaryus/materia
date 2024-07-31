import { api_client, type ResponseError, handle_error } from "@/client";

export interface UserCredentials {
    name: string,
    password: string,
    email?: string
}

export interface UserInfo {
    id: string,
    name: string,
    lower_name: string,
    full_name?: string,
    email?: string,
    is_email_private: boolean,
    must_change_password: boolean,
    login_type: string,
    created: number,
    updated: number,
    last_login?: number,
    is_active: boolean,
    is_admin: boolean,
    avatar?: string 
}


export type Image = string | ArrayBuffer;

export async function info(): Promise<UserInfo | ResponseError> {
    return await api_client.get("/user")
        .then(async response => { return Promise.resolve<UserInfo>(response.data); })
        .catch(handle_error);
}


