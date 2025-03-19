declare module '@/utils/FetchFunctions' {
    export function getData(url: string, token: string): Promise<any>;
    export function postData(url: string, token: string, data: any): Promise<any>;
    export function patchData(url: string, token: string, data: any): Promise<any>;
    export function deleteData(url: string, token: string): Promise<any>;
  }
  