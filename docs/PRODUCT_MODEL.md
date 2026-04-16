# PRODUCT MODEL

Актуальная модель товара состоит из двух уровней:

1. JSON-структура парсера
2. Нормализованная модель БД в `sql/schema_v2.sql`

## 1. JSON-структура парсера

Парсер `RINKAN` сейчас отдает товар в таком виде:
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

## 2. Нормализованная модель БД

## Справочники

### `general_categories`
- `id`
- `name`

### `categories`
- `id`
- `general_category_id`
- `name`

### `subcategories`
- `id`
- `category_id`
- `name`

### `brands`
- `id`
- `name`

### `conditions`
- `id`
- `name`

### `genders`
- `id`
- `name`

### `sources`
- `id`
- `name`
- `base_url`

### `currencies`
- `id`
- `code`
- `name`

## Основная таблица

### `products`
- `id`
- `title`
- `brand_id`
- `gender_id`
- `subcategory_id`
- `condition_id`
- `source_id`
- `currency_id`
- `source_product_id`
- `size_label`
- `measurements_text`
- `price_original`
- `price_rub`
- `delivery_estimate`
- `description`
- `product_url`
- `main_image_url`
- `parsed_at`
- `created_at`
- `updated_at`

Важно:
- поля `size` в актуальной схеме больше нет
- вместо него используются `size_label` и `measurements_text`

## Изображения товара

### `product_images`
- `id`
- `product_id`
- `image_url`
- `position`

## Основные связи
- `categories -> general_categories`
- `subcategories -> categories`
- `products -> brands`
- `products -> genders`
- `products -> subcategories`
- `products -> conditions`
- `products -> sources`
- `products -> currencies`
- `product_images -> products`

## Правило уникальности товара
Товар должен быть уникален по паре:
- `source_id`
- `source_product_id`
