import { Configuration } from "./api";

export const webConfig = {
    getApiConToken() {
        const basePath = import.meta.env.VITE_API_PYTHON;
        console.log(basePath)
        return new Configuration({
            basePath: basePath,
            accessToken: () => localStorage.getItem('accessToken') || ''
        })
    },

    getApiSinToken() {
        const basePath = import.meta.env.VITE_API_PYTHON;
        console.log(basePath)
        return new Configuration({
            basePath: basePath,
        });
    }
}