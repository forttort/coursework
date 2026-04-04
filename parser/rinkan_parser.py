"""MVP-парсер RINKAN.

Что делает:
1. Заходит на страницу каталога RINKAN.
2. Собирает ссылки на карточки товаров.
3. Переходит в детальные страницы товаров.
4. Извлекает raw fields и сохраняет их в JSON.

Зависимости:
    pip install requests beautifulsoup4

Пример запуска:
    python parser/rinkan_parser.py \
        --start-url "https://www.rinkan-online.com/" \
        --pages 1 \
        --limit 20 \
        --output rinkan_products.json
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.rinkan-online.com"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


@dataclass
class RawRinkanProduct:
    title: str
    source_product_id: str
    product_url: str
    main_image_url: Optional[str]
    image_urls: list[str]
    price_original: Optional[int]
    currency_code: str
    brand_name: Optional[str]
    category_name: Optional[str]
    subcategory_name: Optional[str]
    condition_text: Optional[str]
    size_text: Optional[str]
    description: Optional[str]
    parsed_at: str


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def unique_keep_order(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not value:
            continue
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_product_url(href: str, base_url: str = BASE_URL) -> Optional[str]:
    if not href:
        return None
    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)
    if parsed.netloc not in {"www.rinkan-online.com", "rinkan-online.com"}:
        return None
    if not re.search(r"/products/[A-Za-z0-9-]+", parsed.path):
        return None
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def get_soup(url: str, session: requests.Session, timeout: int = 20) -> BeautifulSoup:
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    return BeautifulSoup(response.text, "html.parser")


def extract_product_urls_from_listing(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    for anchor in soup.find_all("a", href=True):
        normalized = normalize_product_url(anchor["href"])
        if normalized:
            urls.append(normalized)
    return unique_keep_order(urls)


def find_next_page_url(soup: BeautifulSoup, current_url: str) -> Optional[str]:
    for selector in ('a[rel="next"]', 'link[rel="next"]'):
        node = soup.select_one(selector)
        if node and node.get("href"):
            return urljoin(current_url, node["href"])

    next_texts = {"次へ", ">", "›", "→", "Next", "next"}
    for anchor in soup.find_all("a", href=True):
        text = clean_text(anchor.get_text(" ", strip=True))
        aria = clean_text(anchor.get("aria-label"))
        if text in next_texts or aria in next_texts:
            return urljoin(current_url, anchor["href"])

    return None


def crawl_listing_urls(
    start_url: str,
    pages: int,
    session: requests.Session,
    delay_sec: float = 1.0,
) -> list[str]:
    collected: list[str] = []
    visited_pages: set[str] = set()
    current_url: Optional[str] = start_url

    for _ in range(max(1, pages)):
        if not current_url or current_url in visited_pages:
            break

        soup = get_soup(current_url, session)
        visited_pages.add(current_url)
        collected.extend(extract_product_urls_from_listing(soup))

        next_url = find_next_page_url(soup, current_url)
        if not next_url:
            break

        current_url = next_url
        if delay_sec > 0:
            time.sleep(delay_sec)

    return unique_keep_order(collected)


def extract_price(text: str) -> Optional[int]:
    if not text:
        return None
    match = re.search(r"¥\s*([\d,]+)", text)
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def extract_label_sections(soup: BeautifulSoup) -> dict[str, str]:
    raw_lines = [clean_text(item) for item in soup.stripped_strings]
    lines = [line for line in raw_lines if line]

    interesting_labels = {
        "品番",
        "商品の状態",
        "ブランド",
        "色",
        "実寸",
        "素材",
        "付属品",
        "その他特徴",
        "サイズ",
        "性別タイプ",
        "カラー",
        "参考価格",
        "重さ",
        "コラボブランド",
        "取り扱い店舗",
    }

    sections: dict[str, list[str]] = {}
    current_label: Optional[str] = None

    for line in lines:
        if line in interesting_labels:
            current_label = line
            sections.setdefault(current_label, [])
            continue

        if current_label is not None:
            sections[current_label].append(line)

    return {key: "\n".join(value).strip() for key, value in sections.items() if value}


def extract_title_candidates(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str], Optional[str]]:
    headings = []
    for tag_name in ("h1", "h2", "h3"):
        for tag in soup.find_all(tag_name):
            text = clean_text(tag.get_text(" ", strip=True))
            if text and text not in headings:
                headings.append(text)

    if headings:
        brand_top = headings[0] if len(headings) >= 1 else None
        title_top = headings[1] if len(headings) >= 2 else None
        model_top = headings[2] if len(headings) >= 3 else None
        return brand_top, title_top, model_top

    title_tag = soup.find("title")
    if title_tag:
        title_text = clean_text(title_tag.get_text())
        if title_text:
            return None, title_text, None

    return None, None, None


def extract_main_image_url(soup: BeautifulSoup, page_url: str) -> Optional[str]:
    meta_candidates = [
        ("meta", {"property": "og:image"}),
        ("meta", {"name": "twitter:image"}),
    ]
    for tag_name, attrs in meta_candidates:
        tag = soup.find(tag_name, attrs=attrs)
        if tag and tag.get("content"):
            return urljoin(page_url, tag["content"])

    for img in soup.find_all("img", src=True):
        src = img["src"]
        if "logo" in src.lower():
            continue
        return urljoin(page_url, src)

    return None


def extract_all_image_urls(soup: BeautifulSoup, page_url: str) -> list[str]:
    candidates: list[str] = []

    for tag in soup.find_all("meta", attrs={"property": "og:image"}):
        if tag.get("content"):
            candidates.append(urljoin(page_url, tag["content"]))

    for img in soup.find_all("img", src=True):
        src = img["src"]
        if "logo" in src.lower():
            continue
        absolute = urljoin(page_url, src)
        candidates.append(absolute)

    cleaned = []
    for url in unique_keep_order(candidates):
        if re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", url, re.IGNORECASE):
            cleaned.append(url)
    return cleaned


def extract_category_info(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
    category_candidates = {"ウェア", "シューズ", "アクセサリー", "グッズ", "バッグ"}
    subcategory_candidates = {
        "アウター",
        "セーター",
        "シャツ",
        "スーツ",
        "パンツ",
        "ファッション雑貨",
        "帽子",
    }

    category_name = None
    subcategory_name = None

    for anchor in soup.find_all("a"):
        text = clean_text(anchor.get_text(" ", strip=True))
        if text in category_candidates and category_name is None:
            category_name = text
        if text in subcategory_candidates and subcategory_name is None:
            subcategory_name = text

    return category_name, subcategory_name


def extract_description(sections: dict[str, str]) -> Optional[str]:
    parts = []
    for key in ("商品の状態", "素材", "付属品", "その他特徴"):
        value = sections.get(key)
        if value:
            parts.append(f"{key}: {value}")
    if not parts:
        return None
    return "\n".join(parts)


def parse_detail_page(page_url: str, session: requests.Session) -> RawRinkanProduct:
    soup = get_soup(page_url, session)
    sections = extract_label_sections(soup)
    brand_top, title_top, model_top = extract_title_candidates(soup)
    category_name, subcategory_name = extract_category_info(soup)

    brand_name = sections.get("ブランド") or brand_top
    title = title_top or model_top or sections.get("ブランド") or ""
    source_product_id = sections.get("品番") or ""

    price_original = extract_price(soup.get_text(" ", strip=True))
    main_image_url = extract_main_image_url(soup, page_url)
    image_urls = extract_all_image_urls(soup, page_url)
    size_text = sections.get("サイズ") or sections.get("実寸")

    if not title:
        raise ValueError(f"Не удалось извлечь title со страницы {page_url}")
    if not source_product_id:
        product_id_match = re.search(r"/products/([A-Za-z0-9-]+)", page_url)
        if product_id_match:
            source_product_id = product_id_match.group(1)
        else:
            raise ValueError(f"Не удалось извлечь source_product_id со страницы {page_url}")

    return RawRinkanProduct(
        title=title,
        source_product_id=source_product_id,
        product_url=page_url,
        main_image_url=main_image_url,
        image_urls=image_urls,
        price_original=price_original,
        currency_code="JPY",
        brand_name=brand_name,
        category_name=category_name,
        subcategory_name=subcategory_name,
        condition_text=sections.get("商品の状態"),
        size_text=size_text,
        description=extract_description(sections),
        parsed_at=datetime.now(timezone.utc).isoformat(),
    )


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def save_products(products: list[RawRinkanProduct], output_path: str) -> None:
    payload = [asdict(item) for item in products]
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MVP-парсер товаров RINKAN: получает ссылки из listing и разбирает detail pages."
    )
    parser.add_argument(
        "--start-url",
        required=True,
        help="URL страницы каталога RINKAN, с которой начинаем сбор товаров.",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=1,
        help="Сколько страниц listing пройти последовательно через next page.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Максимум товаров для разбора после сбора ссылок.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Задержка между HTTP-запросами в секундах.",
    )
    parser.add_argument(
        "--output",
        default="rinkan_products.json",
        help="Путь к JSON-файлу с результатом.",
    )
    args = parser.parse_args()

    session = build_session()
    product_urls = crawl_listing_urls(
        start_url=args.start_url,
        pages=args.pages,
        session=session,
        delay_sec=args.delay,
    )
    if not product_urls:
        raise SystemExit("Не удалось найти ссылки на товары. Проверь start-url.")

    selected_urls = product_urls[: max(1, args.limit)]
    parsed_products: list[RawRinkanProduct] = []

    for index, product_url in enumerate(selected_urls, start=1):
        try:
            product = parse_detail_page(product_url, session)
            parsed_products.append(product)
            print(f"[{index}/{len(selected_urls)}] OK {product.source_product_id} {product.title}")
        except Exception as error:
            print(f"[{index}/{len(selected_urls)}] ERROR {product_url} -> {error}")
        finally:
            if args.delay > 0:
                time.sleep(args.delay)

    save_products(parsed_products, args.output)
    print(f"Готово. Сохранено {len(parsed_products)} товаров в {args.output}")


if __name__ == "__main__":
    main()
