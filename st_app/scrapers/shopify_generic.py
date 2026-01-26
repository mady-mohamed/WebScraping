# scrapers/shopify_generic.py
from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Set, Tuple, Optional

import requests
from bs4 import BeautifulSoup


DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
}


@dataclass
class ScrapeConfig:
    base_url: str
    collection_path: str = "/collections/all"
    page_param: str = "page"
    link_selector: str = 'a[href^="/products/"]'   # for most Shopify sites
    product_json_suffix: str = ".js"               # /products/<handle>.js


def _clean_handle_from_href(href: str) -> str:
    # Extract text after /products/ and before query string.
    if "/products/" not in href:
        return ""
    handle = href.partition("/products/")[-1].split("?")[0].strip("/")
    return handle.strip()


def get_handles_from_collection_page(
    session: requests.Session,
    cfg: ScrapeConfig,
    page: int,
    timeout: int = 15,
    headers: Optional[Dict[str, str]] = None,
) -> Set[str]:
    """
    Scrapes a collection page and returns a set of product handles.
    URL pattern: {base_url}{collection_path}?page=<page>
    """
    url = f"{cfg.base_url}{cfg.collection_path}?{cfg.page_param}={page}"
    r = session.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
    if r.status_code != 200:
        return set()

    soup = BeautifulSoup(r.text, "html.parser")
    handles: Set[str] = set()
    for a in soup.select(cfg.link_selector):
        href = a.get("href", "") or ""
        handle = _clean_handle_from_href(href)
        if handle:
            handles.add(handle)
    return handles


def fetch_product_json(
    session: requests.Session,
    cfg: ScrapeConfig,
    handle: str,
    timeout: int = 20,
    headers: Optional[Dict[str, str]] = None,
    retries: int = 2,
    backoff_sec: float = 2.0,
) -> Optional[dict]:
    """
    Fetches product JSON from /products/<handle>.js
    """
    url = f"{cfg.base_url}/products/{handle}{cfg.product_json_suffix}"
    last_err = None
    for attempt in range(retries):
        try:
            r = session.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            return r.json()
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(backoff_sec)
    return None  # failed


def scrape_shopify_all_products(
    base_url: str,
    *,
    max_pages: int = 200,
    per_product_delay: float = 1.0,
    timeout_collection: int = 15,
    timeout_product: int = 20,
    retries: int = 2,
    backoff_sec: float = 2.0,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Generic scraper for Shopify sites that list products under /collections/all?page=N
    and expose product JSON at /products/<handle>.js

    Returns:
      (rows, failed_handles)
    """
    session = requests.Session()
    cfg = ScrapeConfig(base_url=base_url.rstrip("/"), collection_path="/collections/all")

    all_handles_seen: Set[str] = set()
    rows: List[Dict] = []
    failed: List[str] = []

    for page in range(1, max_pages + 1):
        handles = get_handles_from_collection_page(
            session, cfg, page, timeout=timeout_collection, headers=headers
        )
        new_handles = handles - all_handles_seen

        # Stop condition: no new products found on this page
        if not new_handles:
            break

        all_handles_seen |= new_handles

        for handle in new_handles:
            product = fetch_product_json(
                session,
                cfg,
                handle,
                timeout=timeout_product,
                headers=headers,
                retries=retries,
                backoff_sec=backoff_sec,
            )
            if not product:
                failed.append(handle)
                continue

            product_url = f"{cfg.base_url}{product.get('url', '')}"
            title = product.get("title")
            variants = product.get("variants", []) or []

            for v in variants:
                rows.append(
                    {
                        "Product": title,
                        "Variant": v.get("title"),
                        "Price": (v.get("price") or 0) / 100.0,
                        "Handle": handle,
                        "Variant ID": v.get("id"),
                        "Availability": v.get("available"),
                        "SKU": v.get("sku"),
                        "Product URL": product_url,
                        "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                    }
                )

            time.sleep(per_product_delay)

    return rows, failed
