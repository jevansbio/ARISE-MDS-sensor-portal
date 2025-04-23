declare module '@/utils/FetchFunctions' {
    export interface ApiResponse<T = unknown> {
        ok: boolean;
        data?: T;
        error?: string;
    }

    export function getData<T = unknown>(url: string, token: string): Promise<ApiResponse<T>>;
    export function postData<T = unknown>(url: string, token: string, data: unknown): Promise<ApiResponse<T>>;
    export function patchData<T = unknown>(url: string, token: string, data: unknown): Promise<ApiResponse<T>>;
    export function deleteData<T = unknown>(url: string, token: string): Promise<ApiResponse<T>>;
}
  