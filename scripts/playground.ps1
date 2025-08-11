Param()

Write-Host "==> Green CDN: Playground setup (Windows)" -ForegroundColor Green

# Move to repo root based on script path
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Join-Path $ScriptDir ".." | Resolve-Path
Set-Location $RepoRoot

# Check Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Write-Error "Docker is not installed. Please install Docker Desktop first."
  exit 1
}

# Compose shim
function Get-ComposeCommand {
  try { docker compose version | Out-Null; return 'docker compose' } catch {}
  if (Get-Command docker-compose -ErrorAction SilentlyContinue) { return 'docker-compose' }
  throw 'docker compose or docker-compose not found.'
}

$compose = Get-ComposeCommand

# Create .env if missing
if (-not (Test-Path .env)) {
  Copy-Item env_example.txt .env
  Write-Host "Created .env from env_example.txt (using demo data unless you add WattTime credentials)." -ForegroundColor Yellow
}

Write-Host "==> Building images (first run only)" -ForegroundColor Green
Invoke-Expression "$compose build"

Write-Host "==> Starting services" -ForegroundColor Green
Invoke-Expression "$compose up -d"

Start-Sleep -Seconds 3

Write-Host "`nGreen CDN is starting. Access points:" -ForegroundColor Cyan
Write-Host "- Weight Manager:     http://localhost:5000"
Write-Host "- Weight Viewer:      http://localhost:5001"
Write-Host "- HAProxy Stats:      http://localhost:8404/stats"
Write-Host "- Test Load Balancer: http://localhost:80"
Write-Host "- Historical Sim:     http://localhost:5000/historical-simulation"

Write-Host "`nTips:" -ForegroundColor Cyan
Write-Host "- For real WattTime data, set WATTTIME_USERNAME and WATTTIME_PASSWORD in .env and restart."
Write-Host "- To view logs: $compose logs -f"
Write-Host "- To stop:      $compose down"


