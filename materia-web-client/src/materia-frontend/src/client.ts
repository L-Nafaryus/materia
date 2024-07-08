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
    status: number | null,
    message: string | null
}

export function handle_error(error: AxiosError): Promise<ResponseError> {
    let message = error.response?.data?.detail || error.response?.data;
    console.log(error);
    // extract pydantic error message
    if (error.response.status == 422) {
        message = error.response?.data?.detail[1].ctx.reason;
    }

    return Promise.reject<ResponseError>({ status: error.response.status, message: message});
}

const debug = import.meta.hot;

export const api_client: AxiosInstance = axios.create({
    baseURL: debug ? "http://localhost:54601/api" : "/api",
    headers: {
        "Content-Type": "application/json"
    },
    withCredentials: true,
});

export const resources_client: AxiosInstance = axios.create({
    baseURL: debug ? "http://localhost:54601/resources" : "/resources",
    responseType: "blob"
});

