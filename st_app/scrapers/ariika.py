# scrapers/ariika.py
from __future__ import annotations

import time
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional

import requests
from bs4 import BeautifulSoup

from .shopify_generic import DEFAULT_HEADERS


ARIika_CATEGORIES = [
    "https://ariika.com/pages/bed-sheets",
    "https://ariika.com/pages/bed-fillers",
    "https://ariika.com/collections/mattresses",
    "https://ariika.com/pages/quilts-blanket",
]


def _clean_handle(href: str) -> str:
    if "/products/" not in href:
        return ""
    return href.partition("/products/")[-1].split("?")[0].strip("/").strip()


def scrape_ariika(
    *,
    categories: Optional[List[str]] = None,
    max_pages_per_category: int = 100,
    per_product_delay: float = 0.5,
    timeout_page: int = 15,
    timeout_product: int = 20,
    retries: int = 2,
    backoff_sec: float = 2.0,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Ariika uses category pages (some /pages/, some /collections/).
    We paginate with ?page=N and stop when no new handles are found.
    """
    session = requests.Session()
    headers = headers or DEFAULT_HEADERS

    categories = categories or ARIika_CATEGORIES
    all_handles_seen: Set[str] = set()
    rows: List[Dict] = []
    failed: List[str] = []

    for cat_url in categories:
        category_name = cat_url.rstrip("/").split("/")[-1]

        for page in range(1, max_pages_per_category + 1):
            url = f"{cat_url}?page={page}"
            r = session.get(url, headers=headers, timeout=timeout_page)
            if r.status_code != 200:
                break

            soup = BeautifulSoup(r.text, "html.parser")
            handles_on_page: Set[str] = set()

            for a in soup.select('a[href*="/products/"]'):
                href = a.get("href", "") or ""
                handle = _clean_handle(href)
                if handle:
                    handles_on_page.add(handle)

            new_handles = handles_on_page - all_handles_seen
            if not new_handles:
                break

            all_handles_seen |= new_handles

            for handle in new_handles:
                product = None
                json_url = f"https://ariika.com/products/{handle}.js"

                for attempt in range(retries):
                    try:
                        pr = session.get(json_url, headers=headers, timeout=timeout_product)
                        if pr.status_code != 200:
                            raise RuntimeError(f"HTTP {pr.status_code}")
                        product = pr.json()
                        break
                    except Exception:
                        if attempt < retries - 1:
                            time.sleep(backoff_sec)

                if not product:
                    failed.append(handle)
                    continue

                product_full_url = f"https://ariika.com/products/{handle}"
                for v in product.get("variants", []) or []:
                    rows.append(
                        {
                            "Category": category_name,
                            "Product": product.get("title"),
                            "Variant": v.get("title"),
                            "Price": (v.get("price") or 0) / 100.0,
                            "Handle": handle,
                            "Variant ID": v.get("id"),
                            "Availability": v.get("available"),
                            "SKU": v.get("sku"),
                            "Product URL": product_full_url,
                            "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                        }
                    )

                time.sleep(per_product_delay)

    return rows, failed
