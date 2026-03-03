@echo off
setlocal enableextensions

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

pushd "%PROJECT_DIR%" >nul
if errorlevel 1 (
  echo [ERROR] No se pudo acceder al directorio del proyecto: "%PROJECT_DIR%"
  exit /b 1
)

echo [INFO] Proyecto: %CD%

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] No se encontro python en PATH. Activa el entorno virtual correcto e intenta de nuevo.
  popd >nul
  exit /b 1
)

echo [1/3] Verificando pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
  echo [INFO] pip no disponible. Intentando bootstrap con ensurepip...
  python -m ensurepip --upgrade >nul 2>&1
  if errorlevel 1 (
    echo [ERROR] No fue posible habilitar pip automaticamente.
    echo        Ejecuta manualmente: python -m ensurepip --upgrade
    popd >nul
    exit /b 1
  )
)

echo [2/3] Verificando PyInstaller...
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo [INFO] PyInstaller no encontrado. Instalando...
  python -m pip install --upgrade pyinstaller
  if errorlevel 1 (
    echo [ERROR] No se pudo instalar PyInstaller.
    popd >nul
    exit /b 1
  )
)

echo [3/3] Generando ejecutable...
python -m PyInstaller --noconfirm --windowed --name ControlDiarioClaro ^
  --add-data "src\docs;src\docs" ^
  --add-data "settings.yaml;." ^
  --add-data "client_secret.json;." ^
  --add-data "credentials.json;." ^
  --add-data "app_config.json;." ^
  --add-data "CLARO-TIKTOK.db;." ^
  run_desktop.py

if errorlevel 1 (
  echo [ERROR] Fallo la generacion del ejecutable.
  popd >nul
  exit /b 1
)

echo.
echo [OK] Ejecutable disponible en: dist\ControlDiarioClaro\ControlDiarioClaro.exe

popd >nul
exit /b 0
