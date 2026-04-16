# PARSER

Описание текущего парсера первого источника.

## Текущий источник
Первый реализованный источник — `RINKAN`.

Файл парсера:
- `parser/rinkan_parser_v4.py`

## Что делает парсер
- получает ссылки на товары со страниц листинга
- ходит в карточки товаров
- извлекает структуру товара
- сохраняет результат в JSON

## Извлекаемые поля
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

## CLI-параметры
Парсер сейчас принимает:
- `--start-url`
- `--pages`
- `--limit`
- `--delay`
- `--output`

Пример запуска:
```bash
python parser/rinkan_parser_v4.py \
  --start-url "https://www.rinkan-online.com/collections/all" \
  --pages 1 \
  --limit 20 \
  --delay 1.0 \
  --output rinkan_products_v7.json
```

## Важное замечание по naming
В репозитории есть небольшая несинхронность:
- файл называется `rinkan_parser_v4.py`
- внутри help и default output уже используют `v7`

Это не мешает коду работать, но требует приведения к одному виду.

## Что особенно важно в логике парсера
- `general_category_name` вычисляется отдельно
- картинки собираются из нескольких источников в HTML
- карточка использует structured data из `__NUXT_DATA__`
- `source_product_id` — ключевой внешний идентификатор товара

## Что ещё не хватает
- автоматической загрузки результата в PostgreSQL
- тестов на стабильность парсинга
- единого формата версионирования parser output
