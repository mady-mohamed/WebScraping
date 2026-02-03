# import csv
# import requests
# from bs4 import BeautifulSoup
# import time
# from datetime import datetime

# def get_handles_from_page(base_url, page):
#     """Scrapes a collection page and returns a set of product handles."""
#     url = f"{base_url}/collections/all?page={page}"
#     try:
#         response = requests.get(url, timeout=10)
#         if response.status_code != 200:
#             print(f"Failed to retrieve page {page}: {response.status_code}")
#             return set()
        
#         soup = BeautifulSoup(response.text, "html.parser")
#         handles = set()
#         for a in soup.select('a[href^="/products/"]'):
#             # Extract handle and strip query parameters/slashes
#             handle = a.get("href", "").partition('/products/')[-1].split('?')[0].strip('/')
#             if handle:
#                 handles.add(handle)
#         return handles
#     except Exception as e:
#         print(f"Error fetching page {page}: {e}")
#         return set()

# def extract_product_data(base_url, handles):
#     """Fetches JSON data for a list of handles and returns a list of variant dictionaries."""
#     results = []
#     failed = []
    
#     for handle in handles:
#         product = None
#         product_url = None
#         handle_url = f'{base_url}/products/{handle}.js'
        
#         for attempt in range(2):
#             try:
#                 r = requests.get(handle_url, timeout=20)
#                 if r.status_code != 200:
#                     raise RuntimeError(f"HTTP {r.status_code}")
#                 product = r.json()
#                 product_url = f'{base_url}{product.get("url")}'
#                 break
#             except Exception as e:
#                 if attempt == 1:
#                     print(f"FAILED {handle}: {e}")
#                     failed.append(handle)
#                 else:
#                     time.sleep(2)
#                     continue
        
#         if product:
#             for v in product.get("variants", []):
#                 item = {
#                     "Product": product.get("title"),
#                     "Variant": v.get("title"),
#                     "Price": v.get("price") / 100.0,
#                     "Handle": handle,
#                     "Variant ID": v.get("id"),
#                     "Availability": v.get("available"),
#                     "SKU": v.get("sku"),
#                     "Product URL": product_url,
#                     "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
#                     "Product Description:": get_descriptions("https://hebalinens.com", handle) ## this is what I want to do correctly for each product
#                 }
#                 results.append(item)
#             time.sleep(1)  # Respectful delay
            
#     return results, failed

# def get_descriptions(base_url, handles):
#     '''
#     Outer HTML
#     <div class="pb-8 prose">
                    
#     <p data-mce-fragment="1">Snuggle your little space explorer with our Astronauts Swaddle Towel sets! Super-absorbent and with an adorable astronaut design, our towels wrap your baby in luxurious comfort and security. Make memories of hugs and love each morning they wake up! Let your baby explore the universe in style!</p>
#     <p data-mce-fragment="1">Material: 100% cotton&nbsp;</p>
#     <p data-mce-fragment="1">Set consists of:</p>
#     <p data-mce-fragment="1">1 swaddle towel with hoodie size 100cm x 100cm</p>
#     <p data-mce-fragment="1">1 towel size 50cm width x 70cm length&nbsp;</p>
#     </div>

#     Selector:
#     #shopify-section-template--20234534846755__product-details-tabs > section > div > div > div.md\:py-10 > div.sf__accordion-item.sf-tab-content.md\:opacity-0.open.active > div.sf__accordion-content.max-height-set > div

#     //*[@id="shopify-section-template--20234534846755__product-details-tabs"]/section/div/div/div[2]/div[1]/div[2]/div
#     '''
#     results = []
#     failed = []
    
#     for handle in handles:
#         product = None
#         product_url = None
#         handle_url = f'{base_url}/products/{handle}.js'
        
#         for attempt in range(2):
#             try:
#                 r = requests.get(handle_url, timeout=20)
#                 if r.status_code != 200:
#                     raise RuntimeError(f"HTTP {r.status_code}")
#                 product = r.json()
#                 product_url = f'{base_url}{product.get("url")}'
#                 break
#             except Exception as e:
#                 if attempt == 1:
#                     print(f"FAILED {handle}: {e}")
#                     failed.append(handle)
#                 else:
#                     time.sleep(2)
#                     continue
#         if product:
#             results.append(product.get("description"))
#         time.sleep(1)
#         soup = BeautifulSoup(str(results), "html.parser")
#         texts = [p.get_text(strip=True) for p in soup.find_all('p')]
#         description = "\n".join(texts)
#         return description, failed
                
# handles = get_handles_from_page("https://hebalinens.com", 1)
# descriptions = get_descriptions("https://hebalinens.com", handles)
# print(descriptions[0])

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
    
    for handle in handles:
        handle_url = f'{base_url}/products/{handle}.js'
        
        try:
            r = requests.get(handle_url, timeout=20)
            if r.status_code != 200:
                print(f"FAILED {handle}: HTTP {r.status_code}")
                failed.append(handle)
                continue
                
            product = r.json()
            product_url = f'{base_url}/products/{handle}'
            
            # GET DESCRIPTION HERE: 
            # Shopify JSON already provides the HTML description. 
            # We just need to clean it.
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

# # --- Execution ---
# BASE_URL = "https://hebalinens.com"

# # 1. Get handles
# print("Fetching handles...")
# handles = get_handles_from_page(BASE_URL, 1)
# print(f"Found {len(handles)} handles.")

# # 2. Extract data (including descriptions)
# print("Extracting data...")
# all_data, failed_handles = extract_product_data(BASE_URL, handles)
