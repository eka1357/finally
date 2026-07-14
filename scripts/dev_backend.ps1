# Local backend dev server
$Root = Split-Path -Parent $PSScriptRoot
Set-Location "$Root\backend"
if (Test-Path "$Root\.env") {
  Get-Content "$Root\.env" | ForEach-Object {
    if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
    $p = $_.Split('=', 2)
    [System.Environment]::SetEnvironmentVariable($p[0].Trim(), $p[1].Trim(), "Process")
  }
}
$env:DB_PATH = "$Root\db\finally.db"
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
