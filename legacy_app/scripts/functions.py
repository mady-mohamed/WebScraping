'''
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
            handle = a.get("href", "").partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
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
    # Find all paragraphs and join them with newlines
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    if not paragraphs:
        # Fallback if there are no <p> tags
        return soup.get_text(separator="\n", strip=True)
    return "\n".join(paragraphs)

def extract_product_data(base_url, handles):
    """Fetches JSON data for handles and returns a list of variant dictionaries."""
    results = []
    failed = []
    
    # Headers should be defined or passed in
    HEADERS = {'User-Agent': 'Mozilla/5.0'} 
    
    for handle in handles:
        handle_url = f'{base_url}/products/{handle}.js'
        
        try:
            r = requests.get(handle_url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"FAILED {handle}: HTTP {r.status_code}")
                failed.append(handle)
                continue
                
            product = r.json()
            product_url = f'{base_url}/products/{handle}'
            
            # Extract descriptions
            raw_description = product.get("description", "")
            # Assuming clean_html_description is defined elsewhere
            clean_description = clean_html_description(raw_description) if 'clean_html_description' in globals() else raw_description
            
            # Map option names for easy lookup (e.g., {0: "Size", 1: "Color"})
            option_names = {i: opt.get("name") for i, opt in enumerate(product.get("options", []))}
                    
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
                    'Weight': v.get('weight'),
                    'Inventory Management': v.get('inventory_management'),
                    "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                    "Description": clean_description
                }
                
                # Correctly map the specific values to this variant
                # Shopify stores variant values in option1, option2, option3
                for i in range(1, 4):
                    opt_key = f"option{i}"
                    if v.get(opt_key):
                        label = option_names.get(i-1, f"Option {i}")
                        item[label] = v.get(opt_key)

                results.append(item)
            
            print(f"Successfully scraped: {handle}")
            time.sleep(1)  # Respectful delay
            
        except Exception as e:
            print(f"Error processing {handle}: {e}")
            failed.append(handle)
            
    return results, failed

def deep_scrape(new_handles, all_handles_seen, all_product_data, total_failed_handles, page):
    print(f"Found {len(new_handles)} new products. Starting deep scrape...")
        
    # Update our master "seen" set
    all_handles_seen.update(new_handles)
    
    # Scrape the specific data for these new handles
    page_data, page_failed = extract_product_data(BASE, new_handles)
    
    all_product_data.extend(page_data)
    total_failed_handles.extend(page_failed)
    
    print(f"Page {page} complete. Total variants collected: {len(all_product_data)}")

def save_to_csv(all_product_data, filename):
    if all_product_data:
        # 1. Identify every unique key present in ANY of the dictionaries
        all_keys = set()
        for entry in all_product_data:
            all_keys.update(entry.keys())
        
        # Convert set to a sorted list so columns are consistent
        fieldnames = sorted(list(all_keys))

        with open(filename, "w", newline="", encoding="utf-8") as f:
            # 2. Use the comprehensive list of fieldnames
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_product_data)
            
        print(f"Successfully saved {len(all_product_data)} variants to {filename}")
    else:
        print("No data collected.")
'''
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
            handle = a.get("href", "").partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
                handles.add(handle)
        return handles
    except Exception as e:
        print(f"Error fetching page {page}: {e}")
        return set()

def clean_html_description(html_content):
    """Helper to convert HTML description into clean plain text with no newlines."""
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract text from paragraphs and join them with a space instead of a newline
    paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
    
    if not paragraphs:
        # If no <p> tags, get all text using space as a separator for block elements
        text = soup.get_text(separator=" ", strip=True)
    else:
        text = " ".join(paragraphs)
    
    # Final cleanup: Replace any actual newline or carriage return characters with a space
    # and collapse multiple spaces into one
    clean_text = text.replace('\n', ' ').replace('\r', ' ')
    return " ".join(clean_text.split())

def extract_product_data(base_url, handles):
    """Fetches JSON data for handles and returns a list of variant dictionaries."""
    results = []
    failed = []
    HEADERS = {'User-Agent': 'Mozilla/5.0'} 
    
    for handle in handles:
        handle_url = f'{base_url}/products/{handle}.js'
        try:
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
                    "Handle": handle,
                    "Price": v.get("price") / 100.0,
                    "SKU": v.get("sku"),
                    "Availability": v.get("available"),
                    "Variant Title": v.get("title"),
                    "Variant ID": v.get("id"),
                    "Weight": v.get("weight"),
                    "Inventory Management": v.get("inventory_management"),
                    "Product URL": product_url,
                    "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                    "Description": clean_description
                }
                results.append(item)
            
            print(f"Successfully scraped: {handle}")
            time.sleep(0.5)
            
        except Exception as e:
            print(f"Error processing {handle}: {e}")
            failed.append(handle)
            
    return results, failed

def deep_scrape(base_url, new_handles, all_handles_seen, all_product_data, total_failed_handles, page):
    print(f"Found {len(new_handles)} new products. Starting deep scrape...")
    all_handles_seen.update(new_handles)
    page_data, page_failed = extract_product_data(base_url, new_handles)
    all_product_data.extend(page_data)
    total_failed_handles.extend(page_failed)
    print(f"Page {page} complete. Total variants collected: {len(all_product_data)}")

def save_to_csv(all_product_data, filename):
    if not all_product_data:
        print("No data collected.")
        return

    # Define a specific order for the columns
    fieldnames = [
        "Product", "Handle", "Price", "SKU", "Availability", 
        "Variant Title", "Variant ID",  "Weight", "Inventory Management", 
        "Product URL", "Scraped at", "Description"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(all_product_data)
            
    print(f"Successfully saved {len(all_product_data)} variants to {filename}")