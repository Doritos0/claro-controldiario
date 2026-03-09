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

    const { data: configuracion } = useQuery<Configuracion | null>({
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
            <h2>
                Hola Mundo! Bienvenido {usuario} para la empresa {empresa} con el identificador {usuarioId}
            </h2>

            {/* Lógica condicional para la configuración */}
            {!configuracion ? (
                <div style={{ backgroundColor: '#fff3cd', padding: '10px', borderRadius: '5px' }}>
                    <strong>Aviso:</strong> Necesitas configurar la aplicación antes de seguir.
                </div>
            ) : (
                <p>
                    <strong>Configuración actual:</strong> {JSON.stringify(configuracion)}
                </p>
            )}
        </>
    )
}

export default Home