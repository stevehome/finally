$ErrorActionPreference = "Stop"

$ContainerName = "finally"
$ImageName = "finally"
$Port = 8000

# Build if image doesn't exist or -Build flag passed
$NeedsBuild = $false
if ($args -contains "--build") { $NeedsBuild = $true }
$existing = docker image inspect $ImageName 2>&1
if ($LASTEXITCODE -ne 0) { $NeedsBuild = $true }

if ($NeedsBuild) {
    Write-Host "Building Docker image..."
    docker build -t $ImageName .
}

# Stop existing container if running
docker rm -f $ContainerName 2>$null | Out-Null

# Run container
Write-Host "Starting FinAlly..."
docker run -d `
    --name $ContainerName `
    -p "${Port}:8000" `
    -v "finally-data:/app/db" `
    --env-file .env `
    $ImageName

Write-Host ""
Write-Host "FinAlly is running at http://localhost:$Port"
Write-Host ""

# Open browser
Start-Process "http://localhost:$Port"
