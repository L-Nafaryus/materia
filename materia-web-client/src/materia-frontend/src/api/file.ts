import { api_client, type ResponseError, handle_error } from "@/client";

export interface FileInfo {
    id: number,
    repository_id: number,
    parent_id?: number,
    created: number,
    updated: number,
    name: string,
    path?: string,
    is_public: boolean,
    size: number
}
