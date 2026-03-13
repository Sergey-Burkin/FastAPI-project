# URL Shortener API

Сервис сокращения ссылок на FastAPI с JWT-аутентификацией, PostgreSQL, Redis-кешем и фоновыми задачами очистки через APScheduler.

## Возможности

- Регистрация и авторизация пользователей (JWT Bearer).
- Создание коротких ссылок (в том числе с `custom_alias`).
- Публичный редирект по короткому коду: `/{short_code}`.
- Поиск ссылок по оригинальному URL.
- Получение статистики, обновление и удаление ссылок.
- Очистка:
	- истекших ссылок (каждый час),
	- неиспользуемых ссылок старше `UNUSED_DAYS` (раз в сутки).

## Стек

- FastAPI
- SQLAlchemy (async) + asyncpg
- PostgreSQL
- Redis
- APScheduler
- python-jose (JWT)

## Структура API

Базовый префикс для версионированных маршрутов: `/v1`

### Auth

- `POST /v1/auth/register` - регистрация
- `POST /v1/auth/login` - вход и получение JWT

### Links

- `POST /v1/links/shorten` - создать короткую ссылку
- `GET /v1/links/search?original_url=...` - поиск по оригинальному URL
- `GET /v1/links/expired` - получить истекшие ссылки текущего пользователя
- `PUT /v1/links/{short_code}` - обновить исходный URL
- `DELETE /v1/links/{short_code}` - удалить ссылку
- `GET /v1/links/{short_code}/stats` - статистика ссылки

### Redirect

- `GET /{short_code}` - редирект на оригинальный URL (307)

### Service

- `GET /` - информация о сервисе

Swagger UI: `http://localhost:8000/docs`

## Примеры запросов

### 1) Регистрация

```bash
curl -X POST http://localhost:8000/v1/auth/register \
	-H "Content-Type: application/json" \
	-d '{
		"username": "demo",
		"email": "demo@example.com",
		"password": "strong-password"
	}'
```

### 2) Логин (получение токена)

```bash
curl -X POST http://localhost:8000/v1/auth/login \
	-H "Content-Type: application/x-www-form-urlencoded" \
	-d "username=demo&password=strong-password"
```

Ответ:

```json
{
	"access_token": "<JWT_TOKEN>",
	"token_type": "bearer"
}
```

### 3) Создать короткую ссылку

```bash
curl -X POST http://localhost:8000/v1/links/shorten \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer <JWT_TOKEN>" \
	-d '{
		"original_url": "https://example.com/some/very/long/path",
		"custom_alias": "myalias",
		"expires_at": "2026-12-31T23:59:59"
	}'
```

### 4) Редирект по короткому коду

```bash
curl -i http://localhost:8000/myalias
```

### 5) Статистика ссылки

```bash
curl -X GET http://localhost:8000/v1/links/myalias/stats
```

### 6) Поиск по оригинальному URL

```bash
curl "http://localhost:8000/v1/links/search?original_url=example.com"
```

### 7) Обновить ссылку

```bash
curl -X PUT http://localhost:8000/v1/links/myalias \
	-H "Content-Type: application/json" \
	-H "Authorization: Bearer <JWT_TOKEN>" \
	-d '{
		"original_url": "https://example.org/new-path"
	}'
```

### 8) Удалить ссылку

```bash
curl -X DELETE http://localhost:8000/v1/links/myalias \
	-H "Authorization: Bearer <JWT_TOKEN>"
```

## Инструкция по запуску

### Docker Compose

1. Из корня проекта запустите:

```bash
docker-compose -f docker/docker-compose.yml up --build
```

2. API будет доступен на `http://localhost:8000`.

## Переменные окружения

Пример (`.env.example`):

```env
POSTGRES_DSN=postgresql+asyncpg://user:pass@db:5432/shortener
REDIS_DSN=redis://redis:6379/0
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
UNUSED_DAYS=30
```

## Описание БД

### PostgreSQL

Используются таблицы:

1. `users`
	 - `id` (PK)
	 - `username` (unique)
	 - `email` (unique)
	 - `hashed_password`
	 - `is_active`

2. `links`
	 - `id` (PK)
	 - `original_url`
	 - `short_code` (unique)
	 - `created_at`
	 - `expires_at` (nullable)
	 - `clicks`
	 - `last_used_at` (nullable)
	 - `is_active`
	 - `user_id` (FK -> `users.id`, nullable)

Связь: один пользователь может иметь много ссылок.

### Redis

- Кеширует пары `short_code -> original_url` (ключ формата `link:{short_code}`) на 1 час.
- Используется для ускорения редиректа.

## Коды ответов (основные)

- `201` - ссылка создана.
- `307` - успешный редирект.
- `400` - ошибка валидации/бизнес-логики.
- `401` - не авторизован.
- `403` - недостаточно прав.
- `404` - ссылка/ресурс не найден.
