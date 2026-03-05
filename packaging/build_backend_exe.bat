@echo off
setlocal enableextensions

set "ROOT=%~dp0.."
set "OUT=%ROOT%\release\backend"

if not exist "%OUT%" mkdir "%OUT%"

pushd "%ROOT%\backend"
if errorlevel 1 exit /b 1

REM Entornos creados con uv pueden no traer pip, por eso evitamos depender de pip aqui.
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] PyInstaller no esta disponible en este entorno.
  echo         Instala con: uv add pyinstaller  (o pip install pyinstaller)
  popd
  exit /b 1
)

python -m PyInstaller --noconfirm --onefile --name backend run_fastapi.py
if errorlevel 1 (
  echo [ERROR] No se pudo generar backend.exe
  popd
  exit /b 1
)

copy /Y dist\backend.exe "%OUT%\backend.exe" >nul
if errorlevel 1 (
  echo [ERROR] No se pudo copiar backend.exe a release
  popd
  exit /b 1
)

popd
echo [OK] backend.exe generado en %OUT%\backend.exe
exit /b 0
