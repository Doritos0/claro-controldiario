# Guía para exportar Frontend + FastAPI + Node en un solo `.exe`

## Objetivo
Empaquetar una app de escritorio que levanta internamente:
- Frontend (React)
- API Python (FastAPI)
- Servicio Node (Express + WhatsApp)

## Arquitectura recomendada en escritorio
1. El `.exe` principal (por ejemplo Electron/Tauri/PyWebview) abre la UI local.
2. Al iniciar, el wrapper arranca FastAPI en `127.0.0.1:8000`.
3. También arranca Node en `127.0.0.1:3000`.
4. React consume esas APIs locales (igual que hoy).

## Cambios aplicados en este repo para hacerlo portable

### 1) Rutas de datos en carpetas de usuario (no rutas relativas del proyecto)
Se agregó `backend/src/config/path_config.py` para centralizar:
- `APP_DATA_DIR` (base de datos local de la app)
- `DOWNLOADS_DIR` (imágenes descargadas por fecha)

Si no defines variables, usa por defecto:
- Windows: `%LOCALAPPDATA%/ClaroControlDiario`
- Linux/Mac: `~/.claro-control-diario`

### 2) SQLite persistente para el `.exe`
`engine_config.py` ahora crea/usa la DB en `APP_DATA_DIR` cuando no existe `BD_PATH`.

Variables válidas:
- `AMBIENTE=sqlite`
- `BD_NAME=CLARO-TIKTOK`
- opcional `BD_PATH=/ruta/absoluta/CLARO-TIKTOK.db`

### 3) OCR leyendo desde carpeta configurable
`proceso_01_ocr.py` ahora busca imágenes en:
- `DOWNLOADS_DIR/<fecha>`
- o fallback `APP_DATA_DIR/descargas/<fecha>`

### 4) Node con rutas y puerto configurables
`backend/whatsapp-service` ahora soporta:
- `NODE_PORT` (por defecto 3000)
- `SESSION_DIR` (sesión WhatsApp)
- `DOWNLOADS_DIR` (carpeta de imágenes)
- `FRONTEND_ORIGIN` para CORS

## `.env` recomendado para desktop

### Backend/FastAPI + compartido
```env
AMBIENTE=sqlite
BD_NAME=CLARO-TIKTOK
APP_DATA_DIR=%LOCALAPPDATA%/ClaroControlDiario
DOWNLOADS_DIR=%LOCALAPPDATA%/ClaroControlDiario/descargas
GEMINI_API_KEY=...
GEMINI_MODEL_OCR=gemini-3-flash-preview
NODE_PORT=3000
FRONTEND_ORIGIN=http://127.0.0.1:5173
```

### Frontend
```env
VITE_API_PYTHON=http://127.0.0.1:8000
VITE_API_EXPRESS=http://127.0.0.1:3000
```

> En empaquetado final puedes mantener estos puertos fijos o inyectarlos en build/runtime.

## Checklist adicional para pasar a escritorio
- Incluir Chromium/Playwright/Puppeteer según lo que use `whatsapp-web.js`.
- Ejecutar todo con `127.0.0.1` (no `localhost`) para evitar algunos problemas de DNS/políticas.
- Definir estrategia de logs en carpeta de usuario.
- Manejar autoarranque/autoapagado limpio de procesos FastAPI y Node.
- Firma de código y permisos de antivirus (Windows Defender suele bloquear apps nuevas).
- Instalador (MSI/NSIS) para crear accesos directos y desinstalación.
- Migraciones de DB cuando cambie el esquema.

## Sugerencia de empaquetado
- Opción A: **Electron** (UI + process manager para Python/Node).
- Opción B: **PyInstaller + WebView** (si quieres centrar todo en Python).
- Opción C: **Tauri** (binario más ligero, más configuración inicial).

La clave es que el `.exe` principal gestione procesos hijos y variables de entorno compartidas.
