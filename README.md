# Система управления кондитерским цехом

Веб-приложение для управления заказами, складом, расписанием операций и ресурсами производства.

## Текущий стек

- Сервер: `Python + FastAPI`
- БД: `PostgreSQL`
- ORM: `SQLAlchemy`
- Миграции: `Alembic`
- Клиент: `JavaScript + HTML + CSS` (без TypeScript)

## Основной функционал

- Авторизация (базовый вход)
- CRUD заказов
- Автогенерация операций по рецепту при создании/обновлении заказа
- Автопересчет статусов заказов (`Запланирован` / `В работе` / `Выполнен`)
- Склад: ингредиенты, приход, срок годности
- Календарь операций по дням месяца
- Технологические карты изделий
- Настройки сотрудников и оборудования (статусы, удаление)
- Запуск планирования отдельным API: `POST /api/planning/run`

## Быстрый запуск

### 1. PostgreSQL

Создайте базу:

```sql
CREATE DATABASE confectionery;
```

### 2. Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:DATABASE_URL="postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/confectionery"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Проверка backend: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 3. Frontend

В корне проекта:

```powershell
python -m http.server 8080
```

Открыть: [http://127.0.0.1:8080](http://127.0.0.1:8080)

## Структура данных

Ключевые сущности:

- `ingredients`
- `equipment`
- `employees`
- `products`
- `recipes`
- `orders`
- `operations`

## API (кратко)

- `POST /api/auth/login`
- `GET/POST /api/ingredients`
- `POST /api/ingredients/{id}/receive`
- `GET/PATCH/DELETE /api/equipment/{id}`
- `GET/POST/PATCH/DELETE /api/employees/{id}`
- `GET /api/products`
- `GET /api/recipes`
- `GET/POST/PUT/DELETE /api/orders`
- `GET /api/operations`
- `POST /api/planning/run`
- `GET /api/schedule/{date}`
