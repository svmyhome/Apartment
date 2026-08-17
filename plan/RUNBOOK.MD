# Runbook: конфигурация, запуск и проверки

Этот документ собирает рабочие команды проекта Renovation Planner в одном
месте. Он описывает локальную разработку и тесты. Полноценное production
развёртывание пока не реализовано: текущий сервис `web` запускает Vite в режиме
разработки с hot reload, а не production-сервер.

Для истории и создания миграций используйте [ALEMBIC.MD](ALEMBIC.MD). Для
детального чек-листа реализации — [1.2-СОБРАТЬ-ОСНОВУ.MD](1.2-СОБРАТЬ-ОСНОВУ.MD).

## 1. Требования

- Docker Desktop с работающим Docker Compose;
- Python 3.13 и `uv` для запуска тестов и Alembic на хосте;
- Node.js 24 LTS и npm — только для запуска frontend вне Docker.

Все команды ниже выполняются из корня репозитория, если не указано обратное.

## 2. Первоначальная настройка

Создайте локальный файл окружения из шаблона:

```bash
cp .env.example .env
```

Основные значения в `.env`:

| Переменная | Назначение |
| --- | --- |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Основная PostgreSQL БД для локальной разработки. |
| `CORS_ALLOWED_ORIGINS` | Разрешённые адреса браузерного клиента. По умолчанию `http://localhost:5173`. |
| `TEST_DB_NAME`, `TEST_DB_USER`, `TEST_DB_PASSWORD`, `TEST_DB_PORT` | Отдельный контейнер PostgreSQL для интеграционных тестов. |
| `TEST_DATABASE_URL` | Строка подключения тестов; экспортируется в терминал перед запуском и должна оканчиваться на `_test`. |

`.env` содержит локальные пароли и не должен попадать в Git.

## 3. Локальный запуск через Docker Compose

Запустите основную БД, API и web-клиент:

```bash
docker compose up --build -d
docker compose ps
```

Ожидаемые сервисы: `apartment_db` со статусом `healthy`, а также `api` и `web`.

Проверьте API:

```bash
curl -i http://localhost:8000/api/v1/health
```

Ожидается `200 OK` и тело `{"status":"ok"}`. Затем откройте
<http://localhost:5173>; страница `Renovation Planner` должна показать «API
доступен».

Полезные команды диагностики:

```bash
docker compose logs --tail=100 api
docker compose logs --tail=100 web
docker compose logs --tail=100 apartment_db
```

Остановить окружение без удаления данных:

```bash
docker compose down
```

`docker compose down -v` удаляет volume основной БД и её данные. Применяйте его
только для полностью локального окружения, когда данные не нужны.

## 4. Локальный запуск frontend без Docker

Сначала запустите API и основную БД через Compose:

```bash
docker compose up -d apartment_db api
```

Затем в отдельном терминале:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

Откройте <http://localhost:5173>. Изменения `.env.local` применяются только
после перезапуска Vite. В `VITE_API_URL` нельзя хранить секреты: Vite передаёт
такие переменные в браузер.

## 5. Unit-тесты и проверки кода

Эти команды не требуют PostgreSQL:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest -m "not integration"
uv run python -c "from backend.app.main import app; assert app"
```

Проверки frontend:

```bash
cd frontend
npm run lint
npm run build
```

Production-сборка frontend создаётся в `frontend/dist`; это генерируемый
каталог, его не нужно коммитить.

## 6. Интеграционные тесты с отдельной БД

Тестовая БД запускается отдельным Compose-профилем и использует другой порт:

```bash
docker compose --profile test up -d apartment_test_db
docker compose ps
```

Сформируйте URL из значений `.env` и экспортируйте его в текущий терминал. Для
значений шаблона команда выглядит так:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://postgres:postgres@127.0.0.1:5433/apartment_test'
uv run pytest -m integration
uv run alembic current
uv run alembic check
```

Интеграционные тесты и Alembic откажутся работать, если имя БД в URL не
оканчивается на `_test`. Это защита основной БД от случайных тестовых миграций
и очистки.

После тестов можно остановить только тестовую БД:

```bash
docker compose --profile test stop apartment_test_db
```

Чтобы удалить только данные тестовой БД, остановите её и найдите имя её volume:

```bash
docker compose --profile test stop apartment_test_db
docker volume ls | rg 'pg_test_data'
```

Проверьте найденное имя: для стандартного имени Compose оно будет
`apartment_pg_test_data`. Только после такой проверки удалите именно его:

```bash
docker volume rm apartment_pg_test_data
```

Не используйте для этой цели `docker compose down -v`: эта команда может
удалить volume основной БД вместе с тестовым. После работы можно выполнить
`unset TEST_DATABASE_URL`.

## 7. Миграции основной БД

При запущенной основной БД:

```bash
uv run alembic upgrade head
uv run alembic current
uv run alembic check
```

Не запускайте эти команды с `TEST_DATABASE_URL`, если хотите проверить основную
БД. Полный цикл создания, проверки и отката миграций описан в
[ALEMBIC.MD](ALEMBIC.MD).

## 8. Production: текущее ограничение и следующий шаг

`frontend/Dockerfile` и сервис `web` предназначены только для разработки:
они запускают `npm run dev`, монтируют исходный код и используют Vite. Их нельзя
считать production-развёртыванием.

Перед первым production-деплоем нужно:

1. Собрать frontend через `npm ci && npm run build`.
2. Создать отдельный production-образ, который раздаёт `frontend/dist`
   статическим сервером (например, Nginx) и не содержит исходный код или Vite
   dev server.
3. Передать публичный адрес API как `VITE_API_URL` на этапе сборки frontend;
   переменная встраивается в браузерный bundle и не подходит для секретов.
4. Задать уникальные production-пароли и не хранить `.env` в репозитории.
5. Ограничить `CORS_ALLOWED_ORIGINS` реальными HTTPS-адресами frontend, без `*`.
6. Настроить HTTPS, резервное копирование PostgreSQL, мониторинг health-check и
   запуск миграций в контролируемом шаге релиза.

Пока эти пункты не реализованы, используйте Compose только как локальное
development-окружение.

## 9. CI

Workflow GitHub Actions ещё не создан. План его реализации находится в разделе
8 файла [1.2-СОБРАТЬ-ОСНОВУ.MD](1.2-СОБРАТЬ-ОСНОВУ.MD): backend job должен
запускать Ruff, unit- и интеграционные тесты с изолированной PostgreSQL, а
frontend job — `npm ci`, линтинг и production-сборку.
