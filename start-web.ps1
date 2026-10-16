param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Chua co .venv. Tao venv va cai requirements-web.txt theo README.'
}
& $python -m uvicorn web_backend:app --host 127.0.0.1 --port $Port
