# SITE MVP

## Что добавлено

Минимальный сайт для отображения данных без сложной верстки.

### Backend
- `backend/main.py`
- `backend/requirements.txt`

### Frontend
- `frontend/index.html`
- `frontend/product.html`
- `frontend/app.js`
- `frontend/product.js`
- `frontend/styles.css`

### Data source
- `rinkan_products_v4.json`

Сейчас JSON-файл содержит `10` товаров.

## Как запустить

### 1. Установить зависимости
```bash
pip install -r backend/requirements.txt
```

### 2. Запустить сервер
```bash
uvicorn backend.main:app --reload
```

### 3. Открыть в браузере
```text
http://127.0.0.1:8000
```

## Доступные маршруты

### HTML
- `/` — каталог
- `/product.html?id=<source_product_id>` — страница товара

### API
- `/api/health`
- `/api/products`
- `/api/products/{source_product_id}`

Поддерживаемые query-параметры каталога:
- `q`
- `general_category`
- `brand`

## Что сейчас использует backend
Сейчас backend читает не базу данных, а файл:
- `rinkan_products_v4.json`

Это временный этап до перевода backend на PostgreSQL.

## Что уже умеет frontend
- показать каталог
- искать по строке
- фильтровать по общей категории
- открыть карточку товара
- показать галерею изображений и описание

## Что заменить позже
После перевода backend на БД нужно:
1. заменить чтение JSON на запросы в PostgreSQL
2. добавить пагинацию
3. добавить фильтры по бренду, состоянию, размеру
4. добавить price_rub и delivery_estimate
