$ErrorActionPreference = "Stop"

Write-Host "[1/5] Build frontend"
Push-Location frontend
$env:VITE_API_PYTHON = "http://127.0.0.1:8000"
$env:VITE_API_EXPRESS = "http://127.0.0.1:3000"
npm ci
npm run build
Pop-Location

Write-Host "[2/5] Build WhatsApp service executable (pkg)"
Push-Location backend/whatsapp-service
npm ci
npx pkg src/index.js --targets node20-win-x64 --output dist/whatsapp-service.exe
Pop-Location

Write-Host "[3/5] Prepare runtime folder"
New-Item -ItemType Directory -Force -Path runtime/whatsapp-service | Out-Null
Copy-Item -Force backend/whatsapp-service/dist/whatsapp-service.exe runtime/whatsapp-service/whatsapp-service.exe

Write-Host "[4/5] Build launcher exe (PyInstaller onefile)"
pyinstaller --noconfirm --clean --onefile --name ClaroControlDiario --add-data "backend;backend" --add-data "frontend/dist;frontend/dist" --add-data "runtime;runtime" desktop_launcher.py

Write-Host "[5/5] Done"
Write-Host "Output: dist/ClaroControlDiario.exe"
Write-Host "Este ejecutable ya no depende de Node instalado (usa runtime/whatsapp-service/whatsapp-service.exe)."
