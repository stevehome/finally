$Container = "finally"

docker stop $Container
docker rm $Container
Write-Host "Container stopped. Volume (data) preserved."
# Do NOT run: docker volume rm finally-data
