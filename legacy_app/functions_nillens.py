import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# Define a standard browser User-Agent to avoid being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

def get_handles_from_page(base_url, page):
    """Scrapes a collection page and returns a set of product handles."""
    url = f"{base_url}/collections/all?page={page}"
    try:
        # Added headers to the request
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: HTTP {response.status_code}")
            return set()
        
        soup = BeautifulSoup(response.text, "html.parser")
        handles = set()
        
        # CHANGED: Use a 'contains' selector (*=) instead of 'starts with' (^=)
        # This catches both relative links (/products/...) and absolute links (https://nillens.com/products/...)
        links = soup.select('a[href*="/products/"]')
        
        for a in links:
            href = a.get("href", "")
            # Ensure we are not grabbing collection links that happen to contain /products/
            if "/products/" in href:
                handle = href.partition('/products/')[-1].split('?')[0].strip('/')
                if handle and "/" not in handle: # Avoid nested paths
                    handles.add(handle)
        
        return handles
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return set()

def clean_html_description(html_content):
    """Helper to convert HTML description into clean plain text."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Join paragraphs with newlines
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    if not paragraphs:
        return soup.get_text(separator="\n", strip=True)
    return "\n".join(paragraphs)

def extract_product_data(base_url, handles):
    """Fetches JSON data for handles and returns a list of variant dictionaries."""
    results = []
    failed = []
    
    for handle in handles:
        handle_url = f'{base_url}/products/{handle}.js'
        
        try:
            # Added headers here as well
            r = requests.get(handle_url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"FAILED {handle}: HTTP {r.status_code}")
                failed.append(handle)
                continue
                
            product = r.json()
            product_url = f'{base_url}/products/{handle}'
            
            raw_description = product.get("description", "")
            clean_description = clean_html_description(raw_description)

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
                    "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                    "Description": clean_description
                }
                results.append(item)
            
            print(f"Successfully scraped: {handle}")
            time.sleep(1)  # Respectful delay
            
        except Exception as e:
            print(f"Error processing {handle}: {e}")
            failed.append(handle)
            
    return results, failed