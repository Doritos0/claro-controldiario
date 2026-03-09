import { jwtDecode } from "jwt-decode";

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



    return(
        <h2>Hola Mundo! Bienvenido { usuario } para la empresa { empresa } con el identificador { usuarioId }</h2>
    )
}

export default Home