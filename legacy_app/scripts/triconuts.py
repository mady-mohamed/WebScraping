import csv
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
from functions import *

BASE = "https://www.triconuts.com/"
filename = r'C:\Users\moham\OneDrive\Desktop\WebScraping\legacy_app\output\Triconuts\triconuts.csv'

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