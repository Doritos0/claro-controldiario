import axios from 'axios'

const baseURL = import.meta.env.VITE_API_PYTHON || "http://localhost:8001";

console.log("BASE URL ", baseURL)

const api = axios.create({
    baseURL,
    headers:{
        "Content-Type": "application/json",
    },
    timeout: 10000,
});

export default api