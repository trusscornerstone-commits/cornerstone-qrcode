[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [string]$DatabaseUrl = $env:DATABASE_URL,
  [string]$Csv = "apps/qrcode_app/trusses.csv",
  [switch]$Migrate = $true,
  [string]$Service = "django",
  [string]$LogDir = "logs"
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

if (-not (Test-Path ".\docker-compose.yml")) {
  Write-Error "docker-compose.yml não encontrado na raiz do projeto: $repoRoot"
  exit 1
}

# Paths de log
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"
$LogPath = Join-Path $LogDir "import-$timestamp.log"

function Write-Log([string]$Message) {
  $line = "[{0}] {1}" -f (Get-Date -Format "s"), $Message
  $line | Tee-Object -FilePath $LogPath -Append | Out-Null
  Write-Host $line
}

function Invoke-LoggedCommand([string]$exe, [string[]]$args) {
  Write-Log ("RUN: {0} {1}" -f $exe, ($args -join " "))
  & $exe @args 2>&1 | Tee-Object -FilePath $LogPath -Append
  if ($LASTEXITCODE -ne $null -and $LASTEXITCODE -ne 0) {
    throw "Command failed with exit code $LASTEXITCODE: $exe"
  }
}

# Verifica docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker não encontrado no PATH."
  exit 1
}

# DATABASE_URL (Render)
if (-not $DatabaseUrl) {
  $DatabaseUrl = Read-Host "Informe a DATABASE_URL do Render (inclua ?sslmode=require)"
}
if ($DatabaseUrl -notmatch "sslmode=require") {
  Write-Log "WARN: sua DATABASE_URL não contém 'sslmode=require'. No Render, isso é recomendado/necessário."
}

# Confere CSV (no host; no container deve estar montado conforme compose)
if (-not (Test-Path $Csv)) {
  Write-Log "ERRO: CSV não encontrado no host: $Csv"
  exit 1
}

Write-Log "Início do import (Compose)"
Write-Log "Repo:   $repoRoot"
Write-Log "CSV:    $Csv"
Write-Log "Serviço: $Service"
try {
  # Sobe o serviço se necessário (semçaída, só garante imagem/volumes)
  Invoke-LoggedCommand "docker" @("compose","pull",$Service)
  Invoke-LoggedCommand "docker" @("compose","build",$Service)

  if ($Migrate) {
    if ($PSCmdlet.ShouldProcess("container:$Service", "migrate --noinput")) {
      Write-Log "Rodando migrations no container..."
      Invoke-LoggedCommand "docker" @("compose","run","--rm","-e","DATABASE_URL=$DatabaseUrl",$Service,"python","manage.py","migrate","--noinput")
    }
  }

  if ($PSCmdlet.ShouldProcess("container:$Service", "import_trusses")) {
    Write-Log "Importando trusses no container..."
    Invoke-LoggedCommand "docker" @("compose","run","--rm","-e","DATABASE_URL=$DatabaseUrl",$Service,"python","manage.py","import_trusses","--csv",$Csv)
  }

  Write-Log "Concluído com sucesso."
  Write-Host "`nLog salvo em: $LogPath" -ForegroundColor Green
} catch {
  Write-Log ("FALHA: {0}" -f $_.Exception.Message)
  Write-Host "`nLog salvo em: $LogPath" -ForegroundColor Yellow
  exit 1
}