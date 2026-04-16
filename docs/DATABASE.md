# DATABASE

Описание актуальной структуры базы данных проекта.

## Основная схема
Текущая рабочая схема находится в `sql/schema_v2.sql`.

Файл `sql/schema.sql` можно считать ранней версией.

## Справочники

### `general_categories`
Верхний уровень общих категорий.

### `categories`
Второй уровень категорий, связан с `general_categories`.

### `subcategories`
Третий уровень категорий, связан с `categories`.

### `brands`
Справочник брендов.

### `conditions`
Справочник рангов состояния товара.

### `genders`
Справочник пола / gender label.

### `sources`
Справочник источников данных, например `RINKAN`.

### `currencies`
Справочник валют.

## Основные таблицы

### `products`
Основная таблица товаров.

Ключевые поля:
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

Уникальность товара:
- `UNIQUE (source_id, source_product_id)`

### `product_images`
Хранит дополнительные изображения товара.

Ключевые поля:
- `product_id`
- `image_url`
- `position`

## Логика загрузки данных
После появления loader загрузка должна работать так:

1. upsert в справочники
2. upsert в `products`
3. пересоздание или синхронизация `product_images` для товара

## Что ещё не реализовано в коде
- реальное подключение backend к PostgreSQL
- миграции
- начальное заполнение справочников
