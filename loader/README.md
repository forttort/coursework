# Loader

Следующий этап после парсера и MVP-сайта.

## Текущее состояние
На момент обновления документации loader еще не реализован.

## Цель
Сделать загрузчик, который переносит данные из JSON парсера в PostgreSQL.

## Целевой файл
- `loader/load_rinkan_to_postgres.py`

## Что должен делать loader
1. читать JSON-файл с результатом парсера
2. upsert в справочники:
   - `general_categories`
   - `categories`
   - `subcategories`
   - `brands`
   - `genders`
   - `conditions`
   - `sources`
   - `currencies`
3. upsert в `products`
4. обновлять `product_images`

## База для реализации
- схема: `sql/schema_v2.sql`
- mapping: `docs/DB_SCHEMA_V2.md`

## Важная логика
Товар должен определяться уникально через:
- `source_id`
- `source_product_id`

То есть для RINKAN loader должен делать upsert по паре:
- source = `RINKAN`
- source_product_id = внешний id товара
