# Control Diario Claro TikTok (FastAPI + Express + React)

## Arquitectura
- `whatsapp-service` (Express): inicia sesión en WhatsApp Web, entrega QR y descarga imágenes por grupo/fecha.
- `src` (FastAPI): autentica usuarios, guarda configuración por usuario, procesa imágenes con Gemini y escribe en SQLite.
- `frontend` (React): login y panel para generar reportes, registrar ejecutivos y configurar grupo WhatsApp.

## Ejecutar en localhost

### 1) WhatsApp API (Express)
```bash
cd backend/whatsapp-service
npm install
npm start
```
Servicio: `http://localhost:3100`

### 2) FastAPI
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
Servicio: `http://localhost:8000`

### 3) Frontend React
```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```
UI: `http://localhost:5173`

## Flujo de uso
1. Login en frontend.
2. Si no existe configuración, ingresar `grupo_wsp`.
3. Botón “Iniciar sesión WhatsApp” para mostrar QR.
4. Generar reporte (ayer o fecha específica):
   - FastAPI invoca `POST /descargar-imagenes` en Express.
   - FastAPI lee `backend/whatsapp-service/src/descargas/<fecha>`.
   - Gemini procesa imágenes y se insertan `LIVE` en DB.
   - Se genera dashboard diario.

## Empaquetado recomendado (.exe)
Para tres procesos (Node + Python + UI), la estrategia más robusta es **Electron** como contenedor:
- React compilado como frontend embebido.
- Electron arranca FastAPI y Express como subprocesos.
- `electron-builder` genera instalador Windows.

Ventajas:
- Un único instalador para usuario final.
- Mejor manejo de procesos múltiples que PyInstaller solo.
- Permite reiniciar servicios internos y mostrar estado (QR/sesión) en UI.
