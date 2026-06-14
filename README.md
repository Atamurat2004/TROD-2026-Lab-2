# Lab-2: Sports Store + Docker + CI/CD

Полная копия **lab-1** для отдельного репозитория: код, Docker, тесты и пайплайн в одной папке.

При создании нового репозитория залейте **содержимое этой папки** (`lab-2/*`) в **корень** репо — не саму папку `lab-2`, а файлы внутри неё.

## Структура

```text
<корень нового репо>/
├── app/
├── db/
├── nginx/
├── ci/                          # копия workflow (опционально)
├── .github/workflows/ci.yml     # GitHub Actions (CI)
├── docker-compose.yml
├── .env.example
└── README.md
```

**CI/CD:** `.github/workflows/ci.yml`. Секреты в GitHub: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

## Быстрый старт

1) Создай `.env`:

```powershell
Copy-Item .env.example .env
```

2) Запусти систему:

```bash
docker compose up --build
```

Если ошибка `auth.docker.io ... TLS handshake timeout` (нестабильная сеть до Docker Hub):

```powershell
# 1) Скачать базовые образы, когда интернет стабилен
.\scripts\pull-base-images.ps1

# 2) В .env должно быть COMPOSE_BAKE=false (см. .env.example)

# 3) Сборка без повторной загрузки базовых образов
docker compose build --pull=false
docker compose up -d

# Запасной вариант (классический builder)
$env:DOCKER_BUILDKIT = "0"
docker compose build --pull=false
docker compose up -d
```

3) Открой (весь HTTP идёт через **nginx**, приложение снаружи не слушает порт `8000`):

- Web UI: `http://localhost:8080/`
- API docs: `http://localhost:8080/docs`
- Liveness: `http://localhost:8080/health/live`
- Readiness: `http://localhost:8080/health/ready`

Порт хоста задаётся в `docker-compose.yml` (`8080:80`). При необходимости замени `8080` на другой свободный порт.

## API Demo Script (товары спорт-магазина)

### 1. Добавить товар

```bash
curl -X POST http://localhost:8080/products \
  -H "Content-Type: application/json" \
  -d '{
        "title":"Nike Running Shoes",
        "description":"Footwear",
        "priority":2,
        "status":"todo"
      }'
```

`status` значения:

- `todo` = `in_stock`
- `in_progress` = `low_stock`
- `done` = `out_of_stock`

### 2. Получить список товаров

```bash
curl "http://localhost:8080/products?limit=10&offset=0"
```

### 3. Поиск/фильтрация

```bash
curl "http://localhost:8080/products?status=todo&search=Nike"
```

### 4. Частично обновить товар (PATCH)

```bash
curl -X PATCH http://localhost:8080/products/1 \
  -H "Content-Type: application/json" \
  -d '{"status":"in_progress"}'
```

### 5. Удалить товар

```bash
curl -i -X DELETE http://localhost:8080/products/1
```

## Локальные тесты и линтер (как в CI)

Из каталога `app/` (в корне нового репо):

```powershell
cd app
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
ruff format --check .
pytest --cov=src --cov-report=term --cov-fail-under=50
```

Полный стек: `docker compose up --build` из корня репозитория.

Подробнее про пайплайн и выгрузку в отдельный репозиторий: [ci/README.md](ci/README.md).

## Остановка

```bash
docker compose down
```

Полная очистка (включая данные БД):

```bash
docker compose down -v
```
