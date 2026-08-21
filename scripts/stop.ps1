$ErrorActionPreference = "SilentlyContinue"

docker stop pm-app | Out-Null
docker rm pm-app | Out-Null

Write-Host "Stopped"
