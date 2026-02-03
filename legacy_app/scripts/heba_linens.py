import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from functions import get_handles_from_page, extract_product_data

BASE = "https://hebalinens.com"

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
        filename = "legacy_app\heba.csv"
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