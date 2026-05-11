import requests
import time
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.google.com/"
}

# --- Helper Functions ---

def create_session(website):
    session = requests.Session()
    session.headers.update(HEADERS)
    domain = website.rstrip('/')
    base_url = f"{domain}/collections/all"
    return session, domain, base_url

def fetch_page(session, url):
    try:
        response = session.get(url, timeout=15)
        if response.status_code != 200:
            print(f"Stop: Status {response.status_code}")
            return None
        return response.text
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def extract_new_handles(html, all_handles):
    soup = BeautifulSoup(html, "html.parser")
    current_page_handles = set()
    for a in soup.select('a[href*="/products/"]'):
        href = a.get("href", "")
        handle = href.partition('/products/')[-1].split('?')[0].strip('/')
        if handle:
            current_page_handles.add(handle)
    
    new_handles = current_page_handles - all_handles
    return new_handles

def fetch_product_details(session, domain, handle):
    """Handles the JSON request and retry logic for a single product."""
    json_url = f'{domain}/products/{handle}.js'
    for attempt in range(2):
        try:
            r = session.get(json_url, timeout=20)
            if r.status_code == 200:
                return r.json()
            time.sleep(1)
        except Exception as e:
            print(f"Failed product {handle}: {e}")
            time.sleep(1)
    return None

def parse_product(product, domain, handle, brand):
    # Process Product Details
    description_raw = product.get('description', "")
    description_clean = " ".join(BeautifulSoup(description_raw, "html.parser").get_text(separator=" ").split()) if description_raw else ""
    base_price = product.get('price', 0) / 100
    product_rows = []

    for v in product.get("variants", []):
        item = {
            'ID': product.get('id'),
            'Product': product.get('title'),
            'Variant': v.get('title'),
            'Variant ID': v.get('id'),
            'Availability': v.get('available'),
            'Inventory Management': v.get('inventory_management'),
            'Handle': handle,
            "Product URL": f"{domain}/products/{handle}",
            'Price': v.get('price', 0) / 100,
            'Base Price': base_price,
            'SKU': v.get("sku"),
            "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
            "Description": description_clean,
            "Brand": brand
        }
        product_rows.append(item)
    return product_rows

# --- Main Refactored Function ---

def scrape_website(website):
    all_product_data = []
    all_handles = set()
    page = 1
    
    session, domain, base_url = create_session(website)
    
    # Extract brand once outside the loop
    domain_name = urlparse(domain).netloc.replace("www.", "")
    brand = domain_name.split(".")[0]
    if brand == 'me':
        brand = 'housebabylon'

    while True:
        url = f"{base_url}?page={page}"
        print(f"Fetching Page {page}: {url}")
        
        html = fetch_page(session, url)
        if not html:
            break
            
        new_handles = extract_new_handles(html, all_handles)
        if not new_handles:
            print(f"No new handles found on page {page}. Finishing...")
            break
        
        print(f"Found {len(new_handles)} new products. Scraping details...")
        
        for handle in new_handles:
            all_handles.add(handle)
            product = fetch_product_details(session, domain, handle)
            
            if product:
                product_rows = parse_product(product, domain, handle, brand)
                all_product_data.extend(product_rows)
            time.sleep(1) # Rate limiting per product
        
        page += 1
        
    print("\n--- Scrape Process Complete ---")
    
    if all_product_data:
        df = pd.DataFrame(all_product_data)
        print(f"Total variants collected: {len(df)}")
        return df
    
    print("No data was collected.")
    return pd.DataFrame()