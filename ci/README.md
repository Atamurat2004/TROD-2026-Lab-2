# CI/CD (GitHub Actions)

Пайплайн в корне репозитория:

- `.github/workflows/ci.yml` — рабочий workflow
- `github-ci.yml` — копия того же файла (резерв)

Настройки lint/test: `app/pyproject.toml`, `app/requirements-dev.txt`.

Секреты в GitHub → Settings → Secrets: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`. Образ на Docker Hub: `username/lab2-app` (переопределить: Variables → `DOCKER_IMAGE_NAME`).
