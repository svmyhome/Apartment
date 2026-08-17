# Renovation Planner — Web

Web-клиент проекта Renovation Planner. Это приложение на React, TypeScript и
Vite, которое на временной странице проверяет доступность backend API через
`GET /api/v1/health`.

## Локальный запуск

Нужны Node.js и запущенный backend API. Рекомендуемая версия Node.js — 24 LTS
или новее.

Из корня репозитория:

```bash
cd frontend
cp .env.example .env.local
npm ci
npm run dev
```

После запуска открыть <http://localhost:5173>. Для успешной проверки API
должен быть доступен по адресу <http://localhost:8000>.

## Переменные окружения

Файл `frontend/.env.local` предназначен для локальных значений и не попадает в
Git. Его шаблон находится в [`.env.example`](.env.example).

```dotenv
VITE_API_URL=http://localhost:8000
```

Vite передаёт в браузер только переменные с префиксом `VITE_`. Эти значения
видны пользователю приложения, поэтому пароли, токены и другие секреты в них
хранить нельзя. После изменения `.env.local` перезапустите `npm run dev`.

Backend разрешает запросы с origin `http://localhost:5173` через CORS. Если
Vite запускается на другом адресе или порте, добавьте этот origin в
`CORS_ALLOWED_ORIGINS` у backend и перезапустите API.

## Проверки

```bash
cd frontend
npm run lint
npm run build
```

`npm run build` создаёт production-сборку в `frontend/dist`. Каталог `dist` —
результат сборки и не коммитится.

## Запуск через Docker Compose

Из корня репозитория:

```bash
docker compose up --build -d
```

Compose поднимет PostgreSQL, API и Vite-сервис `web`. Откройте
<http://localhost:5173>. Логи web-клиента можно посмотреть командой:

```bash
docker compose logs --tail=100 web
```

## Связанная документация

- [Общий план проекта](../plan/PLAN.MD)
- [Этап 1.2: собрать основу](../plan/1.2-СОБРАТЬ-ОСНОВУ.MD)
- [Контракт API](../plan/API.MD)
