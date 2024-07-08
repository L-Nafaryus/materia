import { api_client, type ResponseError, handle_error } from "@/client";

export interface RepositoryInfo {
    id: number,
    capacity: number,
    used?: number 
}

export async function info(): Promise<RepositoryInfo | ResponseError> {
    return await api_client.get("/repository")
        .then(async response => { return Promise.resolve<RepositoryInfo>(response.data); })
        .catch(handle_error);
}

export async function create(): Promise<null | ResponseError> {
    return await api_client.post("/repository")
        .catch(handle_error);
}

export async function remove(): Promise<null | ResponseError> {
    return await api_client.delete("/repository")
        .catch(handle_error);
}
