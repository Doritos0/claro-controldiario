@echo off
setlocal enableextensions

set "ROOT=%~dp0.."

call "%~dp0build_backend_exe.bat"
if errorlevel 1 exit /b 1

call "%~dp0build_whatsapp_exe.bat"
if errorlevel 1 exit /b 1

pushd "%ROOT%\frontend"
call npm install
if errorlevel 1 (
  echo [ERROR] npm install frontend fallo
  popd
  exit /b 1
)
call npm run build
if errorlevel 1 (
  echo [ERROR] npm run build frontend fallo
  popd
  exit /b 1
)
popd

pushd "%ROOT%\desktop"
call npm install
if errorlevel 1 (
  echo [ERROR] npm install desktop fallo
  popd
  exit /b 1
)
call npm run verify
if errorlevel 1 (
  echo [ERROR] Verificacion de artefactos fallo
  popd
  exit /b 1
)
call npm run dist:win
if errorlevel 1 (
  echo [ERROR] electron-builder fallo
  popd
  exit /b 1
)
popd

echo [OK] Instalador generado en desktop\dist
exit /b 0
