# FinAlly start script (Windows PowerShell)
param(
    [switch]$Build,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Created .env from .env.example — add your API keys." -ForegroundColor Yellow
    }
}

$image = "finally"
$container = "finally-app"

$exists = docker images -q $image
if ($Build -or -not $exists) {
    Write-Host "Building Docker image..." -ForegroundColor Cyan
    docker build -t $image .
}

$running = docker ps -q -f "name=^/${container}$"
if ($running) {
    Write-Host "Container already running." -ForegroundColor Green
} else {
    $old = docker ps -aq -f "name=^/${container}$"
    if ($old) { docker rm -f $container | Out-Null }

    Write-Host "Starting FinAlly..." -ForegroundColor Cyan
    docker run -d `
        --name $container `
        -p 8000:8000 `
        -v finally-data:/app/db `
        --env-file .env `
        $image | Out-Null
}

Write-Host ""
Write-Host "FinAlly is available at http://localhost:8000" -ForegroundColor Green
if (-not $NoBrowser) {
    Start-Process "http://localhost:8000"
}
