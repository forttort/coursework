# API

Актуальное описание backend API MVP.

## Технология
Backend реализован на `FastAPI` в `backend/main.py`.

## HTML-маршруты

### `GET /`
Возвращает страницу каталога `frontend/index.html`.

### `GET /product.html`
Возвращает страницу отдельного товара `frontend/product.html`.

Ожидаемый query-параметр на frontend:
- `id` — `source_product_id` товара

## API-маршруты

### `GET /api/health`
Простейшая проверка состояния backend.

Пример ответа:
```json
{
  "status": "ok",
  "data_source": "json"
}
```

`data_source` сейчас показывает, какой источник предпочитает backend:
- `postgresql`
- `json`

### `GET /api/products`
Возвращает список товаров из PostgreSQL, если подключение настроено.

Если БД не настроена или недоступна, backend использует fallback на `rinkan_products_v4.json`.

Поддерживаемые query-параметры:
- `q` — поиск по `title`, `brand_name`, `subcategory_name`
- `general_category` — фильтр по общей категории
- `brand` — фильтр по бренду

Пример:
```text
/api/products?q=dior&general_category=wear
```

Пример элемента ответа:
```json
{
  "title": "...",
  "source_product_id": "10519-251030-0154",
  "product_url": "...",
  "main_image_url": "...",
  "image_urls": ["..."],
  "price_original": 29900,
  "currency_code": "JPY",
  "brand_name": "DIOR",
  "gender_label": "メンズ",
  "general_category_name": "wear",
  "category_name": "shirts",
  "subcategory_name": "t-shirts",
  "condition_rank": "B",
  "size_label": "M",
  "measurements_text": "...",
  "description": "...",
  "parsed_at": "..."
}
```

### `GET /api/products/{source_product_id}`
Возвращает один товар по `source_product_id`.

Если товар не найден, backend отвечает `404`.

## Ограничения текущего API
- нет подтвержденного end-to-end прогона на локальной PostgreSQL в рамках репозитория
- нет пагинации
- нет сортировки
- нет фильтров по размеру, состоянию и полу
