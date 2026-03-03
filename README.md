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
  --add-data "src/docs;src/docs" \
  --add-data "settings.yaml;." \
  --add-data "client_secret.json;." \
  --add-data "credentials.json;." \
  --add-data "app_config.json;." \
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

La app resuelve configuración en este orden:
1. Variables de entorno (`.env`) si existen.
2. `app_config.json` junto al `.exe`.
3. Valor por defecto para credenciales: `credentials.json` junto al `.exe`.

Archivo recomendado `app_config.json`:

```json
{
  "google_drive_root_folder_id": "TU_FOLDER_ID",
  "google_drive_credentials_path": "credentials.json"
}
```

> Para entregar al usuario final: distribuye la carpeta `dist/ControlDiarioClaro/` completa, incluyendo `app_config.json` y `credentials.json`.

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
