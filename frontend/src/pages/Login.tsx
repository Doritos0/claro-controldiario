import React, { useState } from "react"
import { AuthApi } from "../api"
import { webConfig } from "../config"
import { useNavigate } from 'react-router-dom';

export function Login(){
    
    const navigate = useNavigate();
    const [user, setUser] = useState('')
    const [pass, setPass] = useState('')
    const [error, setError] = useState<string | null>(null);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        const basePath = import.meta.env.VITE_API_PYTHON
        const api = new AuthApi(webConfig.getApiSinToken(), basePath);
        const response = await api.autenticarUsuario({
            loginRequest: {
                user: user,
                password: pass
            }
        })
        const accessToken = response.data.access_token;
        const refreshToken = response.data.refresh_token;

        if (!accessToken) {
            setError('La respuesta no contiene token');
            console.error(error)
            return;
        }

        localStorage.setItem('accessToken', accessToken);
        localStorage.setItem('refreshToken', refreshToken);

        navigate('/home', { replace: true });

    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
            {/* Contenedor Principal */}
            <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
                
                {/* Encabezado */}
                <div className="text-center mb-8">
                    <h2 className="text-3xl font-extrabold text-gray-900">Bienvenido</h2>
                    <p className="text-gray-500 mt-2">Ingresa tus credenciales para acceder</p>
                </div>

                {/* Formulario */}
                <form className="space-y-6" onSubmit={handleLogin}>
                    
                    {/* Campo Usuario */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Usuario</label>
                        <input 
                            type="text" 
                            value={user}
                            onChange={(e) => setUser(e.target.value)}
                            placeholder="Ej: usuario" 
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
                        />
                    </div>

                    {/* Campo Password */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Contraseña</label>
                        <input 
                            type="password" 
                            value={pass}
                            onChange={(e) => setPass(e.target.value)}
                            placeholder="••••••••" 
                            className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition duration-200"
                        />
                    </div>

                    {/* Opciones adicionales */}
                    <div className="flex items-center justify-between text-sm">
                        <label className="flex items-center text-gray-600">
                            <input type="checkbox" className="rounded border-gray-300 text-indigo-600 shadow-sm focus:ring-indigo-500 mr-2" />
                            Recordarme
                        </label>
                        <a href="#" className="text-indigo-600 hover:text-indigo-500 font-medium">¿Olvidaste tu clave?</a>
                    </div>

                    {/* Botón de Acción */}
                    <button
                        type="submit"
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 rounded-xl shadow-lg hover:shadow-indigo-200 transition duration-300 transform active:scale-95"
                    >
                        Iniciar Sesión
                    </button>
                </form>

                {/* Footer del Login */}
                <div className="mt-8 text-center text-sm text-gray-500">
                    ¿No tienes cuenta? <a href="#" className="text-indigo-600 font-bold hover:underline">Contacta a soporte</a>
                </div>
            </div>
        </div>
    )
}

export default Login