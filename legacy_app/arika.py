import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

# The list of URLs you want to scrape
CATEGORIES = [
    "https://ariika.com/pages/bed-sheets",
    "https://ariika.com/pages/bed-fillers",
    "https://ariika.com/collections/mattresses",
    "https://ariika.com/pages/quilts-blanket"
]

all_product_data = []  # MASTER LIST to hold everything
all_handles = set()    # To avoid scraping the same product twice
failed_handles = []

# Headers to look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}

for base_url in CATEGORIES:
    category_name = base_url.split('/')[-1]
    print(f"\n--- Starting Category: {category_name} ---")
    
    page = 1
    while True:
        # Construct pagination URL
        # Note: Shopify pages usually use ?page=X, but some custom /pages/ might not. 
        # The 'if len(new_handles) == 0: break' logic handles this.
        url = f"{base_url}?page={page}"
        print(f"Fetching Page {page}: {url}")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code != 200:
                print(f"Stop: Reached end or error (Status {response.status_code})")
                break
        except Exception as e:
            print(f"Request failed: {e}")
            break

        soup = BeautifulSoup(response.text, "html.parser")
        current_page_handles = set()
        
        # Extract product handles from links
        for a in soup.select('a[href*="/products/"]'):
            href = a.get("href", "")
            # Clean handle: extract text after /products/ and before any ?
            handle = href.partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
                current_page_handles.add(handle)

        # Check if we found any products we haven't seen before
        new_handles_on_page = current_page_handles - all_handles
        
        if not new_handles_on_page:
            print(f"No new handles found on page {page}. Moving to next category.")
            break

        print(f"Found {len(new_handles_on_page)} new products. Scraping details...")
        
        for handle in new_handles_on_page:
            all_handles.add(handle)
            product = None
            
            # Try to get JSON data for the product
            for attempt in range(2):
                try:
                    json_url = f'https://ariika.com/products/{handle}.js'
                    r = requests.get(json_url, headers=HEADERS, timeout=20)
                    
                    if r.status_code == 200:
                        product = r.json()
                        break
                    else:
                        time.sleep(1)
                except Exception as e:
                    if attempt == 1:
                        print(f"  FAILED {handle}: {e}")
                        failed_handles.append(handle)
                    else:
                        time.sleep(2)
            
            if product:
                product_full_url = f"https://ariika.com/products/{handle}"
                for v in product.get("variants", []):
                    item = {
                        "Category": category_name,
                        "Product": product.get("title"),
                        "Variant": v.get("title"),
                        "Price": v.get("price") / 100.0,
                        "Handle": handle,
                        "Variant ID": v.get("id"),
                        "Availability": v.get("available"),
                        "SKU": v.get("sku"),
                        "Product URL": product_full_url,
                        "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p")
                    }
                    all_product_data.append(item)
            
            # Respectful delay between product requests
            time.sleep(0.5)

        page += 1

print("\n--- Scrape Process Complete ---")
print(f"Total variants collected: {len(all_product_data)}")
print(f"Failed handles: {failed_handles}")

# Save to CSV
if all_product_data:
    filename = "ariika_bedding.csv"
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_product_data[0].keys())
        writer.writeheader()
        writer.writerows(all_product_data)
    print(f"Successfully saved to {filename}")
else:
    print("No data was collected.")