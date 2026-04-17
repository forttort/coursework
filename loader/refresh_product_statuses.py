from __future__ import annotations

import argparse
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg
import requests
from bs4 import BeautifulSoup
from psycopg.rows import dict_row

ACTIVE_STATUS = "active"
MISSING_STATUS = "missing"
SOLD_STATUS = "sold"
UNKNOWN_STATUS = "unknown"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh product availability statuses from live product pages")
    parser.add_argument("--dsn", default=None)
    parser.add_argument("--source-name", default="RINKAN")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--statuses", default="active,missing")
    parser.add_argument("--source-product-id", default=None)
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


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_products_to_check(
    connection: psycopg.Connection[Any],
    source_name: str,
    statuses: list[str],
    limit: int,
    source_product_id: Optional[str],
) -> list[dict[str, Any]]:
    query = """
        SELECT
            p.id,
            p.source_product_id,
            p.product_url,
            p.status,
            p.last_checked_at
        FROM products p
        JOIN sources s ON s.id = p.source_id
        WHERE s.name = %s
    """
    params: list[Any] = [source_name]

    if source_product_id:
        query += " AND p.source_product_id = %s"
        params.append(source_product_id)
    else:
        query += " AND p.status = ANY(%s)"
        params.append(statuses)

    query += " ORDER BY p.last_checked_at ASC NULLS FIRST, p.id ASC LIMIT %s"
    params.append(limit)

    with connection.cursor(row_factory=dict_row) as cursor:
        cursor.execute(query, params)
        return list(cursor.fetchall())


def detect_status_from_html(html: str) -> tuple[str, str]:
    if not html:
        return UNKNOWN_STATUS, "empty_html"

    if re.search(r"<button[^>]*disabled[^>]*>\s*在庫なし\s*</button>", html):
        return SOLD_STATUS, "disabled_button_zaiko_nashi"

    soup = BeautifulSoup(html, "html.parser")

    for button in soup.find_all("button"):
        text = " ".join(button.stripped_strings).strip()
        if "在庫なし" in text and button.has_attr("disabled"):
            return SOLD_STATUS, "button_text_zaiko_nashi"

    page_text = " ".join(soup.stripped_strings)
    if "在庫なし" in page_text:
        return SOLD_STATUS, "page_text_zaiko_nashi"

    if any(marker in page_text for marker in ["カートに入れる", "注文する", "注文へ進む"]):
        return ACTIVE_STATUS, "active_order_button_text"

    return ACTIVE_STATUS, "page_available_no_sold_marker"


def check_product_status(session: requests.Session, product_url: str) -> tuple[str, str, int]:
    response = session.get(product_url, timeout=60)
    status_code = response.status_code

    if status_code == 404:
        return MISSING_STATUS, "http_404", status_code

    if status_code >= 500:
        return UNKNOWN_STATUS, f"http_{status_code}", status_code

    status, reason = detect_status_from_html(response.text)
    return status, reason, status_code


def update_product_status(
    connection: psycopg.Connection[Any],
    product_id: int,
    status: str,
    checked_at: datetime,
) -> None:
    updates = ["status = %s", "last_checked_at = %s", "updated_at = CURRENT_TIMESTAMP"]
    params: list[Any] = [status, checked_at]

    if status in {ACTIVE_STATUS, SOLD_STATUS}:
        updates.append("last_seen_at = %s")
        params.append(checked_at)

    if status == SOLD_STATUS:
        updates.append("sold_at = COALESCE(sold_at, %s)")
        params.append(checked_at)

    if status == ACTIVE_STATUS:
        updates.append("sold_at = NULL")

    params.append(product_id)

    query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"

    with connection.cursor() as cursor:
        cursor.execute(query, params)


def main() -> None:
    args = parse_args()
    dsn = resolve_dsn(args.dsn)
    statuses = [item.strip() for item in args.statuses.split(",") if item.strip()]
    session = build_session()

    checked = 0
    changed = 0

    with psycopg.connect(dsn) as connection:
        products = fetch_products_to_check(
            connection,
            source_name=args.source_name,
            statuses=statuses,
            limit=args.limit,
            source_product_id=args.source_product_id,
        )

        if not products:
            print("Нет товаров для проверки")
            return

        for index, product in enumerate(products, start=1):
            checked_at = datetime.now(timezone.utc)
            status, reason, status_code = check_product_status(session, product["product_url"])

            previous_status = product["status"]
            if status != previous_status:
                changed += 1

            update_product_status(connection, product["id"], status, checked_at)
            connection.commit()
            checked += 1

            print(
                f"[{index}/{len(products)}] {product['source_product_id']} "
                f"{previous_status} -> {status} ({reason}, http={status_code})"
            )

            if args.delay > 0 and index < len(products):
                time.sleep(args.delay)

    print(f"Проверено товаров: {checked}")
    print(f"Изменено статусов: {changed}")


if __name__ == "__main__":
    main()
