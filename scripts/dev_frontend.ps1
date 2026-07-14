# Local frontend dev server (proxies API via NEXT_PUBLIC_API_BASE)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\frontend"
$env:NEXT_PUBLIC_API_BASE = "http://localhost:8000"
npm.cmd run dev
