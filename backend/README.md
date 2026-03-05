# Control Diario Claro TikTok (FastAPI + Express + React)

## Arquitectura
- `backend/whatsapp-service` (Express): sesión WhatsApp + QR + descarga de imágenes.
- `backend/src` (FastAPI): autenticación, configuración por usuario, proceso OCR + DB.
- `frontend` (React): interfaz para login, reportes, configuración y QR.
- `desktop` (Electron): contenedor de escritorio que orquesta los dos backends y la UI.

## Ejecutar en localhost (sin empaquetar)

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

## Generar instalador `.exe` (Electron)

> Objetivo: un instalador único de Windows que incluya UI + FastAPI + whatsapp-service.

### Requisitos en la máquina Windows de build
- Python instalado y en `PATH`.
- Node.js + npm instalados.

### Estructura de build
1. `backend.exe` (PyInstaller) -> `release/backend/backend.exe`
2. `whatsapp-service.exe` (pkg) -> `release/whatsapp-service/whatsapp-service.exe`
3. `frontend/dist` (Vite build)
4. `electron-builder` crea instalador NSIS desde `desktop/`.

### Comando único (recomendado)
Desde la raíz del repo, ejecutar:
```bat
packaging\build_electron_installer.bat
```

### Comandos por etapa (manual)
```bat
packaging\build_backend_exe.bat
packaging\build_whatsapp_exe.bat
cd frontend && npm install && npm run build
cd desktop && npm install && npm run verify && npm run dist:win
```

### Salida esperada
- Instalador en: `desktop/dist/`
- Binarios intermedios en: `release/backend/` y `release/whatsapp-service/`


### Errores comunes y solución rápida
- **`No module named pip` al ejecutar `build_backend_exe.bat`**:
  - El script ya no usa `pip` automáticamente. Solo requiere que `PyInstaller` exista en tu entorno activo.
  - Instala con `uv add pyinstaller` dentro de `backend/`.
- **`pkg Error! No available node version satisfies ...`**:
  - `pkg` no soporta targets arbitrarios según tu Node local.
  - Este proyecto usa `node18-win-x64` como target de build para `whatsapp-service.exe`.

## Notas operativas
- En desarrollo, Electron puede arrancar FastAPI y Express en modo comando (`python -m uvicorn` y `npm start`).
- En producción empaquetada, Electron levanta los binarios incluidos (`backend.exe`, `whatsapp-service.exe`).
- Si cambia la configuración base, actualiza `backend/app_config.json` antes de empaquetar.
