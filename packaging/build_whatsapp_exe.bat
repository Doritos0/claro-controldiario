@echo off
setlocal enableextensions

set "ROOT=%~dp0.."
set "OUT=%ROOT%\release\whatsapp-service"

if not exist "%OUT%" mkdir "%OUT%"

pushd "%ROOT%\backend\whatsapp-service"
if errorlevel 1 exit /b 1

call npm install
if errorlevel 1 (
  echo [ERROR] npm install fallo
  popd
  exit /b 1
)

call npm run build:win
if errorlevel 1 (
  echo [ERROR] No se pudo generar whatsapp-service.exe
  popd
  exit /b 1
)

copy /Y dist\whatsapp-service.exe "%OUT%\whatsapp-service.exe" >nul
if errorlevel 1 (
  echo [ERROR] No se pudo copiar whatsapp-service.exe a release
  popd
  exit /b 1
)

popd
echo [OK] whatsapp-service.exe generado en %OUT%\whatsapp-service.exe
exit /b 0
