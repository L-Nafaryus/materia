import axios, { type AxiosInstance, AxiosError } from "axios";

export class HttpError extends Error {
    status_code: number;

    constructor(status_code: number, message: string) {
        super(JSON.stringify({ status_code: status_code, message: message }));
        Object.setPrototypeOf(this, new.target.prototype);

        this.name = Error.name;
        this.status_code = status_code;
    }
}

export interface ResponseError {
    status_code: number,
    message: string
}

export function handle_error(error: AxiosError): Promise<ResponseError> {
    return Promise.reject<ResponseError>({ status_code: error.response?.status, message: error.response?.data });
}

const debug = import.meta.hot;

export const client: AxiosInstance = axios.create({
    baseURL: debug ? "http://localhost:54601/api" : "/api",
    headers: {
        "Content-Type": "application/json"
    },
    withCredentials: true,
});

export const upload_client: AxiosInstance = axios.create({
    baseURL: debug ? "http://localhost:54601/api" : "/api",
    headers: {
        "Content-Type": "multipart/form-data"
    },
    withCredentials: true,
});

export const resources_client: AxiosInstance = axios.create({
    baseURL: debug ? "http://localhost:54601/resources" : "/resources",
    responseType: "blob"
});

export default client;
