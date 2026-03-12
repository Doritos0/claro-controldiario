$ErrorActionPreference = "Stop"

Write-Host "[1/3] Build frontend"
Push-Location frontend
$env:VITE_API_PYTHON = "http://127.0.0.1:8000"
$env:VITE_API_EXPRESS = "http://127.0.0.1:3000"
npm ci
npm run build
Pop-Location

Write-Host "[2/3] Build launcher exe"
pyinstaller --noconfirm --clean --onefile --name ClaroControlDiario --add-data "backend;backend" --add-data "frontend/dist;frontend/dist" desktop_launcher.py

Write-Host "[3/3] Done"
Write-Host "Output: dist/ClaroControlDiario.exe"
Write-Host "Opcional: copia runtime/node/node.exe a dist/runtime/node/node.exe para no depender de Node instalado."
