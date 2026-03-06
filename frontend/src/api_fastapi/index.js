import api_python from "./axios";

const endpoints = {
    control_diario: {
        ejecutar: (data) => api_python.post("/ejecutar", data),
    },
}

export default endpoints