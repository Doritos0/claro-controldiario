import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { jwtDecode } from "jwt-decode";
import { WebApi, type Configuracion } from "../api";
import { webConfig } from "../config";
import React, { useEffect, useMemo, useState } from "react";
import { DefaultApi } from "../node";
import { Navigate, useNavigate } from "react-router-dom";

interface TokenPayload {
    usuario_id: number;
    empresa_id: number;
    sub: string;
}

interface EjecutivoGestion {
    id: number;
    nombre: string;
    estado: string;
    eps: string;
    nro_telefono: number;
}

export function Home() {
    const queryClient = useQueryClient();
    const navigate = useNavigate();
    const apiNode = new DefaultApi(webConfig.getApiNode(), import.meta.env.VITE_API_EXPRESS);
    const apiWeb = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);

    const obtenerDataToken = () => {
        const token = localStorage.getItem("accessToken");
        if (!token) return { usuario: null, empresa: null, sub: null };

        try {
            const decoded = jwtDecode<TokenPayload>(token);
            return {
                usuario: decoded.usuario_id || null,
                empresa: decoded.empresa_id || null,
                sub: decoded.sub || null,
            };
        } catch {
            return { usuario: null, empresa: null, sub: null };
        }
    };

    const dataInicial = useMemo(() => obtenerDataToken(), []);

    const usuarioId: number | null = dataInicial.usuario;
    const usuario: string | null = dataInicial.sub;

    const [grupo, setGrupo] = useState<string>("");
    const [grupoEdicion, setGrupoEdicion] = useState<string>("");
    const [showGrupoModal, setShowGrupoModal] = useState<boolean>(false);
    const [showEjecutivosModal, setShowEjecutivosModal] = useState<boolean>(false);
    const [fechaReporte, setFechaReporte] = useState<Date | null>(null);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [resultadoReporte, setResultadoReporte] = useState<{ node: any; fastapi: any } | null>(null);
    const [imagenReporte, setImagenReporte] = useState<string | null>(null);

    const [ejecutivos, setEjecutivos] = useState<EjecutivoGestion[]>([]);
    const [nuevoNombre, setNuevoNombre] = useState<string>("");
    const [nuevoEstado, setNuevoEstado] = useState<string>("ACTIVO");
    const [nuevoTelefono, setNuevoTelefono] = useState<string>("");

    const [editandoId, setEditandoId] = useState<number | null>(null);
    const [editEstado, setEditEstado] = useState<string>("ACTIVO");
    const [editTelefono, setEditTelefono] = useState<string>("");

    const iniciarSesion = useMutation({
        mutationFn: () => apiNode.iniciarSesionWhatsapp(),
    });

    const { data: configuracion, isLoading: configLoading } = useQuery<Configuracion | null>({
        queryKey: ["configuracion"],
        queryFn: async () => {
            const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);
            const response = await api.obtenerConfiguracion();
            return response.data;
        },
        enabled: !!usuarioId,
        refetchOnWindowFocus: false,
        refetchOnReconnect: false,
        refetchOnMount: false,
    });

    const { data: wspData } = useQuery({
        queryKey: ["wspEstado"],
        queryFn: async () => {
            const response = await apiNode.obtenerEstadoSesionWhatsapp();
            return response.data;
        },
        enabled: !!configuracion,
        refetchInterval: (query) => {
            const data = query.state.data;
            return data?.status === "ready" ? false : 4000;
        },
        refetchOnWindowFocus: false,
    });

    useEffect(() => {
        if (configuracion) {
            iniciarSesion.mutate();
            setGrupoEdicion(configuracion.grupo_wsp);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [configuracion]);

    const cargarEjecutivos = async () => {
        const response = await apiWeb.obtenerEjecutivos({
            getEjecutivosRequest: {
                incluir_elimados: false,
            },
        });

        if (!response) throw new Error("No se pudieron cargar ejecutivos");

        const data = response.data as EjecutivoGestion[];
        setEjecutivos(data);
    };

    const handleConfig = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);
            await api.agregarConfiguracion({
                postConfiguracionRequest: {
                    grupo_wsp: grupo,
                },
            });

            setGrupo("");
            queryClient.invalidateQueries({ queryKey: ["configuracion"] });
        } catch (error) {
            console.error("Error al guardar: ", error);
        }
    };

    const handleModificarGrupo = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await apiWeb.agregarConfiguracion({
                postConfiguracionRequest: {
                    grupo_wsp: grupoEdicion,
                },
            });

            if (!response) throw new Error("No se configuro el nuevo grupo");

            setShowGrupoModal(false);
            queryClient.invalidateQueries({ queryKey: ["configuracion"] });
        } catch (error) {
            console.error("Error al modificar grupo:", error);
        }
    };

    const handleAgregarEjecutivo = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const response = await apiWeb.crearEjecutivo({
                ejecutivoRest: {
                    nombre: nuevoNombre,
                    estado: nuevoEstado,
                    eps: "PHOENIX",
                    nro_telefono: Number(nuevoTelefono),
                },
            });

            if (!response) throw new Error("No se pudo crear el ejecutivo");

            setNuevoNombre("");
            setNuevoTelefono("");
            setNuevoEstado("ACTIVO");
            await cargarEjecutivos();
        } catch (error) {
            console.error("Error al crear ejecutivo:", error);
        }
    };

    const prepararEdicion = (ejecutivo: EjecutivoGestion) => {
        setEditandoId(ejecutivo.id);
        setEditEstado(ejecutivo.estado);
        setEditTelefono(String(ejecutivo.nro_telefono ?? ""));
    };

    const handleModificarEjecutivo = async (id: number, nombre: string) => {
        try {
            const response = await apiWeb.modificarEjecutivo({
                modificarEjecutivoRequest: {
                    ejecutivo_id: id,
                    nombre,
                    estado: editEstado,
                    nro_telefono: Number(editTelefono),
                },
            });

            if (!response) throw new Error("No se pudo modificar el ejecutivo");

            setEditandoId(null);
            await cargarEjecutivos();
        } catch (error) {
            console.error("Error al modificar ejecutivo:", error);
        }
    };

    const handleEliminarEjecutivo = async (id: number, nombre: string) => {
        const confirmacion = window.confirm(`¿Estás seguro que deseas eliminar a ${nombre}?`);
        if (!confirmacion) return;

        try {
            const response = await apiWeb.eliminarEjecutivo({
                eliminarEjecutivoRequest: {
                    ejecutivo_id: id,
                },
            });

            if (!response) throw new Error("No se pudo eliminar el ejecutivo");

            await cargarEjecutivos();
        } catch (error) {
            console.error("Error al eliminar ejecutivo:", error);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem("accessToken");
        localStorage.removeItem("refreshToken");
        navigate("/login", { replace: true });
    };

    const handleReport = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!fechaReporte) return;
        if (!configuracion?.grupo_wsp) return;

        const responseNode = await apiNode.descargarFotos({
            descargarFotosRequest: {
                nombreGrupo: configuracion.grupo_wsp,
                fecha: formatFechaSlash(fechaReporte),
            },
        });

        const api = new WebApi(webConfig.getApiConToken(), import.meta.env.VITE_API_PYTHON);
        const responseFast = await api.ejecutarReporteDiario(
            {
                ejecutarRequest: {
                    fecha_objetivo: formatFechaGuion(fechaReporte),
                },
            },
            {
                responseType: "blob",
            }
        );

        const imageBlob = responseFast.data;
        const imageUrl = URL.createObjectURL(imageBlob);
        setImagenReporte(imageUrl);
        setResultadoReporte({
            node: responseNode.data,
            fastapi: responseFast.data,
        });
    };

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

    if (!usuarioId) {
        return <Navigate to="/login" replace />;
    }

    return (
        <div className="min-h-screen bg-slate-100 text-slate-800">
            <header className="mx-auto flex w-full max-w-5xl items-center justify-between px-6 py-5">
                <h1 className="text-lg font-semibold">Bienvenido, {usuario}!</h1>
                <button
                    onClick={handleLogout}
                    className="rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white transition hover:bg-slate-800"
                >
                    Cerrar sesión
                </button>
            </header>

            <main className="mx-auto flex w-full max-w-5xl flex-col items-center px-4 pb-10 pt-2">
                {configLoading ? (
                    <div className="w-full max-w-xl rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm">
                        Cargando configuración...
                    </div>
                ) : !configuracion ? (
                    <section className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                        <h2 className="text-center text-xl font-semibold">Configura tu grupo de WhatsApp</h2>
                        <p className="mt-3 text-center text-sm text-slate-600">
                            Antes de continuar, agrega el nombre del grupo donde se publican las capturas de TikTok.
                        </p>

                        <form className="mt-6 space-y-4" onSubmit={handleConfig}>
                            <div>
                                <label className="mb-1 block text-sm font-medium text-slate-700">Grupo WhatsApp</label>
                                <input
                                    type="text"
                                    value={grupo}
                                    onChange={(e) => setGrupo(e.target.value)}
                                    placeholder="Ej. Campaña Digital"
                                    className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 focus:border-slate-500 focus:outline-none"
                                />
                            </div>
                            <button
                                type="submit"
                                className="w-full rounded-lg bg-slate-700 px-4 py-2 font-semibold text-white transition hover:bg-slate-800"
                            >
                                Guardar configuración
                            </button>
                        </form>
                    </section>
                ) : (
                    <>
                        <div className="mb-4 flex w-full max-w-xl gap-3">
                            <button
                                onClick={async () => {
                                    setShowEjecutivosModal(true);
                                    await cargarEjecutivos();
                                }}
                                className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
                            >
                                Gestionar ejecutivos
                            </button>
                        </div>

                        <section className="w-full max-w-xl space-y-5 rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                            <div className="flex items-center justify-between rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-700">
                                <span>
                                    Grupo configurado: <span className="font-semibold">{configuracion.grupo_wsp}</span>
                                </span>
                                <button
                                    onClick={() => setShowGrupoModal(true)}
                                    className="rounded-md border border-slate-300 bg-white px-3 py-1 text-xs font-semibold hover:bg-slate-50"
                                >
                                    Editar grupo
                                </button>
                            </div>

                            {wspData?.status === "ready" ? (
                                <>
                                    <div className="rounded-lg border border-emerald-300 bg-emerald-50 px-4 py-3 text-center text-emerald-700">
                                        WhatsApp conectado. Ya puedes generar el registro.
                                    </div>

                                    <form className="space-y-4" onSubmit={handleReport}>
                                        <div>
                                            <label className="mb-1 block text-sm font-medium text-slate-700">Fecha del reporte</label>
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
                                                className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 focus:border-slate-500 focus:outline-none"
                                            />
                                        </div>
                                        <button
                                            type="submit"
                                            className="w-full rounded-lg bg-slate-700 px-4 py-2 font-semibold text-white transition hover:bg-slate-800"
                                        >
                                            Generar registro
                                        </button>
                                    </form>
                                </>
                            ) : wspData?.status === "qr_pending" ? (
                                <div className="space-y-4 text-center">
                                    <p className="text-sm text-slate-600">Escanea este código QR para vincular WhatsApp.</p>
                                    <div className="mx-auto inline-flex rounded-xl border border-slate-300 bg-slate-50 p-3">
                                        <img src={wspData.qr ?? undefined} alt="WhatsApp QR Code" className="h-64 w-64" />
                                    </div>
                                    <p className="text-xs text-slate-500">Estado actual: {wspData.status}</p>
                                </div>
                            ) : wspData?.status === "initializing" ? (
                                <p className="text-center text-sm text-slate-600">Generando QR...</p>
                            ) : (
                                <p className="text-center text-sm text-slate-600">Procesando...</p>
                            )}
                        </section>
                    </>
                )}

                {showGrupoModal && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
                        <div className="w-full max-w-xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                            <div className="flex items-center justify-between">
                                <h3 className="text-lg font-semibold">Modificar grupo</h3>
                                <button
                                    onClick={() => setShowGrupoModal(false)}
                                    className="text-sm text-slate-500 hover:text-slate-700"
                                >
                                    Cerrar
                                </button>
                            </div>
                            <form className="mt-6 space-y-4" onSubmit={handleModificarGrupo}>
                                <div>
                                    <label className="mb-1 block text-sm font-medium text-slate-700">Grupo WhatsApp</label>
                                    <input
                                        type="text"
                                        value={grupoEdicion}
                                        onChange={(e) => setGrupoEdicion(e.target.value)}
                                        placeholder="Ej. Campaña Digital"
                                        className="w-full rounded-lg border border-slate-300 bg-slate-50 px-3 py-2 focus:border-slate-500 focus:outline-none"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    className="w-full rounded-lg bg-slate-700 px-4 py-2 font-semibold text-white transition hover:bg-slate-800"
                                >
                                    Guardar configuración
                                </button>
                            </form>
                        </div>
                    </div>
                )}

                {showEjecutivosModal && (
                    <div className="fixed inset-0 z-50 overflow-y-auto bg-black/40 p-4">
                        <div className="mx-auto w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
                            <div className="mb-4 flex items-center justify-between">
                                <h3 className="text-lg font-semibold">Gestionar ejecutivos</h3>
                                <button
                                    onClick={() => setShowEjecutivosModal(false)}
                                    className="text-sm text-slate-500 hover:text-slate-700"
                                >
                                    Cerrar
                                </button>
                            </div>

                            <form className="mb-6 grid grid-cols-1 gap-3 md:grid-cols-4" onSubmit={handleAgregarEjecutivo}>
                                <input
                                    value={nuevoNombre}
                                    onChange={(e) => setNuevoNombre(e.target.value)}
                                    placeholder="Nombre"
                                    className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2"
                                />
                                <input
                                    value={nuevoTelefono}
                                    onChange={(e) => setNuevoTelefono(e.target.value)}
                                    placeholder="N° teléfono"
                                    className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2"
                                />
                                <select
                                    value={nuevoEstado}
                                    onChange={(e) => setNuevoEstado(e.target.value)}
                                    className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2"
                                >
                                    <option value="ACTIVO">ACTIVO</option>
                                    <option value="ELIMINADO">ELIMINADO</option>
                                </select>
                                <button
                                    type="submit"
                                    className="rounded-lg bg-slate-700 px-4 py-2 font-semibold text-white transition hover:bg-slate-800"
                                >
                                    Agregar ejecutivo
                                </button>
                            </form>

                            <div className="space-y-3">
                                {ejecutivos.map((ejecutivo) => (
                                    <div key={ejecutivo.id} className="rounded-lg border border-slate-200 p-4">
                                        <div className="mb-2 text-sm font-semibold text-slate-700">{ejecutivo.nombre}</div>
                                        {editandoId === ejecutivo.id ? (
                                            <div className="grid grid-cols-1 gap-2 md:grid-cols-4">
                                                <input
                                                    value={editTelefono}
                                                    onChange={(e) => setEditTelefono(e.target.value)}
                                                    className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2"
                                                />
                                                <select
                                                    value={editEstado}
                                                    onChange={(e) => setEditEstado(e.target.value)}
                                                    className="rounded-lg border border-slate-300 bg-slate-50 px-3 py-2"
                                                >
                                                    <option value="ACTIVO">ACTIVO</option>
                                                    <option value="ELIMINADO">ELIMINADO</option>
                                                </select>
                                                <button
                                                    type="button"
                                                    onClick={() => handleModificarEjecutivo(ejecutivo.id, ejecutivo.nombre)}
                                                    className="rounded-lg bg-slate-700 px-4 py-2 text-white"
                                                >
                                                    Guardar
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => setEditandoId(null)}
                                                    className="rounded-lg border border-slate-300 px-4 py-2"
                                                >
                                                    Cancelar
                                                </button>
                                            </div>
                                        ) : (
                                            <div className="flex flex-wrap items-center gap-2 text-sm text-slate-600">
                                                <span>Tel: {ejecutivo.nro_telefono}</span>
                                                <span>Estado: {ejecutivo.estado}</span>
                                                <button
                                                    type="button"
                                                    onClick={() => prepararEdicion(ejecutivo)}
                                                    className="ml-auto rounded-md border border-slate-300 px-3 py-1 text-xs hover:bg-slate-50"
                                                >
                                                    Modificar
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={() => handleEliminarEjecutivo(ejecutivo.id, ejecutivo.nombre)}
                                                    className="rounded-md border border-red-300 px-3 py-1 text-xs text-red-700 hover:bg-red-50"
                                                >
                                                    Eliminar
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {resultadoReporte && (
                    <section className="mt-6 w-full max-w-xl space-y-4">
                        <div className="rounded-lg border border-sky-200 bg-sky-50 p-4">
                            <h3 className="mb-2 text-sm font-semibold text-sky-800">Respuesta Node (Descarga)</h3>
                            <pre className="max-h-40 overflow-auto rounded bg-white p-2 text-xs">
                                {JSON.stringify(resultadoReporte.node, null, 2)}
                            </pre>
                        </div>

                        <div className="rounded-lg border border-slate-200 bg-white p-4">
                            <h3 className="mb-2 text-sm font-semibold text-slate-700">Imagen del reporte</h3>
                            {imagenReporte && <img src={imagenReporte} alt="Reporte generado" className="w-full rounded border" />}
                        </div>

                        <button
                            onClick={() => setResultadoReporte(null)}
                            className="w-full rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-600 transition hover:bg-slate-100"
                        >
                            Limpiar resultados
                        </button>
                    </section>
                )}
            </main>
        </div>
    );
}

export default Home;