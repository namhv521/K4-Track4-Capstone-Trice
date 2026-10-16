param([Parameter(Mandatory=$true)][string]$LanIP,[int]$Port=8443,[string]$TlsDirectory='')
$ErrorActionPreference='Stop'
Set-Location $PSScriptRoot
$python=Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not $TlsDirectory) { $TlsDirectory = 'data/tls-' + $LanIP.Replace('.','-') }
$resolvedTls=[System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot $TlsDirectory))
$rootPrefix=[System.IO.Path]::GetFullPath($PSScriptRoot)+[System.IO.Path]::DirectorySeparatorChar
if (-not $resolvedTls.StartsWith($rootPrefix,[System.StringComparison]::OrdinalIgnoreCase)) { throw 'TLS directory must remain inside Trice.' }
$cert=Join-Path $resolvedTls 'server-cert.pem'
$key=Join-Path $resolvedTls 'server-key.pem'
if (-not (Test-Path -LiteralPath $cert)) {
    & $python tools/create_local_tls.py --ip $LanIP --out $resolvedTls
    if ($LASTEXITCODE -ne 0) { throw 'Could not create certificate.' }
}
Write-Host "Desktop: https://localhost:$Port ; phone: https://${LanIP}:$Port/phone.html"
Write-Host "Public CA: $(Join-Path $resolvedTls 'trice-local-ca.crt')"
Write-Host 'Requires same reachable network and manually trusted local CA. Does not change firewall or certificate trust.'
& $python -m uvicorn web_backend:app --host 0.0.0.0 --port $Port --ssl-keyfile $key --ssl-certfile $cert --no-access-log
