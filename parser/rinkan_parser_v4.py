"""MVP-парсер RINKAN v4.

v4:
- brand_name берётся только из блока после label `ブランド`
- condition_text очищается от `状態ランクとは？`
- size_text `-` -> null
- остальная логика v3 сохранена
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

INTERESTING_LABELS = {
    "品番", "商品の状態", "ブランド", "色", "実寸", "素材", "付属品",
    "その他特徴", "サイズ", "性別タイプ", "カラー", "参考価格", "重さ",
    "コラボブランド", "取り扱い店舗",
}

STOP_LABELS = {
    "注文", "配送", "返品", "配送＆返品", "注文 / 配送＆返品", "店舗一覧",
    "ご利用ガイド", "よくある質問", "ご利用規約", "お問い合わせ", "お買取りはこちら",
    "会社概要", "プライバシーポリシー", "特定商取引法に基づく表示",
    "悪質サイトへのご注意", "ギフトラッピングサービス", "採用情報", "ASKWATCH ONLINE",
}

BAD_BRAND_VALUES = {
    "配送＆返品",
    "注文 / 配送＆返品",
    "注文",
    "配送",
    "返品",
    "ASKWATCH ONLINE",
}

HELPER_STOP_LINES = {"状態ランクとは？", "サイズガイド"}


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
        if value and value not in seen:
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


def crawl_listing_urls(start_url: str, pages: int, session: requests.Session, delay_sec: float = 1.0) -> list[str]:
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
    match = re.search(r"¥\s*([\d,]+)", text or "")
    if not match:
        return None
    return int(match.group(1).replace(",", ""))


def get_clean_lines(soup: BeautifulSoup) -> list[str]:
    return [clean_text(item) for item in soup.stripped_strings if clean_text(item)]


def clean_block_value(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    lines = [clean_text(line) for line in value.splitlines()]
    filtered = [line for line in lines if line and line not in HELPER_STOP_LINES]
    if not filtered:
        return None
    return "\n".join(filtered)


def extract_block_after_label(lines: list[str], label: str) -> Optional[str]:
    for index, line in enumerate(lines):
        if line != label:
            continue
        collected: list[str] = []
        for next_line in lines[index + 1 :]:
            if next_line in STOP_LABELS:
                break
            if next_line in INTERESTING_LABELS and next_line != label:
                break
            if next_line in HELPER_STOP_LINES:
                break
            collected.append(next_line)
        return clean_block_value("\n".join(collected).strip())
    return None


def extract_product_headings(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str], Optional[str]]:
    headings = []
    for tag_name in ("h1", "h2", "h3"):
        for tag in soup.find_all(tag_name):
            text = clean_text(tag.get_text(" ", strip=True))
            if text and text not in headings:
                headings.append(text)
    brand_top = headings[0] if len(headings) >= 1 else None
    title_top = headings[1] if len(headings) >= 2 else None
    model_top = headings[2] if len(headings) >= 3 else None
    if not title_top:
        title_tag = soup.find("title")
        if title_tag:
            title_top = clean_text(title_tag.get_text())
    return brand_top, title_top, model_top


def normalize_brand_name(value: Optional[str]) -> Optional[str]:
    value = clean_text(value)
    if not value:
        return None

    if value in BAD_BRAND_VALUES:
        return None

    parts = [clean_text(part) for part in re.split(r"[/／]", value) if clean_text(part)]
    if not parts:
        return None

    latin_parts = [part for part in parts if re.search(r"[A-Za-z]", part)]
    candidate = latin_parts[-1] if latin_parts else parts[-1]

    if candidate in BAD_BRAND_VALUES:
        return None

    return candidate


def normalize_size_text(value: Optional[str]) -> Optional[str]:
    value = clean_text(value)
    if not value:
        return None
    value = value.lstrip("：:").strip()
    if value == "-":
        return None
    return value or None


def extract_product_image_urls(soup: BeautifulSoup, page_url: str, source_product_id: str) -> list[str]:
    html = str(soup)
    candidates: list[str] = []
    attr_names = ("src", "data-src", "data-original", "data-lazy-src")
    for img in soup.find_all("img"):
        for attr_name in attr_names:
            attr_value = img.get(attr_name)
            if attr_value:
                candidates.append(urljoin(page_url, attr_value))
    for tag in soup.find_all("meta", attrs={"property": "og:image"}):
        if tag.get("content"):
            candidates.append(urljoin(page_url, tag["content"]))
    product_image_pattern = re.compile(
        rf"https?://[^\"' >]+/{re.escape(source_product_id)}_\d+\.(?:jpg|jpeg|png|webp)(?:\?[^\"' >]*)?",
        re.IGNORECASE,
    )
    candidates.extend(product_image_pattern.findall(html))
    filtered: list[str] = []
    for url in unique_keep_order(candidates):
        lower_url = url.lower()
        if any(bad in lower_url for bad in ("icon-acc", "productsbnr", "line/", "repeat-coupon/", "purchase/", "rinkantag")):
            continue
        if source_product_id.lower() not in lower_url:
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", lower_url):
            continue
        filtered.append(url)
    return filtered


def extract_description(lines: list[str]) -> Optional[str]:
    parts = []
    for key in ("商品の状態", "素材", "付属品", "その他特徴"):
        value = extract_block_after_label(lines, key)
        if value and value != "-":
            parts.append(f"{key}: {value}")
    if not parts:
        return None
    return "\n".join(parts)


def parse_detail_page(page_url: str, session: requests.Session) -> RawRinkanProduct:
    soup = get_soup(page_url, session)
    lines = get_clean_lines(soup)
    detail_lines = lines
    if "商品詳細" in lines:
        detail_start = lines.index("商品詳細")
        detail_lines = lines[detail_start:]
    brand_top, title_top, model_top = extract_product_headings(soup)
    product_id_match = re.search(r"/products/([A-Za-z0-9-]+)", page_url)
    fallback_product_id = product_id_match.group(1) if product_id_match else ""
    source_product_id = clean_text(extract_block_after_label(detail_lines, "品番")) or fallback_product_id
    if not source_product_id:
        raise ValueError(f"Не удалось извлечь source_product_id со страницы {page_url}")
    title = clean_text(title_top) or clean_text(model_top) or ""
    if not title:
        raise ValueError(f"Не удалось извлечь title со страницы {page_url}")
    price_original = extract_price(soup.get_text(" ", strip=True))
    image_urls = extract_product_image_urls(soup, page_url, source_product_id)
    main_image_url = image_urls[0] if image_urls else None
    brand_raw = extract_block_after_label(detail_lines, "ブランド")
    brand_name = normalize_brand_name(brand_raw)
    condition_text = clean_block_value(extract_block_after_label(detail_lines, "商品の状態"))
    size_text = normalize_size_text(
        extract_block_after_label(detail_lines, "サイズ") or extract_block_after_label(detail_lines, "実寸")
    )
    description = extract_description(detail_lines)
    return RawRinkanProduct(
        title=title,
        source_product_id=source_product_id,
        product_url=page_url,
        main_image_url=main_image_url,
        image_urls=image_urls,
        price_original=price_original,
        currency_code="JPY",
        brand_name=brand_name,
        category_name=None,
        subcategory_name=None,
        condition_text=condition_text,
        size_text=size_text,
        description=description,
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
    parser = argparse.ArgumentParser(description="MVP-парсер товаров RINKAN v4")
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", default="rinkan_products_v4.json")
    args = parser.parse_args()
    session = build_session()
    product_urls = crawl_listing_urls(args.start_url, args.pages, session, args.delay)
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
