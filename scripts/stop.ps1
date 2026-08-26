$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location "$PSScriptRoot\.."
Write-Host "Stopping Mem0 Local Server..." -ForegroundColor Yellow
docker compose down
Write-Host "Container stopped." -ForegroundColor Green
