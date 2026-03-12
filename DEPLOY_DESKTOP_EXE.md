# Crear un `.exe` realmente portable (sin Python ni Node instalados)

Sí, **`--onefile` sí hace falta** para el launcher Python (y ya está incluido).
Pero ojo: `--onefile` solo empaqueta **Python**. Para no depender de Node también, hay que empaquetar el servicio Node como `.exe` adicional y meterlo dentro del bundle final.

## Estrategia final

1. Compilar `frontend` (`npm run build`).
2. Compilar `backend/whatsapp-service` a `whatsapp-service.exe` usando `pkg`.
3. Empaquetar `desktop_launcher.py` con PyInstaller `--onefile`, incluyendo:
   - `backend/`
   - `frontend/dist/`
   - `runtime/whatsapp-service/whatsapp-service.exe`

Con eso, en el PC destino no necesitas Python ni Node instalados.

## Variables recomendadas

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

## Build automático (Windows)

```powershell
./scripts/build_windows_exe.ps1
```

Este script hace:
- build frontend
- build Node `.exe` con `pkg`
- copia a `runtime/whatsapp-service/whatsapp-service.exe`
- build final de `dist/ClaroControlDiario.exe` con `--onefile`

## Build manual (Windows)

```powershell
# 1) Frontend
cd frontend
$env:VITE_API_PYTHON="http://127.0.0.1:8000"
$env:VITE_API_EXPRESS="http://127.0.0.1:3000"
npm ci
npm run build
cd ..

# 2) Node service -> exe
cd backend/whatsapp-service
npm ci
npx pkg src/index.js --targets node20-win-x64 --output dist/whatsapp-service.exe
cd ../..
mkdir runtime\whatsapp-service -Force
copy backend\whatsapp-service\dist\whatsapp-service.exe runtime\whatsapp-service\whatsapp-service.exe

# 3) Launcher Python -> onefile
pip install pyinstaller
pyinstaller --noconfirm --clean --onefile --name ClaroControlDiario `
  --add-data "backend;backend" `
  --add-data "frontend/dist;frontend/dist" `
  --add-data "runtime;runtime" `
  desktop_launcher.py
```

## Cómo probar el `.exe`

1. Ejecuta `dist/ClaroControlDiario.exe`.
2. Verifica:
   - `http://127.0.0.1:8000/swagger`
   - `http://127.0.0.1:3000/docs`
   - `http://127.0.0.1:5173`
3. Prueba flujo completo:
   - login
   - QR WhatsApp
   - descarga por fecha
   - OCR y dashboard
4. Reinicia app y valida persistencia de DB/descargas en `%LOCALAPPDATA%/ClaroControlDiario`.

## Nota importante

`whatsapp-web.js` usa Chromium/Puppeteer; en algunas máquinas puede requerir ajustes adicionales de runtime (dependencias del navegador). Si pasa, documenta esa dependencia en tu instalador final.
