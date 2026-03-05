@echo off
setlocal enableextensions

set "ROOT=%~dp0.."
set "OUT=%ROOT%\release\backend"

if not exist "%OUT%" mkdir "%OUT%"

pushd "%ROOT%\backend"
if errorlevel 1 exit /b 1

python -m pip install --upgrade pyinstaller >nul
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
