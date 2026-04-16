# Coursework

Веб-каталог fashion-товаров с японских площадок. Текущая версия репозитория — это MVP, в котором уже есть парсер первого источника, минимальный backend на `FastAPI`, статический frontend и sample-данные для демонстрации каталога.

## Что уже есть
- `parser/rinkan_parser_v4.py` — рабочий парсер для `RINKAN`
- `backend/main.py` — backend API и раздача статических HTML-страниц
- `frontend/index.html` и `frontend/product.html` — каталог и страница товара
- `data/products.sample.json` — тестовый набор данных, который сейчас использует backend
- `sql/schema_v2.sql` — актуальная схема БД под загрузку товаров
- `docs/*` — документация по API, БД, фронту, парсеру и текущему состоянию

## Как сейчас работает проект
Текущий поток данных такой:

1. Парсер собирает товары с `RINKAN`
2. Результат сохраняется в JSON
3. Backend читает sample JSON из `data/products.sample.json`
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
Можно запускать модуль `uvicorn` с параметрами:

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
- `data` — sample-данные для локального запуска
- `docs` — актуальная документация по проекту

## Текущее ограничение
- backend пока читает JSON, а не базу данных
- loader в PostgreSQL ещё не реализован
- нет пагинации, сортировки и расширенных фильтров
- frontend минимальный и без UI-фреймворка

## Следующий логичный этап
1. Реализовать `loader/load_rinkan_to_postgres.py`
2. Подключить backend к PostgreSQL
3. Перевести каталог с sample JSON на реальные запросы к БД
4. Расширить API и фильтры на frontend
