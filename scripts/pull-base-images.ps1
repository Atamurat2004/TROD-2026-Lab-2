# Базовые образы для docker compose build (запустите при стабильном интернете).
docker pull python:3.12-slim
docker pull nginx:1.27-alpine
docker pull postgres:17.5-alpine3.21
Write-Host "OK. Теперь: docker compose up --build"
