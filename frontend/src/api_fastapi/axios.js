import axios from 'axios'

const baseUrl = import.meta.env.VITE_API_PYTHON || "http://localhost:8001";

console.log("BASE URL ", baseUrl)

const api_python = axios.create({
    baseUrl,
    headers:{
        "Content-Type": "application/json",
    },
    timeout: 10000,
});

export default api_python