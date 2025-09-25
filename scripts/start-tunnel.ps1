# Sobe o serviço django via Docker Compose e abre o Cloudflare Tunnel.

$ErrorActionPreference = "Stop"
$PORT = 8000

# 1) Sobe/reinicia o serviço django
Write-Host ">> Subindo serviço 'django' com Docker Compose..." -ForegroundColor Cyan
docker compose up -d django

# (Opcional) Se você usa Gunicorn e mudou código/variáveis:
# docker compose restart django

# 2) Verifica cloudflared
$cfCmd = Get-Command cloudflared -ErrorAction SilentlyContinue
$cloudflared = $cfCmd?.Source
if (-not $cloudflared) { $cloudflared = "C:\Program Files\Cloudflare\Cloudflared\cloudflared.exe" }
if (-not (Test-Path $cloudflared)) {
  Write-Error "cloudflared não encontrado. Instale com: winget install Cloudflare.cloudflared"
  exit 1
}

# 3) Abre o túnel para a porta exposta localmente
Write-Host ">> Abrindo túnel Cloudflare (http2 + IPv4) para http://localhost:$PORT ..." -ForegroundColor Green
& $cloudflared tunnel --url "http://localhost:$PORT" --protocol http2 --edge-ip-version 4