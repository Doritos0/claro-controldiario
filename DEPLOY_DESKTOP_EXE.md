# Crear y probar el ejecutable (`.exe`) de este proyecto

Esta guía sí está alineada con la estructura actual del repo:
- `frontend` (React)
- `backend` (FastAPI)
- `backend/whatsapp-service` (Node/Express)

## 1) Qué cambia al pasar a `.exe`

Para escritorio no debes depender de rutas relativas del repo. Ya quedó preparado:
- DB SQLite en `APP_DATA_DIR` (o `BD_PATH` si lo defines)
- imágenes descargadas en `DOWNLOADS_DIR`
- Node configurable por `NODE_PORT`, `FRONTEND_ORIGIN`, `SESSION_DIR`, `DOWNLOADS_DIR`

## 2) Variables de entorno recomendadas

Backend/Node compartido:

```env
AMBIENTE=sqlite
BD_NAME=CLARO-TIKTOK
APP_DATA_DIR=%LOCALAPPDATA%/ClaroControlDiario
DOWNLOADS_DIR=%LOCALAPPDATA%/ClaroControlDiario/descargas
NODE_PORT=3000
FRONTEND_ORIGIN=http://127.0.0.1:5173
GEMINI_API_KEY=TU_API_KEY
GEMINI_MODEL_OCR=gemini-3-flash-preview
```

Frontend build:

```env
VITE_API_PYTHON=http://127.0.0.1:8000
VITE_API_EXPRESS=http://127.0.0.1:3000
```

## 3) Prueba local antes de empaquetar

En 3 terminales:

```bash
# terminal 1
cd backend
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

```bash
# terminal 2
cd backend/whatsapp-service
node src/index.js
```

```bash
# terminal 3
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173
```

Verificaciones:
- FastAPI: `http://127.0.0.1:8000/swagger`
- Node docs: `http://127.0.0.1:3000/docs`
- Frontend: `http://127.0.0.1:5173`

## 4) Crear el `.exe` (launcher único)

Se añadió `desktop_launcher.py` para abrir los 3 componentes (Node + FastAPI + UI estática) desde un solo proceso.

### Build manual (Windows)

```powershell
pip install pyinstaller
cd <raiz-del-repo>

# build frontend para incluirlo dentro del exe
cd frontend
$env:VITE_API_PYTHON="http://127.0.0.1:8000"
$env:VITE_API_EXPRESS="http://127.0.0.1:3000"
npm ci
npm run build
cd ..

# generar exe
pyinstaller --noconfirm --clean --onefile --name ClaroControlDiario `
  --add-data "backend;backend" `
  --add-data "frontend/dist;frontend/dist" `
  desktop_launcher.py
```

O usa el helper:

```powershell
./scripts/build_windows_exe.ps1
```

Salida:
- `dist/ClaroControlDiario.exe`

## 5) Cómo probar el `.exe`

1. Copia y abre `dist/ClaroControlDiario.exe`.
2. Verifica que levanta:
   - `http://127.0.0.1:8000/swagger`
   - `http://127.0.0.1:3000/docs`
   - `http://127.0.0.1:5173` (si `frontend/dist` fue incluido correctamente)
3. Ejecuta flujo real:
   - iniciar sesión web
   - iniciar sesión de WhatsApp (QR)
   - descargar fotos por fecha
   - ejecutar OCR/reporte
4. Confirma datos en carpeta de usuario (`APP_DATA_DIR`) y que persiste entre reinicios.

## 6) Punto importante de distribución

El launcher puede usar `node` del sistema. Si quieres **cero dependencias en el PC destino**, empaqueta también Node runtime y colócalo en:

- `dist/runtime/node/node.exe`

Así el launcher usará ese binario y no dependerá de instalación previa de Node.
