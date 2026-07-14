# FinAlly stop script (Windows PowerShell)
$ErrorActionPreference = "Stop"
$container = "finally-app"

$running = docker ps -q -f "name=^/${container}$"
if ($running) {
    Write-Host "Stopping FinAlly..." -ForegroundColor Cyan
    docker stop $container | Out-Null
    docker rm $container | Out-Null
    Write-Host "Stopped. Data volume 'finally-data' is preserved." -ForegroundColor Green
} else {
    $old = docker ps -aq -f "name=^/${container}$"
    if ($old) {
        docker rm $container | Out-Null
        Write-Host "Removed stopped container." -ForegroundColor Green
    } else {
        Write-Host "No FinAlly container found." -ForegroundColor Yellow
    }
}
