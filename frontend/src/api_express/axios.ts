import axios from 'axios'

const baseURL = import.meta.env.VITE_API_EXPRESS || "http://localhost:3000";

console.log(baseURL)

const api_express = axios.create({
    baseURL,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 10000,
});

export default api_express