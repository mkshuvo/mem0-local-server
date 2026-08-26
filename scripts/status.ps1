Write-Host "Checking Mem0 Local Server status (port 28842)..." -ForegroundColor Cyan
try {
    $res = Invoke-RestMethod -Uri "http://localhost:28842/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "Server is ONLINE and HEALTHY" -ForegroundColor Green
    $stats = Invoke-RestMethod -Uri "http://localhost:28842/api/v1/stats"
    Write-Host "Metrics:" -ForegroundColor Cyan
    $stats | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Server is OFFLINE or unreachable on port 28842" -ForegroundColor Red
    docker ps -a --filter name=mem0-local-server
}
