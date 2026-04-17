# CURRENT STATE

Актуальное состояние репозитория на текущий момент.

## Что реально реализовано

### 1. Backend MVP
Есть минимальный backend на `FastAPI` в `backend/main.py`.

Он:
- читает товары из PostgreSQL, если настроено подключение
- fallback'ается на `rinkan_products_v4.json`, если БД недоступна или не настроена
- отдает `GET /api/health`
- отдает `GET /api/products`
- отдает `GET /api/products/{source_product_id}`
- раздает `frontend/index.html` и `frontend/product.html`

Поддерживаемые query-параметры каталога:
- `q`
- `general_category`
- `brand`

### 1.1. Обновление статусов товаров
Добавлен отдельный скрипт `loader/refresh_product_statuses.py`.

Он:
- берет товары из PostgreSQL
- открывает их `product_url`
- проверяет доступность карточки
- определяет `active / missing / sold`

Для `RINKAN` сейчас используется рабочий признак out of stock:
- disabled-кнопка с текстом `在庫なし`

### 2. Frontend MVP
Есть 2 статические страницы:
- `frontend/index.html` — каталог
- `frontend/product.html` — карточка товара

Текущий frontend умеет:
- загрузить товары из API
- искать по строке поиска
- фильтровать по общей категории
- фильтровать по бренду
- фильтровать по статусу
- листать каталог по страницам
- открывать страницу отдельного товара

### 3. JSON-данные
В `rinkan_products_v4.json` сейчас лежит `10` товаров.

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

## Что проверено
- `backend/main.py` компилируется
- `parser/rinkan_parser_v4.py` компилируется
- функции backend корректно читают JSON-файл с товарами
- backend-код для PostgreSQL добавлен и готов к запуску при настроенном DSN
- локальная PostgreSQL поднята, схема применена, `48` товаров загружены через loader
- backend локально читает данные из PostgreSQL
- логика refresh статусов проверена на реальной карточке `RINKAN`
- пагинация и filter options API работают от PostgreSQL

## Что ещё не сделано
- API с пагинацией и сортировкой
- фильтры по бренду, состоянию, размеру и полу на frontend
- расчет `price_rub`
- поле `delivery_estimate`
- тесты для backend и parser

## Что бросается в глаза при анализе репы
- файл называется `parser/rinkan_parser_v4.py`, но внутри комментарии и CLI уже называют его `v7`
- default output у парсера сейчас `rinkan_products_v7.json`
- в корне лежит `rinkan_products_v4.json`, то есть naming сейчас не до конца синхронизирован
- backend пока использует локальный JSON, а не результат loader или БД

## Следующий практический шаг
1. Привести naming парсера к одному виду
2. Докрутить scheduler для daily запуска
3. Добавить сортировку и дополнительные фильтры в backend/frontend
4. Подтвердить стратегию работы с картинками без VPN
