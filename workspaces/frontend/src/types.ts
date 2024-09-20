import { api_types } from "@";
import { CancelToken } from "axios";

export type Error = object;

export type RepositoryItemMeta = {
    selected: bool;
    clickCount: number;
    clickTimer: (object | null);
};

export type RepositoryItemType = "directory" | "file";

export type RepositoryItemInfo = {
    info: (api_types.DirectoryInfo | api_types.FileInfo);
    meta: RepositoryItemMeta;
    type: RepositoryItemType;
};

export type RepositoryContent = RepositoryItemInfo[];

export type UploadFileStatus = "success" | "fail" | "transfer" | "idle";

export type UploadFile = {
    content: File;
    status: UploadFileStatus;
    progress: number;
    cancel: CancelToken | null;
    error: string | null;
};
