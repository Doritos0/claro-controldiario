import { Configuration } from "./api";

export const webConfig = {
    getApiConToken() {
        const basePath = import.meta.env.VITE_API_PYTHON;
        return new Configuration({
            basePath: basePath,
            accessToken: () => localStorage.getItem('accessToken') || ''
        })
    },

    getApiSinToken() {
        const basePath = import.meta.env.VITE_API_PYTHON;
        return new Configuration({
            basePath: basePath,
        });
    },

    getApiNode() {
        const basePath = import.meta.env.VITE_API_EXPRESS;
        return new Configuration({
            basePath: basePath,
        });
    }
}
