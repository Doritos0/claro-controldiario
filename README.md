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

```bash
pyinstaller --noconfirm --windowed --name ControlDiarioClaro \
  --add-data "src/docs;src/docs" \
  --add-data "settings.yaml;." \
  --add-data "client_secret.json;." \
  --add-data "credentials.json;." \
  run_desktop.py
```

El ejecutable se genera en:

- `dist/ControlDiarioClaro/ControlDiarioClaro.exe`

---

## 4) Flujo esperado para el usuario final

1. Instala/abre `ControlDiarioClaro.exe`.
2. Inicia sesión.
3. Clic en **Generar reporte**.
4. Revisa el dashboard generado en pantalla.
5. Clic en **Descargar dashboard** para guardar el PNG.

El sistema guarda también una copia en `artifacts/` con nombre:
- `dashboard_YYYY-MM-DD.png`
