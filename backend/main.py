from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "products.sample.json"
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Coursework Catalog MVP")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


def load_products() -> list[dict[str, Any]]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        return []
    return data


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products")
def list_products(
    q: str | None = Query(default=None),
    general_category: str | None = Query(default=None),
    brand: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    products = load_products()

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
    products = load_products()
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
