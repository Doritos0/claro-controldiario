# Crear un `.exe` realmente portable (sin Python ni Node instalados)

Sí, **`--onefile` sí hace falta** para el launcher Python.
Y además, para no depender de Node en la PC destino, se empaqueta `whatsapp-service` como `.exe` con `pkg`.

## Estrategia final

1. Build `frontend`.
2. Build `backend/whatsapp-service` a `whatsapp-service.exe`.
3. Build `desktop_launcher.py` con PyInstaller `--onefile`, incluyendo backend + frontend + runtime.

Con esto el usuario final ejecuta **solo** `dist/ClaroControlDiario.exe`.

---

## Build automático (Windows)

```powershell
./scripts/build_windows_exe.ps1
```

El script ahora:
- valida errores de cada paso y se detiene si algo falla,
- libera procesos que bloquean archivos (`node`, `esbuild`, `vite`, `npm`),
- reintenta instalación npm en caso de `EPERM` (lock de archivos),
- usa `pkg@5.8.1` con target `node18-win-x64` (compatible),
- valida que exista `backend/whatsapp-service/dist/whatsapp-service.exe` antes de continuar.

---

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

---

## Troubleshooting (errores que reportaste)

### 1) `EPERM ... lightningcss.win32-x64-msvc.node` o `Acceso denegado ... esbuild.exe`
Causa común: binarios nativos bloqueados por procesos activos (Node/Vite/esbuild), antivirus o explorador.

Qué hacer:
1. Cierra VSCode, terminales y cualquier `node.exe` activo.
2. Desactiva temporalmente antivirus en carpeta del proyecto (o agrega excepción).
3. Ejecuta PowerShell como Administrador.
4. Reintenta `./scripts/build_windows_exe.ps1`.

El script actualizado ya intenta esto automáticamente:
- mata procesos bloqueantes (`node`, `esbuild`, `vite`, `npm`),
- elimina `node_modules` con estrategia robusta (`Remove-Item` + fallback `rmdir /s /q`),
- reinstala dependencias.

Extra útil:
```powershell
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### 2) `"tsc" no se reconoce...`
Suele pasar cuando falló instalación de dependencias del frontend y no existe `node_modules/.bin/tsc`.

Con el script nuevo esto se corrige porque:
- intenta `npm ci`,
- si falla, limpia y hace `npm install`,
- recién entonces ejecuta `npm run build`.

### 3) `pkg ... No available node version satisfies 'node20'`
Correcto: `pkg` no soporta ese target en tu contexto.

Solución aplicada:
- target cambiado a `node18-win-x64`.

### 4) `Copy-Item ... whatsapp-service.exe no existe`
Ese error era consecuencia del fallo anterior de `pkg`.

Solución aplicada:
- el script valida existencia del archivo y aborta con mensaje claro antes de copiar.

---

## Cómo probar el `.exe`

1. Ejecuta `dist/ClaroControlDiario.exe`.
2. Verifica endpoints:
   - `http://127.0.0.1:8000/swagger`
   - `http://127.0.0.1:3000/docs`
   - `http://127.0.0.1:5173`
3. Flujo funcional:
   - login
   - QR WhatsApp
   - descargar por fecha
   - OCR + dashboard
4. Reinicia app y valida persistencia en `%LOCALAPPDATA%/ClaroControlDiario`.

---

## Nota
`whatsapp-web.js` depende de Chromium/Puppeteer; en algunas máquinas puede requerir ajustes adicionales del runtime del navegador.
