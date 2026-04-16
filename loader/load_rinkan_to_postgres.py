from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import psycopg


DEFAULT_SOURCE_NAME = "RINKAN"
DEFAULT_SOURCE_BASE_URL = "https://rinkan-online.com"
ACTIVE_STATUS = "active"
MISSING_STATUS = "missing"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load RINKAN JSON into PostgreSQL")
    parser.add_argument("--input", default="rinkan_products_v4.json")
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--source-name", default=DEFAULT_SOURCE_NAME)
    parser.add_argument("--source-base-url", default=DEFAULT_SOURCE_BASE_URL)
    parser.add_argument("--mode", choices=["incremental", "full"], default="incremental")
    return parser.parse_args()


def resolve_dsn(cli_dsn: Optional[str]) -> str:
    if cli_dsn:
        return cli_dsn

    env_dsn = os.getenv("DATABASE_URL")
    if env_dsn:
        return env_dsn

    database = os.getenv("PGDATABASE")
    if not database:
        raise SystemExit(
            "Не передан --dsn и не найден DATABASE_URL/PGDATABASE. "
            "Передай --dsn или настрой переменные PostgreSQL."
        )

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")
    return f"host={host} port={port} dbname={database} user={user} password={password}"


def load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Не найден JSON-файл: {path}")

    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    if not isinstance(payload, list):
        raise SystemExit("JSON должен быть списком товаров")

    return payload


def normalize_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    text = normalize_string(value)
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def to_decimal(value: Any) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    return Decimal(str(value))


def currency_name_from_code(code: str) -> str:
    mapping = {
        "JPY": "Japanese Yen",
        "USD": "US Dollar",
        "EUR": "Euro",
    }
    return mapping.get(code, code)


