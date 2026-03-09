import { useQuery } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import { WebApi, type Configuracion } from "../api";
import { webConfig } from "../config";

interface TokenPayload {
    usuario_id: number;
    empresa_id: number;
    sub: string;
}

export function Home(){
    const obtenerDataToken = () => {
        const token = localStorage.getItem('accessToken');
        if (!token) return { usuario: null, empresa: null, sub: null};
        try {
            const decoded = jwtDecode<TokenPayload>(token)
            return {
                usuario: decoded.usuario_id || null,
                empresa: decoded.empresa_id || null,
                sub: decoded.sub || null
            };
        } catch {
            return { usuario: null, empresa: null, sub: null};
        }
    }

    const dataInicial = obtenerDataToken()

    const usuarioId : number | null = dataInicial.usuario
    const empresa : number | null = dataInicial.empresa
    const usuario : string | null = dataInicial.sub

    const { data: configuracion, isLoading: configLoading} = useQuery<Configuracion | null>({
        queryKey: ['configuracion'],
        queryFn: async () => {
            const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);
            const response = await api.obtenerConfiguracion({
                getConfiguracionRequest:{
                    usuario_id: usuarioId!
                }
            })
            return response.data
        },
        enabled: !!usuarioId,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        refetchOnMount: false,
    })

    return(
        <>
            {configLoading ? (
                <div className="flex justify-center p-10">
                    <span>Cargando configuración...</span>
                </div>
            ) : (
                <>
                    <h2 className="text-xl font-bold mb-4">
                        Hola Mundo! Bienvenido {usuario} para la empresa {empresa} con el identificador {usuarioId}
                    </h2>

                    {!configuracion ? (
                        <div className="bg-amber-100 text-amber-800 p-4 rounded-md border border-amber-200">
                            <strong>Aviso:</strong> Necesitas configurar la aplicación antes de seguir.
                        </div>
                    ) : (
                        <div className="mt-4 p-4 bg-gray-50 rounded-md border">
                            <p><strong>Configuración actual:</strong></p>
                            <pre className="text-sm">{JSON.stringify(configuracion, null, 2)}</pre>
                        </div>
                    )}
                </>
            )}
        </>
    )
}

export default Home