import axios from 'axios'

const baseUrl = import.meta.env.VITE_API_EXPRESS || "http://localhost:3000";

console.log(baseUrl)

const api_express = axios.create({
    baseUrl,
    headers: {
        "Content-Type": "application/json",
    },
    timeout: 10000,
});

export default api_express