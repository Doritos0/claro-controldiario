import { FormEvent, useEffect, useMemo, useState } from 'react'
import './App.css'

type Session = { user_id: number; empresa_id: number; user: string }
const API = 'http://localhost:8000'

function App() {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState('')
  const [password, setPassword] = useState('')
  const [grupo, setGrupo] = useState('')
  const [fecha, setFecha] = useState(new Date().toISOString().slice(0, 10))
  const [mensaje, setMensaje] = useState('')
  const [qr, setQr] = useState<string | null>(null)
  const [necesitaConfig, setNecesitaConfig] = useState(false)

  const ayer = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 1)
    return d.toISOString().slice(0, 10)
  }, [])

  async function login(e: FormEvent) {
    e.preventDefault()
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user, password }),
    })
    if (!res.ok) return setMensaje('Credenciales inválidas')
    const data = await res.json()
    setSession(data)
  }

  async function cargarConfiguracion(userId: number) {
    const res = await fetch(`${API}/configuracion/${userId}`)
    const data = await res.json()
    setNecesitaConfig(!data.exists)
    setGrupo(data.grupo_wsp ?? '')
  }

  useEffect(() => {
    if (session) cargarConfiguracion(session.user_id)
  }, [session])

  async function guardarConfig() {
    if (!session) return
    await fetch(`${API}/configuracion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: session.user_id, grupo_wsp: grupo }),
    })
    setNecesitaConfig(false)
    setMensaje('Configuración guardada')
  }

  async function iniciarWhatsapp() {
    const res = await fetch(`${API}/whatsapp/iniciar-session`, { method: 'POST' })
    const data = await res.json()
    setQr(data.qr)
    setMensaje(`Estado WhatsApp: ${data.status}`)
  }

  async function generarReporte(fechaReporte: string) {
    if (!session) return
    const res = await fetch(`${API}/reporte/generar`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: session.user_id, fecha: fechaReporte }),
    })
    const data = await res.json()
    setMensaje(`Imágenes procesadas: ${data.procesadas}. Dashboard: ${data.dashboard_path ?? 'sin datos'}`)
  }

  async function crearEjecutivo(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    if (!session) return
    const f = new FormData(e.currentTarget)
    const payload = {
      user_id: session.user_id,
      nombre: f.get('nombre'),
      estado: f.get('estado'),
      eps: f.get('eps'),
    }
    await fetch(`${API}/ejecutivos`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
    })
    setMensaje('Ejecutivo registrado')
    e.currentTarget.reset()
  }

  async function consolidado() {
    if (!session) return
    const res = await fetch(`${API}/reporte/consolidado`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: session.user_id, fecha }),
    })
    const data = await res.json()
    setMensaje(`Reporte consolidado con ${data.length} filas`)
  }

  if (!session) {
    return <main className='shell'><form className='card' onSubmit={login}><h1>Control Diario</h1><input placeholder='Usuario' value={user} onChange={(e) => setUser(e.target.value)} /><input placeholder='Password' type='password' value={password} onChange={(e) => setPassword(e.target.value)} /><button>Ingresar</button><p>{mensaje}</p></form></main>
  }

  return (
    <main className='shell'>
      <section className='grid'>
        <div className='card'>
          <h2>Generar reporte</h2>
          <button onClick={() => generarReporte(ayer)}>Ayer</button>
          <input type='date' value={fecha} onChange={(e) => setFecha(e.target.value)} />
          <button onClick={() => generarReporte(fecha)}>Fecha específica</button>
          <button onClick={consolidado}>Reporte consolidado</button>
          <button onClick={iniciarWhatsapp}>Iniciar sesión WhatsApp</button>
          {qr && <img src={qr} alt='QR WhatsApp' className='qr' />}
        </div>

        <form className='card' onSubmit={crearEjecutivo}>
          <h2>Registrar ejecutivo</h2>
          <input name='nombre' placeholder='Nombre' required />
          <input name='estado' placeholder='Estado' defaultValue='ACTIVO' required />
          <input name='eps' placeholder='EPS' defaultValue='PHOENIX' required />
          <button>Guardar</button>
        </form>

        <div className='card'>
          <h2>Configuración</h2>
          {(necesitaConfig || true) && <><input value={grupo} onChange={(e) => setGrupo(e.target.value)} placeholder='Grupo de WhatsApp' /><button onClick={guardarConfig}>Guardar configuración</button></>}
        </div>
      </section>
      <p className='status'>{mensaje}</p>
    </main>
  )
}

export default App
