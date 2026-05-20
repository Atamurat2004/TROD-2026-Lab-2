# CI/CD

Пайплайны для **отдельного** репозитория уже в корне `lab-2/`:

- `.github/workflows/ci.yml` — GitHub Actions
- `.gitlab-ci.yml` — GitLab CI

Каталог `ci/` — те же файлы (резервная копия шаблонов).

Настройки lint/test: `app/pyproject.toml`, `app/requirements-dev.txt`.

Секреты: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

Демо упавших пайплайнов (в монорепо `TROD-2026`): ветки `demo/ci-fail-lint`, `demo/ci-fail-coverage`.
