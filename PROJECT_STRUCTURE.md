# Структура проекта

## Корень

```text
.
├── backend/
├── web/
├── index.html
├── README.md
├── PROJECT_STRUCTURE.md
├── USAGE.md
├── SCENARIOS_IMPLEMENTATION.md
├── SUMMARY.md
└── ATTRIBUTIONS.md
```

## Backend (`backend/`)

```text
backend/
├── app/
│   ├── __init__.py
│   ├── database.py      # SQLAlchemy engine/session + DATABASE_URL
│   ├── models.py        # ORM-модели таблиц
│   ├── schemas.py       # Pydantic DTO для API
│   ├── seed.py          # начальные тестовые данные
│   ├── planning.py      # сервис планирования и синхронизации статусов
│   └── main.py          # FastAPI роуты
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Frontend (`web/`)

```text
web/
├── app.js      # SPA-логика на чистом JavaScript
└── styles.css  # стили интерфейса
```

`index.html` подключает клиент:

- `/web/styles.css`
- `/web/app.js`

## Основные сущности БД

- `ingredients`
- `equipment`
- `employees`
- `products`
- `recipes`
- `orders`
- `operations`

## Ключевые API-эндпоинты

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
