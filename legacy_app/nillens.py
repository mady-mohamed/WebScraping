'''
import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

BASE = "https://nillens.com/"
page = 1
all_product_data = [] # MASTER LIST to hold everything
all_handles = set()
failed_handles = []

while True:
    url = f"{BASE}/collections/all?page={page}"
    response = requests.get(url, timeout=5)
    

    if response.status_code == 200:
        print('passed response')
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
    with open("nillens.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_product_data[0].keys())
        writer.writeheader()
        writer.writerows(all_product_data)
    print("Saved nillens.csv")
else:
    print("No data collected.")
'''
import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from functions_nillens import get_handles_from_page, extract_product_data

BASE = "https://nillens.com"

# --- MAIN EXECUTION ---

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
        
        print(f"Found {len(new_handles)} new products. Starting deep scrape...")
        
        # Update our master "seen" set
        all_handles_seen.update(new_handles)
        
        # Scrape the specific data for these new handles
        page_data, page_failed = extract_product_data(BASE, new_handles)
        
        all_product_data.extend(page_data)
        total_failed_handles.extend(page_failed)
        
        print(f"Page {page} complete. Total variants collected: {len(all_product_data)}")
        page += 1

    # Save to CSV
    if all_product_data:
        filename = r"C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\nillens.csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=all_product_data[0].keys())
            writer.writeheader()
            writer.writerows(all_product_data)
        print(f"Successfully saved {len(all_product_data)} variants to {filename}")
    else:
        print("No data collected.")

    if total_failed_handles:
        print(f"Failed handles: {total_failed_handles}")

if __name__ == "__main__":
    main()