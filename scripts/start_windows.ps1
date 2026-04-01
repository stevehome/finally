param([switch]$Build)

$Image = "finally"
$Container = "finally"
$Volume = "finally-data"
$Port = 8000
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Build if image missing or -Build flag passed
$imageExists = docker image inspect $Image 2>$null
if ($Build -or -not $imageExists) {
    Write-Host "Building image..."
    docker build -t $Image $ProjectRoot
}

# Stop and remove existing container (idempotent)
docker rm -f $Container 2>$null

# Run container
docker run -d `
    --name $Container `
    -p "${Port}:${Port}" `
    -v "${Volume}:/app/db" `
    --env-file "$ProjectRoot\.env" `
    $Image

Write-Host "FinAlly running at http://localhost:$Port"
Start-Sleep 2
Start-Process "http://localhost:$Port"
