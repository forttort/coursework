# DB Schema v2

Актуальная схема базы для загрузки данных из RINKAN-парсера находится в `sql/schema_v2.sql`.

## Что изменилось

По сравнению с первой версией схемы добавлены:
- третий уровень категорий: `general_categories -> categories -> subcategories`
- таблица `genders`
- в `products` вместо общего `size` теперь используются:
  - `size_label`
  - `measurements_text`
- `conditions.name` хранит ранги состояния (`N`, `S`, `A`, `B`, `C`, `D` и т.д.)

## Как маппить поля парсера

Парсер RINKAN сейчас отдает такие ключевые поля:
- `brand_name`
- `gender_label`
- `general_category_name`
- `category_name`
- `subcategory_name`
- `condition_rank`
- `size_label`
- `measurements_text`
- `price_original`
- `currency_code`
- `description`
- `product_url`
- `main_image_url`
- `image_urls`
- `parsed_at`
- `source_product_id`

### Mapping в reference tables
- `general_category_name` -> `general_categories.name`
- `category_name` -> `categories.name`
- `subcategory_name` -> `subcategories.name`
- `brand_name` -> `brands.name`
- `gender_label` -> `genders.name`
- `condition_rank` -> `conditions.name`
- `currency_code` -> `currencies.code`
- source `RINKAN` -> `sources.name`

### Mapping в products
- `title` -> `products.title`
- `source_product_id` -> `products.source_product_id`
- `size_label` -> `products.size_label`
- `measurements_text` -> `products.measurements_text`
- `price_original` -> `products.price_original`
- `description` -> `products.description`
- `product_url` -> `products.product_url`
- `main_image_url` -> `products.main_image_url`
- `parsed_at` -> `products.parsed_at`
- import timestamp -> `products.first_seen_at` при первой вставке
- import timestamp -> `products.last_seen_at`
- import timestamp -> `products.last_checked_at`
- import timestamp -> `products.last_seen_in_listing_at`
- status active -> `products.status`

### Mapping в product_images
- `image_urls[]` -> `product_images.image_url`
- индекс в массиве + 1 -> `product_images.position`

## Важное ограничение

Уникальность товара обеспечивается через:
- `products(source_id, source_product_id)`

Это значит, что loader должен делать upsert по паре:
- source = `RINKAN`
- source_product_id = внешний id товара

## Поля трекинга доступности

В `products` добавлены поля:
- `status`
- `first_seen_at`
- `last_seen_at`
- `last_checked_at`
- `last_seen_in_listing_at`
- `sold_at`

Задумка такая:
- `active` — товар найден в текущем импорте
- `missing` — товар отсутствует в полном импорте, но еще не подтвержден как проданный
- `sold` — товар явно подтвержден как проданный отдельной проверкой карточки
- `unknown` — промежуточный или служебный статус, если понадобится позже

Это позволяет потом строить отдельный процесс:
- быстрый daily import для `new-arrivals`
- редкий full import
- отдельную проверку доступности уже известных карточек товара

## Следующий шаг

Следующий файл после схемы:
- `loader/load_rinkan_to_postgres.py`

Он должен:
1. читать JSON парсера
2. upsert reference tables
3. upsert `products`
4. перезаписывать `product_images` для конкретного товара
