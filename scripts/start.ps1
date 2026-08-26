$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$PSScriptRoot\.."
Write-Host "Starting Mem0 Local Server..." -ForegroundColor Cyan
docker compose up -d --build
Write-Host "Waiting for server healthcheck..." -ForegroundColor Yellow
$healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $res = Invoke-RestMethod -Uri "http://localhost:28842/health" -TimeoutSec 2 -ErrorAction Stop
        if ($res.status -eq "ok" -or $res.status -eq "healthy") {
            Write-Host "Mem0 Local Server is live and healthy at http://localhost:28842" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $healthy) {
    Write-Host "Server started but healthcheck took longer than expected. Run docker compose logs -f to inspect." -ForegroundColor Red
}
