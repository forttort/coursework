# Coursework

Веб-каталог fashion-товаров с японских площадок. Текущая версия репозитория — это MVP, в котором уже есть парсер первого источника, минимальный backend на `FastAPI`, статический frontend и JSON-данные для демонстрации каталога.

## Что уже есть
- `parser/rinkan_parser_v4.py` — рабочий парсер для `RINKAN`
- `backend/main.py` — backend API и раздача статических HTML-страниц
- `frontend/index.html` и `frontend/product.html` — каталог и страница товара
- `rinkan_products_v4.json` — текущий JSON-файл, который сейчас использует backend
- `sql/schema_v2.sql` — актуальная схема БД под загрузку товаров
- `docs/*` — документация по API, БД, фронту, парсеру и текущему состоянию

## Как сейчас работает проект
Текущий поток данных такой:

1. Парсер собирает товары с `RINKAN`
2. Результат сохраняется в JSON
3. Backend читает JSON из `rinkan_products_v4.json`
4. Frontend получает товары через `/api/products`

То есть сейчас проект работает без PostgreSQL и без отдельного loader.

## Что умеет MVP
- открыть каталог товаров
- загрузить список товаров через API
- искать по названию, бренду и подкатегории
- фильтровать по общей категории
- открыть подробную страницу товара
- показать изображения, размер, состояние, описание и ссылку на исходный товар

## Быстрый запуск

### Самый простой запуск из PyCharm
Если не хочется возиться с интерпретаторами и параметрами, можно просто запускать готовые файлы:

- `run_site.py` — поднимает сайт
- `run_parser_new_arrivals.py` — запускает парсер по `new-arrivals` и сохраняет в `rinkan_products_v4.json`

Оба файла сами используют интерпретатор проекта:
- `/Users/danil/coursework/.venv/bin/python`

### Через терминал
```bash
cd /Users/danil/coursework
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

После запуска открыть:
- `http://127.0.0.1:8000/`

### Из PyCharm
Теперь можно вообще просто запускать файл `backend/main.py` кнопкой `Run`.

Самый простой вариант:

- открыть `backend/main.py`
- нажать `Run`
- открыть `http://127.0.0.1:8000/`

В этом режиме сервер стартует без авто-перезагрузки, зато без проблем с импортом модуля `backend`.

Если хочешь именно через отдельную конфигурацию, можно запускать модуль `uvicorn` с параметрами:

- Module name: `uvicorn`
- Parameters: `backend.main:app --reload`
- Working directory: `/Users/danil/coursework`

## Доступные маршруты

### HTML
- `/` — каталог
- `/product.html?id=<source_product_id>` — страница товара

### API
- `/api/health`
- `/api/products`
- `/api/products/{source_product_id}`

## Структура репозитория
- `backend` — API на `FastAPI`
- `frontend` — статические HTML/CSS/JS-файлы MVP
- `parser` — парсер первого источника `RINKAN`
- `loader` — место под будущий загрузчик данных в PostgreSQL
- `sql` — схемы БД
- `data` — вспомогательные данные проекта
- `docs` — актуальная документация по проекту

## Текущее ограничение
- backend пока читает JSON, а не базу данных
- loader в PostgreSQL уже реализован, но backend пока не переведен на БД
- нет пагинации, сортировки и расширенных фильтров
- frontend минимальный и без UI-фреймворка

## Следующий логичный этап
1. Поднять PostgreSQL по `sql/schema_v2.sql` или обновить существующую БД через `sql/alter_products_tracking.sql`
2. Загрузить данные через `loader/load_rinkan_to_postgres.py`
3. Перевести каталог с JSON на реальные запросы к БД
4. Расширить API и фильтры на frontend
