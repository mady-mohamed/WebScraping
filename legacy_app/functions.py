import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def get_handles_from_page(base_url, page):
    """Scrapes a collection page and returns a set of product handles."""
    url = f"{base_url}/collections/all?page={page}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: {response.status_code}")
            return set()
        
        soup = BeautifulSoup(response.text, "html.parser")
        handles = set()
        for a in soup.select('a[href^="/products/"]'):
            # Extract handle and strip query parameters/slashes
            handle = a.get("href", "").partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
                handles.add(handle)
        return handles
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return set()

def extract_product_data(base_url, handles):
    """Fetches JSON data for a list of handles and returns a list of variant dictionaries."""
    results = []
    failed = []
    
    for handle in handles:
        product = None
        product_url = None
        handle_url = f'{base_url}/products/{handle}.js'
        
        for attempt in range(2):
            try:
                r = requests.get(handle_url, timeout=20)
                if r.status_code != 200:
                    raise RuntimeError(f"HTTP {r.status_code}")
                product = r.json()
                product_url = f'{base_url}{product.get("url")}'
                break
            except Exception as e:
                if attempt == 1:
                    print(f"FAILED {handle}: {e}")
                    failed.append(handle)
                else:
                    time.sleep(2)
                    continue
        
        if product:
            for v in product.get("variants", []):
                item = {
                    "Product": product.get("title"),
                    "Variant": v.get("title"),
                    "Price": v.get("price") / 100.0,
                    "Handle": handle,
                    "Variant ID": v.get("id"),
                    "Availability": v.get("available"),
                    "SKU": v.get("sku"),
                    "Product URL": product_url,
                    "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p")
                }
                results.append(item)
            time.sleep(1)  # Respectful delay
            
    return results, failed