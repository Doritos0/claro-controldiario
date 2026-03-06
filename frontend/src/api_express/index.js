import api_express from "./axios";

const endpoints = {
    descarga: {
        descarga_imagenes: (data) => api_express.post("/descargar/", data),
    },
};

export default endpoints;