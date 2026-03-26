$ErrorActionPreference = "Stop"

$ContainerName = "finally"

$result = docker rm -f $ContainerName 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "FinAlly stopped."
} else {
    Write-Host "FinAlly is not running."
}
