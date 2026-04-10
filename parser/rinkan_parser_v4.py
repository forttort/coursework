
"""RINKAN parser v7.

Что делает:
- listing -> detail pages
- парсит title, id, цену, картинки, бренд, пол, размер, замеры
- category/subcategory берет из __NUXT_DATA__
- general_category_name вычисляет из parent_category/category
- condition_rank берет из structured data (product_condition)
- condition_text убран
"""

from __future__ import annotations

import argparse
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
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

STOP_LABELS = {
    "注文",
    "配送",
    "返品",
    "配送＆返品",
    "注文 / 配送＆返品",
    "店舗一覧",
    "ご利用ガイド",
    "よくある質問",
    "ご利用規約",
    "お問い合わせ",
    "お買取りはこちら",
    "会社概要",
    "プライバシーポリシー",
    "特定商取引法に基づく表示",
    "悪質サイトへのご注意",
    "ギフトラッピングサービス",
    "採用情報",
    "ASKWATCH ONLINE",
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

WEAR_PARENTS = {
    "shirts",
    "outerwear",
    "outer",
    "jacket",
    "coat",
    "knit",
    "sweat",
    "hoodie",
    "tops",
    "cutsew",
    "tops-cutsew",
    "pants",
    "bottoms",
    "skirt",
    "onepiece",
    "dress",
    "setup",
    "set-up",
    "suits",
    "vest",
    "underwear",
}

SHOES_PARENTS = {
    "shoes",
    "sneakers",
    "boots",
    "sandals",
    "loafers",
    "mules",
    "pumps",
    "heels",
}

BAGS_PARENTS = {
    "bags",
    "bag",
    "backpack",
    "shoulder-bag",
    "tote-bag",
    "hand-bag",
    "duffle-bag",
    "briefcase",
    "suitcase",
}

ACCESSORIES_PARENTS = {
    "accessories",
    "jewelry",
    "necklace",
    "ring",
    "bracelet",
    "bangle",
    "wallet-chain",
    "watch",
    "pierce",
    "earring",
    "pendant",
    "charm",
}

GOODS_PARENTS = {
    "wallet",
    "wallets",
    "card-case",
    "card-cases",
    "keycase",
    "keycases",
    "belt",
    "belts",
    "hat",
    "hats",
    "cap",
    "caps",
    "eyewear",
    "glasses",
    "sunglasses",
    "stole",
    "scarf",
    "gloves",
    "fashion-goods",
    "small-goods",
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
    gender_label: Optional[str]
    general_category_name: Optional[str]
    category_name: Optional[str]
    subcategory_name: Optional[str]
    condition_rank: Optional[str]
    size_label: Optional[str]
    measurements_text: Optional[str]
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


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    adapter = requests.adapters.HTTPAdapter(max_retries=2)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_soup(url: str, session: requests.Session, timeout: int = 60) -> BeautifulSoup:
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


def _trim_inline_label_prefix(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^[|｜:\s：]+", "", value)
    return value.strip()


def extract_block_after_label(lines: list[str], label: str) -> Optional[str]:
    for index, line in enumerate(lines):
        if line == label:
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

        if line.startswith(label):
            if line in HELPER_STOP_LINES or line.startswith(f"{label}ガイド"):
                continue

            remainder = line[len(label):]
            if remainder and remainder[0] not in {" ", "　", ":", "：", "|", "｜"}:
                continue

            remainder = _trim_inline_label_prefix(remainder)
            if remainder:
                stop_tokens = sorted(STOP_LABELS | INTERESTING_LABELS | HELPER_STOP_LINES, key=len, reverse=True)
                stop_pattern = r"|".join(re.escape(token) for token in stop_tokens)
                remainder = re.split(rf"(?={stop_pattern})", remainder, maxsplit=1)[0]
                return clean_block_value(remainder)

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
    if not value or value in BAD_BRAND_VALUES:
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


def normalize_gender_label(value: Optional[str]) -> Optional[str]:
    value = clean_text(value)
    if not value:
        return None
    mapping = {
        "men": "メンズ",
        "mens": "メンズ",
        "women": "レディース",
        "womens": "レディース",
        "unisex": "ユニセックス",
    }
    return mapping.get(value.lower(), value)


def infer_general_category_name(parent_category: Optional[str], subcategory_slug: Optional[str]) -> Optional[str]:
    parent = clean_text(parent_category).lower()
    slug = clean_text(subcategory_slug).lower()

    if parent in WEAR_PARENTS or slug in WEAR_PARENTS:
        return "wear"
    if parent in SHOES_PARENTS or slug in SHOES_PARENTS:
        return "shoes"
    if parent in BAGS_PARENTS or slug in BAGS_PARENTS:
        return "bags"
    if parent in ACCESSORIES_PARENTS or slug in ACCESSORIES_PARENTS:
        return "accessories"
    if parent in GOODS_PARENTS or slug in GOODS_PARENTS:
        return "goods"

    if "bag" in parent or "bag" in slug:
        return "bags"
    if "shoe" in parent or "shoe" in slug or "sneaker" in slug or "boot" in slug:
        return "shoes"
    if any(token in parent for token in ("shirt", "pant", "jacket", "coat", "hoodie", "sweat", "knit", "dress")):
        return "wear"

    return None


def extract_top_table_value(soup: BeautifulSoup, label: str) -> Optional[str]:
    rows = soup.select("table.table.is-borderless.is-list.is-narrow.is-mobile tr")
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if not th or not td:
            continue
        if clean_text(th.get_text(" ", strip=True)) != label:
            continue
        value = clean_text(td.get_text(" ", strip=True))
        value = value.lstrip("：:").strip()
        if value == "-":
            return None
        return value or None
    return None


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
        if any(
            bad in lower_url
            for bad in ("icon-acc", "productsbnr", "line/", "repeat-coupon/", "purchase/", "rinkantag")
        ):
            continue
        if source_product_id.lower() not in lower_url:
            continue
        if not re.search(r"\.(jpg|jpeg|png|webp)(?:\?|$)", lower_url):
            continue
        filtered.append(url)

    return filtered


def extract_description(lines: list[str]) -> Optional[str]:
    parts = []
    for key in ("素材", "付属品", "その他特徴"):
        value = extract_block_after_label(lines, key)
        if value and value != "-":
            parts.append(f"{key}: {value}")
    if not parts:
        return None
    return "\n".join(parts)


def _resolve_nuxt_ref(root: list[Any], value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and 0 <= value < len(root):
        return _resolve_nuxt_value(root, root[value])
    return _resolve_nuxt_value(root, value)


def _resolve_nuxt_value(root: list[Any], value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _resolve_nuxt_ref(root, v) for k, v in value.items()}
    if isinstance(value, list):
        if value and isinstance(value[0], str) and value[0] in {"ShallowReactive", "Reactive", "Set", "Map"}:
            if len(value) > 1:
                return _resolve_nuxt_ref(root, value[1])
        return [_resolve_nuxt_ref(root, x) for x in value]
    return value


def extract_structured_product_data(soup: BeautifulSoup) -> dict[str, Any]:
    tag = soup.select_one("#__NUXT_DATA__")
    if not tag:
        return {}
    raw = tag.get_text(strip=True)
    if not raw:
        return {}
    try:
        root = json.loads(raw)
        decoded = _resolve_nuxt_value(root, root[0])
        data = decoded.get("data", {})
        product_container = data.get("product", {})
        products = product_container.get("products", [])
        if products and isinstance(products[0], dict):
            return products[0]
    except Exception:
        return {}
    return {}


def parse_detail_page(page_url: str, session: requests.Session) -> RawRinkanProduct:
    soup = get_soup(page_url, session)
    lines = get_clean_lines(soup)

    detail_lines = lines
    if "商品詳細" in lines:
        detail_start = lines.index("商品詳細")
        detail_lines = lines[detail_start:]

    structured = extract_structured_product_data(soup)
    brand_top, title_top, model_top = extract_product_headings(soup)

    product_id_match = re.search(r"/products/([A-Za-z0-9-]+)", page_url)
    fallback_product_id = product_id_match.group(1) if product_id_match else ""

    source_product_id = (
        clean_text(extract_block_after_label(detail_lines, "品番"))
        or clean_text(structured.get("product_code"))
        or fallback_product_id
    )
    if not source_product_id:
        raise ValueError(f"Не удалось извлечь source_product_id со страницы {page_url}")

    title = clean_text(title_top) or clean_text(model_top) or clean_text(structured.get("product_name")) or ""
    if not title:
        raise ValueError(f"Не удалось извлечь title со страницы {page_url}")

    price_original = structured.get("price") if isinstance(structured.get("price"), int) else extract_price(
        soup.get_text(" ", strip=True)
    )

    image_urls = extract_product_image_urls(soup, page_url, source_product_id)
    main_image_url = image_urls[0] if image_urls else None

    gender_label = normalize_gender_label(structured.get("gender")) or extract_top_table_value(soup, "性別タイプ")
    size_label = normalize_size_text(structured.get("size")) or normalize_size_text(extract_top_table_value(soup, "サイズ"))

    parent_category = clean_text(structured.get("parent_category")) or None
    subcategory_slug = clean_text(structured.get("category")) or None
    subcategory_name = clean_text(structured.get("category_name")) or None
    general_category_name = infer_general_category_name(parent_category, subcategory_slug)

    brand_raw = extract_block_after_label(detail_lines, "ブランド")
    brand_name = (
        normalize_brand_name(brand_raw)
        or normalize_brand_name(structured.get("brand_name"))
        or normalize_brand_name(brand_top)
    )

    condition_rank = clean_text(structured.get("product_condition")) or None
    measurements_text = clean_block_value(
        extract_block_after_label(detail_lines, "実寸")
    ) or clean_block_value(structured.get("measurement"))
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
        gender_label=gender_label,
        general_category_name=general_category_name,
        category_name=parent_category,
        subcategory_name=subcategory_name,
        condition_rank=condition_rank,
        size_label=size_label,
        measurements_text=measurements_text,
        description=description,
        parsed_at=datetime.now(timezone.utc).isoformat(),
    )


def save_products(products: list[RawRinkanProduct], output_path: str) -> None:
    payload = [asdict(item) for item in products]
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="RINKAN parser v7")
    parser.add_argument("--start-url", required=True)
    parser.add_argument("--pages", type=int, default=1)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--output", default="rinkan_products_v7.json")
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
