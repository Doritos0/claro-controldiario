import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "./token-storage";

type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

const pythonBaseUrl = import.meta.env.VITE_API_PYTHON as string;
const nodeBaseUrl = import.meta.env.VITE_API_EXPRESS as string;

const pythonAxios = axios.create({
  baseURL: pythonBaseUrl,
});

const nodeAxios = axios.create({
  baseURL: nodeBaseUrl,
});

let isRefreshing = false;
let refreshQueue: Array<(token: string | null) => void> = [];

const flushRefreshQueue = (token: string | null) => {
  refreshQueue.forEach((cb) => cb(token));
  refreshQueue = [];
};

const isAuthEndpoint = (url?: string) => {
  if (!url) {
    return false;
  }
  return url.endsWith("/login") || url.endsWith("/refresh");
};

const setAuthHeader = (
  request: InternalAxiosRequestConfig,
  token: string,
) => {
  const headers = AxiosHeaders.from(request.headers);
  headers.set("Authorization", `Bearer ${token}`);
  request.headers = headers;
};

pythonAxios.interceptors.request.use((request) => {
  const accessToken = getAccessToken();
  if (!accessToken || isAuthEndpoint(request.url)) {
    return request;
  }

  setAuthHeader(request, accessToken);
  return request;
});

pythonAxios.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined;

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest._retry || isAuthEndpoint(originalRequest.url)) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearTokens();
      window.location.replace("/login");
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((token) => {
          if (!token) {
            reject(error);
            return;
          }
          setAuthHeader(originalRequest, token);
          resolve(pythonAxios(originalRequest));
        });
      });
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshResponse = await axios.post(`${pythonBaseUrl}/refresh`, {
        refresh_token: refreshToken,
      });

      const newAccessToken = refreshResponse.data?.access_token as string | undefined;
      const newRefreshToken = refreshResponse.data?.refresh_token as
        | string
        | null
        | undefined;

      if (!newAccessToken) {
        throw new Error("Refresh sin access token");
      }

      setTokens(newAccessToken, newRefreshToken);
      flushRefreshQueue(newAccessToken);
      setAuthHeader(originalRequest, newAccessToken);
      return pythonAxios(originalRequest);
    } catch (refreshError) {
      flushRefreshQueue(null);
      clearTokens();
      window.location.replace("/login");
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  },
);

export function getPythonAxios(): AxiosInstance {
  return pythonAxios;
}

export function getNodeAxios(): AxiosInstance {
  return nodeAxios;
}
