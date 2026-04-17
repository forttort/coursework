# Loader

Следующий этап после парсера и MVP-сайта.

## Текущее состояние
В репозитории уже есть реализация:
- `loader/load_rinkan_to_postgres.py`

## Цель
Сделать загрузчик, который переносит данные из JSON парсера в PostgreSQL.

## Целевой файл
- `loader/load_rinkan_to_postgres.py`
- `loader/refresh_product_statuses.py`

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
5. в режиме `full` помечать товары, которых нет в текущем полном импорте, как `missing`

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

## Режимы работы

### `incremental`
- только вставляет новые товары
- обновляет уже существующие
- не трогает остальные записи

Подходит для `new-arrivals` и ежедневных обновлений.

### `full`
- делает тот же upsert
- дополнительно помечает отсутствующие в текущем полном импорте товары как `missing`

Подходит для редкого полного прогона каталога.

## Поля трекинга в `products`
В таблице теперь есть:
- `status`
- `first_seen_at`
- `last_seen_at`
- `last_checked_at`
- `last_seen_in_listing_at`
- `sold_at`

Это нужно, чтобы потом различать:
- новые товары
- давно известные товары
- товары, пропавшие из полного импорта

## Как запускать

```bash
cd /Users/danil/coursework
source .venv/bin/activate
python loader/load_rinkan_to_postgres.py \
  --input /Users/danil/coursework/rinkan_products_v4.json \
  --dsn "postgresql://postgres:postgres@localhost:5432/coursework" \
  --mode incremental
```

Если база уже создана по старой версии схемы, сначала нужно прогнать:
- `sql/alter_products_tracking.sql`

## Refresh статусов

Отдельный скрипт:
- `loader/refresh_product_statuses.py`

Он проверяет product pages и обновляет статусы в БД.

Пример запуска:

```bash
cd /Users/danil/coursework
source .venv/bin/activate
python loader/refresh_product_statuses.py \
  --dsn "postgresql://danil@localhost:5432/coursework" \
  --limit 100 \
  --delay 0.2 \
  --statuses active,missing
```

Для `RINKAN` основной текущий sold-out marker:
- disabled-кнопка с текстом `在庫なし`

## Daily wrappers

Для удобства добавлены:
- `run_loader_incremental.py`
- `run_refresh_statuses.py`
- `run_daily_update.py`