def get_or_create_simple_ref(cursor: psycopg.Cursor[Any], table: str, value: Optional[str]) -> Optional[int]:
    if not value:
        return None

    cursor.execute(
        f"""
        INSERT INTO {table} (name)
        VALUES (%s)
        ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (value,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_or_create_source_id(cursor: psycopg.Cursor[Any], name: str, base_url: str) -> int:
    cursor.execute(
        """
        INSERT INTO sources (name, base_url)
        VALUES (%s, %s)
        ON CONFLICT (name) DO UPDATE SET base_url = EXCLUDED.base_url
        RETURNING id
        """,
        (name, base_url),
    )
    return cursor.fetchone()[0]


def get_or_create_currency_id(cursor: psycopg.Cursor[Any], code: str) -> int:
    cursor.execute(
        """
        INSERT INTO currencies (code, name)
        VALUES (%s, %s)
        ON CONFLICT (code) DO UPDATE SET name = EXCLUDED.name
        RETURNING id
        """,
        (code, currency_name_from_code(code)),
    )
    return cursor.fetchone()[0]


def get_or_create_category_chain(
    cursor: psycopg.Cursor[Any],
    general_category_name: Optional[str],
    category_name: Optional[str],
    subcategory_name: Optional[str],
) -> tuple[Optional[int], Optional[int], Optional[int]]:
    general_id = None
    category_id = None
    subcategory_id = None

    if general_category_name:
        cursor.execute(
            """
            INSERT INTO general_categories (name)
            VALUES (%s)
            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (general_category_name,),
        )
        general_id = cursor.fetchone()[0]

    if general_id and category_name:
        cursor.execute(
            """
            INSERT INTO categories (general_category_id, name)
            VALUES (%s, %s)
            ON CONFLICT (general_category_id, name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (general_id, category_name),
        )
        category_id = cursor.fetchone()[0]

    if category_id and subcategory_name:
        cursor.execute(
            """
            INSERT INTO subcategories (category_id, name)
            VALUES (%s, %s)
            ON CONFLICT (category_id, name)
            DO UPDATE SET name = EXCLUDED.name
            RETURNING id
            """,
            (category_id, subcategory_name),
        )
        subcategory_id = cursor.fetchone()[0]

    return general_id, category_id, subcategory_id


def replace_product_images(cursor: psycopg.Cursor[Any], product_id: int, image_urls: list[str]) -> None:
    cursor.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))

    for position, image_url in enumerate(image_urls, start=1):
        cursor.execute(
            """
            INSERT INTO product_images (product_id, image_url, position)
            VALUES (%s, %s, %s)
            """,
            (product_id, image_url, position),
        )


def upsert_product(
    cursor: psycopg.Cursor[Any],
    product: dict[str, Any],
    source_id: int,
    brand_id: Optional[int],
    gender_id: Optional[int],
    subcategory_id: Optional[int],
    condition_id: Optional[int],
    currency_id: int,
    seen_at: datetime,
) -> tuple[int, bool]:
    image_urls = product.get("image_urls") or []
    if not isinstance(image_urls, list):
        image_urls = []

    main_image_url = normalize_string(product.get("main_image_url"))
    if not main_image_url and image_urls:
        main_image_url = normalize_string(image_urls[0])

    cursor.execute(
        """
        INSERT INTO products (
            title,
            brand_id,
            gender_id,
            subcategory_id,
            condition_id,
            source_id,
            currency_id,
            source_product_id,
            size_label,
            measurements_text,
            price_original,
            status,
            description,
            product_url,
            main_image_url,
            parsed_at,
            first_seen_at,
            last_seen_at,
            last_checked_at,
            last_seen_in_listing_at,
            sold_at,
            updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, CURRENT_TIMESTAMP
        )
        ON CONFLICT (source_id, source_product_id) DO UPDATE SET
            title = EXCLUDED.title,
            brand_id = EXCLUDED.brand_id,
            gender_id = EXCLUDED.gender_id,
            subcategory_id = EXCLUDED.subcategory_id,
            condition_id = EXCLUDED.condition_id,
            currency_id = EXCLUDED.currency_id,
            size_label = EXCLUDED.size_label,
            measurements_text = EXCLUDED.measurements_text,
            price_original = EXCLUDED.price_original,
            status = EXCLUDED.status,
            description = EXCLUDED.description,
            product_url = EXCLUDED.product_url,
            main_image_url = EXCLUDED.main_image_url,
            parsed_at = EXCLUDED.parsed_at,
            last_seen_at = EXCLUDED.last_seen_at,
            last_checked_at = EXCLUDED.last_checked_at,
            last_seen_in_listing_at = EXCLUDED.last_seen_in_listing_at,
            sold_at = NULL,
            updated_at = CURRENT_TIMESTAMP
        RETURNING id, (xmax = 0) AS inserted
        """,
        (
            normalize_string(product.get("title")),
            brand_id,
            gender_id,
            subcategory_id,
            condition_id,
            source_id,
            currency_id,
            normalize_string(product.get("source_product_id")),
            normalize_string(product.get("size_label")),
            normalize_string(product.get("measurements_text")),
            to_decimal(product.get("price_original")),
            ACTIVE_STATUS,
            normalize_string(product.get("description")),
            normalize_string(product.get("product_url")),
            main_image_url,
            parse_iso_datetime(product.get("parsed_at")),
            seen_at,
            seen_at,
            seen_at,
            seen_at,
            None,
        ),
    )
    product_id, inserted = cursor.fetchone()
    replace_product_images(cursor, product_id, [str(url) for url in image_urls if normalize_string(url)])
    return product_id, bool(inserted)


def mark_missing_products(
    cursor: psycopg.Cursor[Any],
    source_id: int,
    imported_ids: list[str],
    checked_at: datetime,
) -> int:
    if not imported_ids:
        raise SystemExit("Режим full нельзя запускать на пустом наборе товаров")

    cursor.execute(
        """
        UPDATE products
        SET status = %s,
            last_checked_at = %s,
            updated_at = CURRENT_TIMESTAMP
        WHERE source_id = %s
          AND status <> 'sold'
          AND NOT (source_product_id = ANY(%s))
        """,
        (MISSING_STATUS, checked_at, source_id, imported_ids),
    )
    return cursor.rowcount


def validate_product(product: dict[str, Any]) -> None:
    required_fields = ["title", "source_product_id", "product_url"]
    missing = [field for field in required_fields if not normalize_string(product.get(field))]
    if missing:
        raise ValueError(f"У товара нет обязательных полей: {', '.join(missing)}")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).resolve()
    products = load_json(input_path)
    dsn = resolve_dsn(args.dsn)
    seen_at = datetime.now(timezone.utc)

    inserted_count = 0
    updated_count = 0

    with psycopg.connect(dsn) as connection:
        with connection.cursor() as cursor:
            source_id = get_or_create_source_id(cursor, args.source_name, args.source_base_url)
            imported_ids: list[str] = []

            for product in products:
                validate_product(product)

                source_product_id = normalize_string(product.get("source_product_id"))
                imported_ids.append(source_product_id)

                general_category_name = normalize_string(product.get("general_category_name"))
                category_name = normalize_string(product.get("category_name"))
                subcategory_name = normalize_string(product.get("subcategory_name"))
                _, _, subcategory_id = get_or_create_category_chain(
                    cursor,
                    general_category_name,
                    category_name,
                    subcategory_name,
                )

                brand_id = get_or_create_simple_ref(cursor, "brands", normalize_string(product.get("brand_name")))
                gender_id = get_or_create_simple_ref(cursor, "genders", normalize_string(product.get("gender_label")))
                condition_id = get_or_create_simple_ref(cursor, "conditions", normalize_string(product.get("condition_rank")))
                currency_code = normalize_string(product.get("currency_code")) or "JPY"
                currency_id = get_or_create_currency_id(cursor, currency_code)

                _, inserted = upsert_product(
                    cursor,
                    product,
                    source_id,
                    brand_id,
                    gender_id,
                    subcategory_id,
                    condition_id,
                    currency_id,
                    seen_at,
                )

                if inserted:
                    inserted_count += 1
                else:
                    updated_count += 1

            missing_count = 0
            if args.mode == "full":
                missing_count = mark_missing_products(cursor, source_id, imported_ids, seen_at)

        connection.commit()

    print(f"Обработано товаров: {len(products)}")
    print(f"Вставлено новых: {inserted_count}")
    print(f"Обновлено существующих: {updated_count}")
    if args.mode == "full":
        print(f"Помечено missing: {missing_count}")


if __name__ == "__main__":
    main()
