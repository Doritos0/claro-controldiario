# Control Diario Claro TikTok

Este proyecto ahora soporta **dos modos de uso**:

1. **Modo script/backend** para desarrollo técnico.
2. **Modo app de escritorio** para usuarios sin conocimientos de Python/consola.

---

## 1) Ejecutar backend (modo técnico)

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 2) Ejecutar app de escritorio (modo usuario final)

La app muestra:
- Login.
- Botón para generar reporte.
- Opción de fecha por defecto (**ayer**) o fecha manual (`dd/mm/yy`).
- Vista previa del dashboard generado.
- Botón para descargar el PNG en la ubicación elegida.

### Ejecutar en local (sin empaquetar)

```bash
python run_desktop.py
```

Credenciales por defecto del login:
- Usuario: `admin`
- Contraseña: `claro123`

> Recomendación: para producción, compilar el ejecutable y distribuirlo al usuario final.

---

## 3) Crear ejecutable para Windows (.exe)

### Requisitos en la máquina de build

```bash
pip install pyinstaller
```

### Comando de empaquetado

Desde la **raíz del proyecto**:

```bash
pyinstaller --noconfirm --windowed --name ControlDiarioClaro \
  --collect-all "googleapiclient" \
  --collect-all "google_auth_oauthlib" \
  --collect-all "pydantic" \
  --collect-all "sqlmodel" \
  --collect-all "sqlalchemy" \
  --add-data "src/docs;src/docs" \
  --add-data "settings.yaml;." \
  --add-data "client_secret.json;." \
  --add-data "credentials.json;." \
  --add-data "app_config.json;." \
  --add-data "CLARO-TIKTOK.db;." \
  run_desktop.py
```

O usando el script helper (puedes ejecutarlo incluso estando dentro de `packaging/`):

```bash
.\build_windows_exe.bat
```

El ejecutable se genera en:

- `dist/ControlDiarioClaro/ControlDiarioClaro.exe`

---


### Importante para ejecución en `.exe`

El ejecutable queda preparado para usar configuración local sin depender de rutas de tu computador.

La app resuelve configuración en modo **Zero-Config**:
1. Lee `app_config.json` incluido junto al `.exe` (copiado a `%LOCALAPPDATA%/ClaroControlDiario/`).
2. Usa `credentials.json` local del usuario en esa misma carpeta.
3. Mantiene compatibilidad con variables de entorno si existen, pero ya no depende de `.env`.

Archivo recomendado `app_config.json`:

```json
{
  "google_drive_root_folder_id": "TU_FOLDER_ID",
  "google_drive_credentials_path": "credentials.json",
  "gemini_api_key": "TU_GEMINI_API_KEY",
  "gemini_model_ocr": "gemini-3-flash-preview"
}
```

> Para entregar al usuario final: distribuye la carpeta `dist/ControlDiarioClaro/` completa, incluyendo `app_config.json` y `credentials.json`.

Además, para OCR debes configurar `gemini_api_key` (o `GEMINI_API_KEY`).
La app puede pedirla en el primer intento y guardarla automáticamente en `app_config.json`.


### Base de datos lista para usar (primer arranque)

El ejecutable inicializa automáticamente una base SQLite local del usuario (no depende de rutas del PC del desarrollador):
- Carpeta de datos en Windows: `%LOCALAPPDATA%/ControlDiarioClaro/`
- Archivo DB: `CLARO-TIKTOK.db`

En el primer arranque:
1. Copia una DB base incluida en el ejecutable (si existe).
2. Crea tablas faltantes automáticamente.
3. Si no hay ejecutivos, carga ejecutivos iniciales por defecto.

Con esto se evita el error `no such table: ejecutivo`.

### Diagnóstico rápido en app de escritorio

Si el proceso no genera dashboard, la app ahora muestra un mensaje detallado con la causa probable (variables faltantes, ruta de credenciales inválida o ausencia de datos/imágenes para la fecha).

## 4) Flujo esperado para el usuario final

1. Instala/abre `ControlDiarioClaro.exe`.
2. Inicia sesión.
3. Clic en **Generar reporte**.
4. Revisa el dashboard generado en pantalla.
5. Clic en **Descargar dashboard** para guardar el PNG.

El sistema guarda también una copia en `artifacts/` con nombre:
- `dashboard_YYYY-MM-DD.png`
