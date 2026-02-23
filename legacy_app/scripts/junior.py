import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from functions import *

BASE = "https://junior-tex.com/"
filename = r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Junior\junior.csv'

def get_handles_from_page(base_url, page):
    """Scrapes a collection page and returns a set of product handles."""
    # Shopify usually uses /collections/all
    url = f"{base_url}/collections/all?page={page}"
    
    # Identify as a real browser
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: {response.status_code}")
            return set()
        
        soup = BeautifulSoup(response.text, "html.parser")
        handles = set()
        
        # Look for ANY link containing /products/
        # This is more robust than href^ (starts with)
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/products/' in href:
                # Extract the handle (part after /products/)
                handle = href.split('/products/')[-1].split('?')[0].strip('/')
                if handle:
                    handles.add(handle)
        
        print(f"Found {len(handles)} handles on page {page}.")
        return handles
        
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return set()
    
def get_handles_from_json(base_url, page):
    """Fetches product handles using Shopify's built-in JSON API."""
    # Shopify allows up to 250 products per page via JSON
    url = f"{base_url}/products.json?limit=250&page={page}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        products = data.get('products', [])
        handles = {p['handle'] for p in products}
        
        return handles
    except Exception as e:
        print(f"JSON error: {e}")
        return set()

def main():
    page = 1
    all_product_data = []
    all_handles_seen = set()
    total_failed_handles = []

    print("Starting Scrape...")

    while True:
        print(f"Scanning Page {page} for handles...")
        handles_on_page = get_handles_from_page(BASE, page)
        
        # Determine which handles are actually new
        new_handles = handles_on_page - all_handles_seen
        
        if not new_handles:
            print("No new handles found. Ending search.")
            break
        
        deep_scrape(BASE, new_handles, all_handles_seen, all_product_data, total_failed_handles, page)
        page += 1

    # Save to CSV
    save_to_csv(all_product_data, filename)

    if total_failed_handles:
        print(f"Failed handles: {total_failed_handles}")

if __name__ == "__main__":
    main()