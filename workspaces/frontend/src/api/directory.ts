import { api_client, type ResponseError, handle_error } from "@/client";

export interface DirectoryInfo {
    id: number,
    repository_id: number,
    parent_id?: number,
    created: number,
    updated: number,
    name: string,
    path?: string,
    is_public: boolean,
    used?: number
}
