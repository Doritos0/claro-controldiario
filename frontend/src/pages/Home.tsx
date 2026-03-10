import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import { WebApi, type Configuracion } from "../api";
import { webConfig } from "../config";
import React, { useEffect, useState } from "react";
import { DefaultApi } from "../node";

interface TokenPayload {
    usuario_id: number;
    empresa_id: number;
    sub: string;
}

export function Home(){
    const queryClient = useQueryClient();
    const apiNode = new DefaultApi(import.meta.env.VITE_API_EXPRESS)
    const iniciarSesion = useMutation({
        mutationFn: () => apiNode.iniciarSesionWhatsapp()
    })
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

    const [grupo, setGrupo] = useState<string>("")

    const { data: configuracion, isLoading: configLoading} = useQuery<Configuracion | null>({
        queryKey: ['configuracion'],
        queryFn: async () => {
            const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);
            const response = await api.obtenerConfiguracion()
            return response.data
        },
        enabled: !!usuarioId,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        refetchOnMount: false,
    })

    const handleConfig = async (e: React.FormEvent) => {
        e.preventDefault()
        try {
            const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON)
            const response = await api.agregarConfiguracion({
                postConfiguracionRequest: {
                    grupo_wsp: grupo
                }
            })

            console.log("Se envia formulario! con la siguiente informacion: ",response.data.grupo_wsp)
            queryClient.invalidateQueries({ queryKey: ['configuracion'] })
        } catch (error) {
            console.error("Error al guardar: ",error)
        }

    }

    const { data: wspData } = useQuery({
    queryKey: ['wspEstado'],
    queryFn: async () => {
        const response = await apiNode.obtenerEstadoSesionWhatsapp();
        return response.data;
    },
    refetchInterval: (query) => {
        const data = query.state.data;
        return data?.ready ? false : 2000;
    },
    refetchOnWindowFocus: false,
    });
    
    console.log(import.meta.env.VITE_API_EXPRESS)

    console.log(wspData)

    useEffect(() => {
        iniciarSesion.mutate()
    }, [])

    return(
        <>
            {configLoading ? (
                <div className="flex justify-center p-10">
                    <span>Cargando configuración...</span>
                </div>
            ) : (
                <>
                    <h2 className="text-xl font-bold mb-4">
                        Bienvenido {usuario}! | Empresa {empresa}
                    </h2>

                    {!configuracion ? (
                        <div className="bg-amber-100 text-amber-800 p-4 rounded-md border border-amber-200">
                            <strong>Aviso:</strong> No tienes configurado ningun grupo de WhatsApp, agrega el nombre del grupo donde se dejan las capturas de TikTok antes de continuar!
                        <form className="space-y-6" onSubmit={handleConfig}>
                            <div>
                                <label className="bloc text-sm font-medium text-gray-700 mb-1">Grupo WhatsApp</label>
                                <input
                                    type="text"
                                    value={grupo}
                                    onChange={(e) => setGrupo(e.target.value)}
                                    placeholder="Ej. CampañaDigital"
                                    className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
                                />
                            </div>
                            <button
                                type="submit"
                                className="w-full bg-slate-500 hover:bg-slate-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-slate-200 transition duration-300 transform active:scale-95"
                            >
                                Agregar
                            </button>
                        </form>
                        </div>
                    ) : (
                        <>
                        <div className="mt-4 p-4 bg-gray-50 rounded-md border">
                            <p><strong>Configuración actual:</strong></p>
                            <pre className="text-sm">{JSON.stringify(configuracion, null, 2)}</pre>
                        </div>
                        <div>
                            <h3>Inicia en WhatsApp</h3>

                            {wspData?.ready ? (
                                <div className="mt-4 p-4 rounded-md border border-green-300 bg-green-100 text-green-800">
                                WhatsApp conectado correctamente
                                </div>
                            ) : wspData?.qr ? (
                                <div className="border-4 border-indigo-500 p-2 rounded-lg inline-block">
                                <img
                                    src={wspData.qr}
                                    alt="WhatsApp QR Code"
                                    className="w-64 h-64"
                                />
                                </div>
                            ) : (
                                <p>Generando QR...</p>
                            )}
                        </div>
                        </>
                    )}
                </>
            )}
        </>
    )
}

export default Home