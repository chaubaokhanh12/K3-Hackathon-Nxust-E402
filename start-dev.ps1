$ErrorActionPreference = 'Stop'

$projectRoot = $PSScriptRoot
$frontend = Join-Path $projectRoot 'frontend'

# Kiem tra xem co conda environment dang active khong
if (-not $env:CONDA_PREFIX) {
  throw 'Khong tim thay conda environment dang active. Hay activate conda environment truoc (vi du: conda activate <ten_moi>).'
}

$python = Join-Path $env:CONDA_PREFIX 'python.exe'

if (-not (Test-Path -LiteralPath $python)) {
  throw "Khong tim thay python trong conda environment: $env:CONDA_PREFIX"
}
if (-not (Test-Path -LiteralPath (Join-Path $frontend 'node_modules'))) {
  throw 'Chua co frontend/node_modules. Chay npm install trong frontend truoc.'
}

$backend = Start-Process `
  -FilePath $python `
  -ArgumentList @('-m', 'uvicorn', 'app:app', '--app-dir', 'src', '--host', '127.0.0.1', '--port', '8000') `
  -WorkingDirectory $projectRoot `
  -WindowStyle Hidden `
  -PassThru

try {
  $ready = $false
  for ($attempt = 0; $attempt -lt 40; $attempt++) {
    try {
      $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 1
      if ($health.ok) {
        $ready = $true
        break
      }
    } catch {
      Start-Sleep -Milliseconds 250
    }
  }
  if (-not $ready) {
    throw 'Backend khong khoi dong duoc tai http://127.0.0.1:8000.'
  }

  "Backend: http://127.0.0.1:8000 ($($health.retrieval))"
  "Frontend: http://127.0.0.1:5173"
  Push-Location $frontend
  try {
    npm run dev
  } finally {
    Pop-Location
  }
} finally {
  if ($backend -and -not $backend.HasExited) {
    Stop-Process -Id $backend.Id
  }
}
