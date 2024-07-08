import { resources_client, type ResponseError, handle_error } from "@/client";


export type Image = string | ArrayBuffer;

export async function avatars(avatar_id: string, format?: string): Promise<Image | null | ResponseError> {
    return await resources_client.get("/avatars/".concat(avatar_id), { params: { format: format ? format : "png" }})
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
