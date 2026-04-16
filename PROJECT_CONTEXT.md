# PROJECT CONTEXT

## Название проекта
Веб-каталог fashion-товаров с японских площадок.

## Цель
Сделать учебный прототип каталога, который показывает товары fashion-сегмента, собранные с японских сайтов, и позволяет:
- смотреть каталог
- искать товары
- фильтровать их
- открывать подробную страницу товара

## Текущий выбранный источник
Для первой рабочей версии зафиксирован источник `RINKAN`.

Именно под него сейчас уже есть:
- парсер
- sample JSON
- схема БД v2
- MVP сайта

## Текущая архитектура

### Сейчас
`RINKAN parser -> JSON -> FastAPI backend -> static frontend`

### Целевая архитектура
`RINKAN parser -> loader -> PostgreSQL -> FastAPI API -> frontend`

## Текущая предметная область
Основные группы товаров:
- одежда
- обувь
- сумки
- аксессуары
- украшения
- часы

В текущем MVP реально используются общие категории:
- `wear`
- `shoes`
- `bags`
- `goods`
- `accessories`

## Что считается сущностью товара
На текущем этапе товар включает:
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

## Технологии текущей версии
- Python
- FastAPI
- HTML / CSS / JavaScript без frontend-фреймворка
- PostgreSQL schema design в `sql/schema_v2.sql`

## Ограничение текущей версии
Проект уже показывает рабочий каталог, но пока не использует реальную БД и не имеет загрузчика данных из JSON в PostgreSQL.
