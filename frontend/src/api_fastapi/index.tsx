import api_python from "./axios";

const endpoints = {
    control_diario: {
        ejecutar: (empresa_id: number, fecha_objetivo?: string, consolidado?: string) => api_python.post("/ejecutar", {
            empresa_id,
            fecha_objetivo,
            consolidado
        }),
    },

    login: {
        entrar: (user: string, pass: string) =>
            api_python.post("/login", {
                user,
                password: pass
            })
    }
}

export default endpoints