from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "rinkan_products_v4.json"
FRONTEND_DIR = BASE_DIR / "frontend"

logger = logging.getLogger(__name__)

app = FastAPI(title="Coursework Catalog MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def get_database_dsn() -> Optional[str]:
    env_dsn = os.getenv("DATABASE_URL")
    if env_dsn:
        return env_dsn

    database = os.getenv("PGDATABASE")
    if not database:
        return None

    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")
    return f"host={host} port={port} dbname={database} user={user} password={password}"


def load_products_from_json() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        return []
    return data


def serialize_product_row(row: dict[str, Any]) -> dict[str, Any]:
    image_urls = row.get("image_urls") or []
    parsed_at = row.get("parsed_at")
    if parsed_at is not None:
        parsed_at = parsed_at.isoformat()

    return {
        "title": row.get("title"),
        "source_product_id": row.get("source_product_id"),
        "product_url": row.get("product_url"),
        "main_image_url": row.get("main_image_url"),
        "image_urls": list(image_urls),
        "price_original": float(row["price_original"]) if row.get("price_original") is not None else None,
        "currency_code": row.get("currency_code"),
        "brand_name": row.get("brand_name"),
        "gender_label": row.get("gender_label"),
        "general_category_name": row.get("general_category_name"),
        "category_name": row.get("category_name"),
        "subcategory_name": row.get("subcategory_name"),
        "condition_rank": row.get("condition_rank"),
        "size_label": row.get("size_label"),
        "measurements_text": row.get("measurements_text"),
        "description": row.get("description"),
        "parsed_at": parsed_at,
        "status": row.get("status"),
    }


def fetch_products_from_db(
    q: Optional[str] = None,
    general_category: Optional[str] = None,
    brand: Optional[str] = None,
) -> Optional[list[dict[str, Any]]]:
    dsn = get_database_dsn()
    if not dsn or psycopg is None or dict_row is None:
        return None

    query = """
        SELECT
            p.title,
            p.source_product_id,
            p.product_url,
            p.main_image_url,
            COALESCE(
                array_remove(array_agg(pi.image_url ORDER BY pi.position), NULL),
                ARRAY[]::text[]
            ) AS image_urls,
            p.price_original,
            cur.code AS currency_code,
            b.name AS brand_name,
            g.name AS gender_label,
            gc.name AS general_category_name,
            c.name AS category_name,
            s.name AS subcategory_name,
            cond.name AS condition_rank,
            p.size_label,
            p.measurements_text,
            p.description,
            p.parsed_at,
            p.status
        FROM products p
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN genders g ON g.id = p.gender_id
        LEFT JOIN subcategories s ON s.id = p.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        LEFT JOIN general_categories gc ON gc.id = c.general_category_id
        LEFT JOIN conditions cond ON cond.id = p.condition_id
        LEFT JOIN currencies cur ON cur.id = p.currency_id
        LEFT JOIN product_images pi ON pi.product_id = p.id
        WHERE p.status = 'active'
    """

    params: list[Any] = []

    if q:
        query += """
            AND (
                p.title ILIKE %s
                OR COALESCE(b.name, '') ILIKE %s
                OR COALESCE(s.name, '') ILIKE %s
            )
        """
        needle = f"%{q}%"
        params.extend([needle, needle, needle])

    if general_category:
        query += " AND COALESCE(gc.name, '') = %s"
        params.append(general_category)

    if brand:
        query += " AND COALESCE(b.name, '') = %s"
        params.append(brand)

    query += """
        GROUP BY
            p.id,
            cur.code,
            b.name,
            g.name,
            gc.name,
            c.name,
            s.name,
            cond.name
        ORDER BY COALESCE(p.last_seen_in_listing_at, p.last_seen_at, p.parsed_at, p.created_at) DESC, p.id DESC
    """

    try:
        with psycopg.connect(dsn, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [serialize_product_row(row) for row in rows]
    except Exception as error:
        logger.warning("PostgreSQL unavailable, fallback to JSON: %s", error)
        return None


def fetch_product_from_db(source_product_id: str) -> Optional[dict[str, Any]]:
    dsn = get_database_dsn()
    if not dsn or psycopg is None or dict_row is None:
        return None

    query = """
        SELECT
            p.title,
            p.source_product_id,
            p.product_url,
            p.main_image_url,
            COALESCE(
                array_remove(array_agg(pi.image_url ORDER BY pi.position), NULL),
                ARRAY[]::text[]
            ) AS image_urls,
            p.price_original,
            cur.code AS currency_code,
            b.name AS brand_name,
            g.name AS gender_label,
            gc.name AS general_category_name,
            c.name AS category_name,
            s.name AS subcategory_name,
            cond.name AS condition_rank,
            p.size_label,
            p.measurements_text,
            p.description,
            p.parsed_at,
            p.status
        FROM products p
        LEFT JOIN brands b ON b.id = p.brand_id
        LEFT JOIN genders g ON g.id = p.gender_id
        LEFT JOIN subcategories s ON s.id = p.subcategory_id
        LEFT JOIN categories c ON c.id = s.category_id
        LEFT JOIN general_categories gc ON gc.id = c.general_category_id
        LEFT JOIN conditions cond ON cond.id = p.condition_id
        LEFT JOIN currencies cur ON cur.id = p.currency_id
        LEFT JOIN product_images pi ON pi.product_id = p.id
        WHERE p.source_product_id = %s
        GROUP BY
            p.id,
            cur.code,
            b.name,
            g.name,
            gc.name,
            c.name,
            s.name,
            cond.name
        LIMIT 1
    """

    try:
        with psycopg.connect(dsn, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (source_product_id,))
                row = cursor.fetchone()
                return serialize_product_row(row) if row else None
    except Exception as error:
        logger.warning("PostgreSQL unavailable, fallback to JSON detail: %s", error)
        return None


def get_data_source() -> str:
    return "postgresql" if get_database_dsn() and psycopg is not None else "json"


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "data_source": get_data_source()}


@app.get("/api/products")
def list_products(
    q: Optional[str] = Query(default=None),
    general_category: Optional[str] = Query(default=None),
    brand: Optional[str] = Query(default=None),
) -> list[dict[str, Any]]:
    db_products = fetch_products_from_db(q=q, general_category=general_category, brand=brand)
    if db_products is not None:
        return db_products

    products = load_products_from_json()

    if q:
        needle = q.lower()
        products = [
            product for product in products
            if needle in (product.get("title") or "").lower()
            or needle in (product.get("brand_name") or "").lower()
            or needle in (product.get("subcategory_name") or "").lower()
        ]

    if general_category:
        products = [
            product for product in products
            if (product.get("general_category_name") or "") == general_category
        ]

    if brand:
        products = [
            product for product in products
            if (product.get("brand_name") or "") == brand
        ]

    return products


@app.get("/api/products/{source_product_id}")
def get_product(source_product_id: str) -> dict[str, Any]:
    product = fetch_product_from_db(source_product_id)
    if product is not None:
        return product

    products = load_products_from_json()
    for product in products:
        if product.get("source_product_id") == source_product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/product.html")
def product_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "product.html")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
