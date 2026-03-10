import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import { WebApi, type Configuracion } from "../api";
import { webConfig } from "../config";
import React, { useEffect, useState } from "react";
import { DefaultApi } from "../node";
import { useNavigate } from 'react-router-dom';

interface TokenPayload {
    usuario_id: number;
    empresa_id: number;
    sub: string;
}

export function Home(){
    const queryClient = useQueryClient();
    const navigate = useNavigate();
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
    const [fechaReporte, setFechaReporte] = useState<Date | null>(null)
    // Solo guardaremos el contenido de los objetos de respuesta
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [resultadoReporte, setResultadoReporte] = useState<{ node: any; fastapi: any } | null>(null);
    const [imagenReporte, setImagenReporte] = useState<string | null>(null);

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
        console.log("Se consulta!")
        const response = await apiNode.obtenerEstadoSesionWhatsapp();
        return response.data;
    },
    refetchInterval: (query) => {
        const data = query.state.data;
        return data?.ready ? false : 4000;
    },
    refetchOnWindowFocus: false,
    });

    const handleLogout = () => {
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        console.log("Tokens Eliminados")
        
        navigate('/login', { replace: true });
    }

    const handleReport = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!fechaReporte) return;
        if (!configuracion?.grupo_wsp) return;

        console.log("Se descarga imagenes");
        console.log(configuracion.grupo_wsp)
        console.log(formatFechaSlash(fechaReporte));
        console.log(formatFechaGuion(fechaReporte));

        const responseNode = await apiNode.descargarFotos({
            descargarFotosRequest: {
                nombreGrupo: configuracion?.grupo_wsp,
                fecha: formatFechaSlash(fechaReporte)
            }
        })
        console.log(responseNode.data)

        const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON)
        const responseFast = await api.ejecutarReporteDiario(
            {
                ejecutarRequest: {
                    fecha_objetivo: formatFechaGuion(fechaReporte)
                }
            },
            {
                responseType: "blob"
            }
        )
        console.log(responseFast.data)
        const imageBlob = responseFast.data;
        const imageUrl = URL.createObjectURL(imageBlob);
        setImagenReporte(imageUrl);
        setResultadoReporte({
            node: responseNode.data,     // Aquí capturas el return de Node
            fastapi: responseFast.data   // Aquí capturas el return de FastAPI
        });
    }

    const formatFechaSlash = (date: Date) => {
        const day = String(date.getDate()).padStart(2, "0");
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const year = date.getFullYear();

        return `${day}/${month}/${year}`;
    };

    const formatFechaGuion = (date: Date) => {
        const day = String(date.getDate()).padStart(2, "0");
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const year = date.getFullYear();

        return `${day}-${month}-${year}`;
    };

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
                <div className="space-y-6 p-4">
                    <div className="flex items-center justify-between p-4">
                        <h2 className="text-xl font-bold mb-4">
                            Bienvenido {usuario}! | Empresa {empresa}
                        </h2>

                        <button
                            onClick={handleLogout}   
                            className="px-4 py-2 rounded-lg bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition"
                        >
                            Cerrar sesión
                        </button>
                    </div>

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
                            {wspData?.ready ? (
                                <>
                                <div className="mt-4 p-4 rounded-md border border-green-300 bg-green-100 text-green-800">
                                WhatsApp conectado correctamente
                                </div>
                                <div className="grid grid-cols-3 gap-4 mt-4 p-4 bg-rose-100 rounded-md border">
                                    <form className="space-y-6" onSubmit={handleReport}>
                                        <div className="bg-rose-200 text-black p-4">
                                            <label>Generar Reporte </label>
                                            <input
                                                type="date"
                                                value={fechaReporte ? fechaReporte.toISOString().split("T")[0] : ""}
                                                onChange={(e) => {
                                                    const value = e.target.value;

                                                    if (!value) {
                                                    setFechaReporte(null);
                                                    return;
                                                    }

                                                    const [year, month, day] = value.split("-");
                                                    const date = new Date(Number(year), Number(month) - 1, Number(day));

                                                    setFechaReporte(date);
                                                }}
                                            className="mt-2 w-full max-w-xs rounded-xl border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 shadow-sm transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 focus:outline-none"
                                            />
                                        </div>
                                        <button
                                            type="submit"
                                            className="w-full bg-slate-500 hover:bg-slate-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-slate-200 transition duration-300 transform active:scale-95"
                                        >
                                            Descarga Imagenes (Por ahora luego reporte)
                                        </button>
                                        <p></p>
                                    </form>
                                </div>
                                </>
                            ) : wspData?.qr ? (
                                <>
                                <h3>Inicia en WhatsApp</h3>
                                <div className="border-4 border-indigo-500 p-2 rounded-lg inline-block">
                                <img
                                    src={wspData.qr}
                                    alt="WhatsApp QR Code"
                                    className="w-64 h-64"
                                />
                                <p>Estado Actual: {wspData.status}</p>
                                </div>
                                </>
                            ) : (
                                <p>Generando QR...</p>
                            )}
                        </div>
                        </>
                    )}
                
                </div>
                </>
            )}
            {resultadoReporte && (
                <div className="mt-6 space-y-4">
                    <div className="p-4 bg-white border-l-4 border-blue-500 rounded shadow-sm">
                        <h4 className="font-bold text-blue-700 mb-2">Respuesta Node (Descarga):</h4>
                        <pre className="text-xs bg-gray-50 p-2 overflow-auto max-h-40">
                            {JSON.stringify(resultadoReporte.node, null, 2)}
                        </pre>
                    </div>

                    <div className="p-4 bg-white border-l-4 border-green-500 rounded shadow-sm">
                        <h4 className="font-bold text-green-700 mb-2">Respuesta FastAPI (Reporte):</h4>
                        <pre className="text-xs bg-gray-50 p-2 overflow-auto">
                            {imagenReporte && (
                                <div className="mt-6 p-4 bg-white rounded border shadow-sm">
                                    <h4 className="font-bold mb-2">Imagen del reporte:</h4>
                                    <img
                                        src={imagenReporte}
                                        alt="Reporte generado"
                                        className="max-w-full rounded border"
                                    />
                                </div>
                            )}
                        </pre>
                    </div>
                    
                    <button 
                        onClick={() => setResultadoReporte(null)}
                        className="text-xs text-gray-400 hover:text-red-500 transition"
                    >
                        Limpiar consola de resultados
                    </button>
                </div>
            )}
        </>
    )
}

export default Home