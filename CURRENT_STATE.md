# CURRENT STATE

Актуальное состояние репозитория на текущий момент.

## Что реально реализовано

### 1. Backend MVP
Есть минимальный backend на `FastAPI` в `backend/main.py`.

Он:
- читает товары из `data/products.sample.json`
- отдает `GET /api/health`
- отдает `GET /api/products`
- отдает `GET /api/products/{source_product_id}`
- раздает `frontend/index.html` и `frontend/product.html`

Поддерживаемые query-параметры каталога:
- `q`
- `general_category`
- `brand`

### 2. Frontend MVP
Есть 2 статические страницы:
- `frontend/index.html` — каталог
- `frontend/product.html` — карточка товара

Текущий frontend умеет:
- загрузить товары из API
- искать по строке поиска
- фильтровать по общей категории
- открывать страницу отдельного товара

### 3. Sample-данные
В `data/products.sample.json` сейчас лежит `5` товаров.

В sample присутствуют категории:
- `wear`
- `shoes`
- `bags`
- `goods`
- `accessories`

### 4. Парсер первого источника
В репозитории есть файл `parser/rinkan_parser_v4.py`.

По факту он уже парсит:
- листинг -> карточки товаров
- `title`
- `source_product_id`
- `product_url`
- `main_image_url`
- `image_urls`
- `price_original`
- `currency_code`
- `brand_name`
- `gender_label`
- `general_category_name`
- `category_name`
- `subcategory_name`
- `condition_rank`
- `size_label`
- `measurements_text`
- `description`
- `parsed_at`

### 5. Схема БД
Актуальная схема — `sql/schema_v2.sql`.

В ней уже есть:
- `general_categories`
- `categories`
- `subcategories`
- `brands`
- `conditions`
- `genders`
- `sources`
- `currencies`
- `products`
- `product_images`

Файл `sql/schema.sql` остался как более ранняя версия схемы.

## Что проверено
- `backend/main.py` компилируется
- `parser/rinkan_parser_v4.py` компилируется
- функции backend корректно читают sample JSON

## Что ещё не сделано
- loader `JSON -> PostgreSQL`
- реальное подключение backend к PostgreSQL
- API с пагинацией и сортировкой
- фильтры по бренду, состоянию, размеру и полу на frontend
- расчет `price_rub`
- поле `delivery_estimate`
- тесты для backend и parser

## Что бросается в глаза при анализе репы
- файл называется `parser/rinkan_parser_v4.py`, но внутри комментарии и CLI уже называют его `v7`
- default output у парсера сейчас `rinkan_products_v7.json`
- в корне лежит `rinkan_products_v4.json`, то есть naming сейчас не до конца синхронизирован
- backend пока использует sample JSON, а не результат loader

## Следующий практический шаг
1. Привести naming парсера к одному виду
2. Написать `loader/load_rinkan_to_postgres.py`
3. Залить данные в PostgreSQL по `sql/schema_v2.sql`
4. Перевести backend на работу с БД
