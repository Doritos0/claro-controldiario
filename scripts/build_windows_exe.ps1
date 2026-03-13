$ErrorActionPreference = "Stop"

function Invoke-Step {
  param(
    [string]$Name,
    [scriptblock]$Action
  )

  Write-Host $Name
  & $Action
  if ($LASTEXITCODE -ne 0) {
    throw "Step failed ($Name) with exit code $LASTEXITCODE"
  }
}

function Stop-LockingProcesses {
  Write-Warning "Intentando liberar archivos bloqueados (node/esbuild/vite)..."
  $processNames = @("node", "esbuild", "vite", "npm")
  foreach ($p in $processNames) {
    Get-Process -Name $p -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Seconds 2
}

function Remove-PathRobust {
  param([string]$TargetPath)

  if (!(Test-Path $TargetPath)) {
    return
  }

  $attempt = 0
  while ($attempt -lt 3 -and (Test-Path $TargetPath)) {
    try {
      Remove-Item -Recurse -Force $TargetPath -ErrorAction Stop
    }
    catch {
      Write-Warning "No se pudo borrar $TargetPath con Remove-Item (intento $($attempt + 1))."
      Stop-LockingProcesses

      # Fallback con cmd/rmdir, a veces maneja mejor locks parciales en Windows
      cmd /c "rmdir /s /q \"$TargetPath\"" | Out-Null
      Start-Sleep -Seconds 1
    }

    $attempt++
  }

  if (Test-Path $TargetPath) {
    throw "No se pudo eliminar $TargetPath. Cierra VSCode/explorador/terminales y antivirus, luego reintenta."
  }
}

function Install-NodeDeps {
  param([string]$Path)

  Push-Location $Path
  try {
    npm ci
    if ($LASTEXITCODE -eq 0) {
      return
    }

    Write-Warning "npm ci falló en $Path. Reintentando con limpieza por posible lock/EPERM..."

    Stop-LockingProcesses
    Remove-PathRobust "node_modules"

    if (Test-Path "package-lock.json") {
      try {
        Remove-Item -Force "package-lock.json" -ErrorAction Stop
      }
      catch {
        Write-Warning "No se pudo eliminar package-lock.json. Reintentando tras liberar locks..."
        Stop-LockingProcesses
        Remove-Item -Force "package-lock.json" -ErrorAction Stop
      }
    }

    npm install
    if ($LASTEXITCODE -ne 0) {
      throw "npm install también falló en $Path"
    }
  }
  finally {
    Pop-Location
  }
}

Invoke-Step "[1/6] Build frontend" {
  $env:VITE_API_PYTHON = "http://127.0.0.1:8000"
  $env:VITE_API_EXPRESS = "http://127.0.0.1:3000"

  Install-NodeDeps "frontend"

  Push-Location frontend
  try {
    npm run build
    if ($LASTEXITCODE -ne 0) {
      throw "npm run build falló en frontend"
    }
  }
  finally {
    Pop-Location
  }
}

Invoke-Step "[2/6] Build WhatsApp service executable (pkg)" {
  Install-NodeDeps "backend/whatsapp-service"

  Push-Location backend/whatsapp-service
  try {
    npm exec --yes pkg@5.8.1 -- src/index.js --targets node18-win-x64 --output dist/whatsapp-service.exe
    if ($LASTEXITCODE -ne 0) {
      throw "pkg falló generando whatsapp-service.exe"
    }
  }
  finally {
    Pop-Location
  }
}

Invoke-Step "[3/6] Validate WhatsApp executable" {
  if (!(Test-Path "backend/whatsapp-service/dist/whatsapp-service.exe")) {
    throw "No se generó backend/whatsapp-service/dist/whatsapp-service.exe"
  }
}

Invoke-Step "[4/6] Prepare runtime folder" {
  New-Item -ItemType Directory -Force -Path runtime/whatsapp-service | Out-Null
  Copy-Item -Force backend/whatsapp-service/dist/whatsapp-service.exe runtime/whatsapp-service/whatsapp-service.exe
}

Invoke-Step "[5/6] Build launcher exe (PyInstaller onefile)" {
  pyinstaller --noconfirm --clean --onefile --name ClaroControlDiario --add-data "backend;backend" --add-data "frontend/dist;frontend/dist" --add-data "runtime;runtime" desktop_launcher.py
  if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller falló"
  }
}

Invoke-Step "[6/6] Done" {
  Write-Host "Output: dist/ClaroControlDiario.exe"
  Write-Host "Portable: no requiere Python/Node instalados en PC destino."
}
