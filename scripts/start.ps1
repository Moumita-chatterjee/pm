$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

docker build -t pm-app .
docker rm -f pm-app 2>$null | Out-Null
New-Item -ItemType Directory -Force -Path data | Out-Null

$envFileArgs = @()
if (Test-Path .env) {
    $envFileArgs = @("--env-file", ".env")
}

docker run -d --name pm-app -p 8000:8000 @envFileArgs -v "${PWD}/data:/app/data" pm-app

Write-Host "Running at http://localhost:8000"
