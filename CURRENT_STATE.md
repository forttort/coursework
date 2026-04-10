# CURRENT STATE

Актуальное состояние проекта на текущий момент.

## Что уже сделано

### 1. Парсер RINKAN
В репозитории есть рабочий парсер `parser/rinkan_parser_v4.py`.

Он извлекает:
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

### 2. Схема базы данных v2
Для новой структуры данных добавлена схема `sql/schema_v2.sql`.

В ней учтены:
- 3 уровня категорий
- genders
- condition ranks
- size_label
- measurements_text
- products + product_images

### 3. Документация по схеме
Добавлен файл `docs/DB_SCHEMA_V2.md` с mapping парсера в БД.

### 4. MVP сайта
Добавлен минимальный просмотр каталога без сложной верстки:
- `backend/main.py`
- `backend/requirements.txt`
- `frontend/index.html`
- `frontend/product.html`
- `frontend/app.js`
- `frontend/product.js`
- `frontend/styles.css`
- `data/products.sample.json`

## Что умеет MVP сайта
- открыть каталог товаров
- получить список товаров из API
- фильтровать по общей категории
- искать по названию и бренду
- открыть простую страницу товара
- посмотреть изображения и базовые поля

## Что еще не сделано
- loader JSON -> PostgreSQL
- подключение сайта к реальной БД
- price_rub
- delivery_estimate
- нормальная верстка
- полноценные фильтры
- backend для real database queries

## Следующий шаг
Следующий логичный этап:
- сделать `loader/load_rinkan_to_postgres.py`
- наполнить PostgreSQL данными из JSON
- перевести backend с sample JSON на запросы к БД
