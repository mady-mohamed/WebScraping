import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

BASE = "https://eg.lilly-home.com/"
page = 1
all_product_data = [] # MASTER LIST to hold everything
all_handles = set()
failed_handles = []

while True:
    url = f"{BASE}/collections/all?page={page}"
    response = requests.get(url, timeout=5)
    

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        handles = set()
        
        # Extract clean handles
        for a in soup.select('a[href^="/products/"]'):
            handle = a.get("href", "").partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
                handles.add(handle)

        new_handles = handles - all_handles
        if len(new_handles) == 0: break
        else: all_handles |= new_handles
        print(f"Found {len(new_handles)} handles. Starting deep scrape...")
        
        
        for handle in new_handles:
            product = None
            product_url = None

            for attempt in range(2):
                try:
                    
                    handle_url = f'{BASE}/products/{handle}.js'
                    r = requests.get(handle_url, timeout=20)
                    if r.status_code != 200:
                        raise RuntimeError(f"HTTP {r.status_code}")
                    product = r.json()
                    product_url = f'{BASE}{product.get("url")}'
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f"FAILED {handle}: {e}")
                        failed_handles.append(handle)
                    else:
                        time.sleep(2)  # brief backoff then retry
                        continue
                    
            if product is None: continue
            # Extract variants and keep them in the master list
            for v in product["variants"]:
                current_datetime = datetime.now()
                item = {
                    "Product": product.get("title"),
                    "Variant": v.get("title"),
                    "Price": v.get("price") / 100.0,
                    "Handle": handle,
                    "Variant ID": v.get("id"),
                    "Availability": v.get("available"),
                    "SKU": v.get("sku"),
                    "Product URL": product_url,
                    "Scraped at": current_datetime.strftime("%Y/%m/%d %I:%M:%S %p")
                }
                all_product_data.append(item)
            
            time.sleep(1) 
            

        # Now we can calculate max_rows or total rows easily
        print(f"Scrape Complete. Total variants found: {len(all_product_data)}")
        
        print(f"Page {page}: +{len(new_handles)} new products, total variants so far: {len(all_product_data)}")
    else:
        print(f"Failed to retrieve page: {response.status_code}")
        break
    page += 1

print("Failed handles", failed_handles)

if all_product_data:
    with open("lilly_home.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_product_data[0].keys())
        writer.writeheader()
        writer.writerows(all_product_data)
    print("Saved lilly_home.csv")
else:
    print("No data collected.")
