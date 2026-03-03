@echo off
setlocal

echo [1/2] Instalando pyinstaller...
python -m pip install pyinstaller

echo [2/2] Generando ejecutable...
pyinstaller --noconfirm --windowed --name ControlDiarioClaro ^
  --add-data "src\docs;src\docs" ^
  --add-data "settings.yaml;." ^
  --add-data "client_secret.json;." ^
  --add-data "credentials.json;." ^
  run_desktop.py

echo.
echo Listo. Ejecutable disponible en dist\ControlDiarioClaro\ControlDiarioClaro.exe
pause
