from anyio import Semaphore
from openai import timeout
import requests, asyncio, aiohttp
import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import networkx as nx
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer, util

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
        # handle = href.partition('/products/')[-1].split('?')[0].strip('/')
        handle = href.partition('/products/')[-1].split('?')[0].split('#')[0].strip('/')
        if handle:
            current_page_handles.add(handle)
    
    new_handles = current_page_handles - all_handles
    return new_handles

# # Async translation
# async def fetch_product_details_async(session, domain, handle, semaphore):
#     json_url = f'{domain}/products/{handle}.js'
    
#     for attempt in range(2):
#         try:
#             async with semaphore:
#                 async with session.get(json_url, timeout=20) as response:
#                     if response.status == 200:
#                         await asyncio.sleep(1)
#                         return handle, await response.json(content_type=None)
#         except Exception as e:
#             print(f"Failed product {handle}: {e}")
#         await asyncio.sleep(1)
#     return handle, None

async def fetch_product_details_async(session, domain, handle, semaphore):
    json_url = f"{domain}/products/{handle}.js"

    async with semaphore:
        await asyncio.sleep(0.5)
        try:
            async with session.get(json_url, timeout=20) as response:

                if response.status == 200:
                    data = await response.json(content_type=None)
                    return handle, data, None

                return handle, None, f"HTTP {response.status}"

        except Exception as e:
            return handle, None, str(e)

async def fetch_many_products(domain, handles, max_retries=5):
    retry_queue = list(handles)
    sucessful_results = []
    failed_results = []
    
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        semaphore = asyncio.Semaphore(3)
        
        for attempt in range(1, max_retries + 1):
            if not retry_queue:
                break
            
            print(f"Attempt {attempt}: fetching {len(retry_queue)} products")
            
            tasks = [
                fetch_product_details_async(session, domain, handle, semaphore)
                for handle in retry_queue
            ]
            
            results = await asyncio.gather(*tasks)
            
            retry_queue = []
            
            for handle, product, error in results:
                if product:
                    sucessful_results.append((handle, product))
                else:
                    print(f"Retry needed for {handle}: {error}")
                    retry_queue.append(handle)
            
            await asyncio.sleep(2*attempt)
            
        if retry_queue:
            failed_results.extend(retry_queue)
            
    if failed_results:
        print(f'Failed after retries: {failed_results}')
        
    return sucessful_results

# async def fetch_many_products(domain, handles):
#     async with aiohttp.ClientSession(headers=HEADERS) as session:
#         semaphore = asyncio.Semaphore(5)
#         tasks = [
#             fetch_product_details_async(session, domain, handle, semaphore)
#             for handle in handles
#         ]
        
#         return await asyncio.gather(*tasks)

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

@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


def assign_product_category(row):
    title = str(row["Product"]).lower()
    desc = str(row["Description"]).lower()

    categories = {
        "baby_kids": [
            "baby", "newborn", "swaddle", "toddler", "kids", "0-2y", "3-5y",
            "romper", "onesie", "pacifier", "nursery", "bib", "silicone", "diaper"
        ],
        "bedding": [
            "bed linen", "duvet", "sheet", "pillowcase", "fitted", "flat",
            "thread count", "sateen", "quilt", "blanket", "bedspread",
            "comforter", "mattress topper", "percale"
        ],
        "bathroom": [
            "towel", "bath mat", "bathmat", "bathrobe", "robe", "face towel",
            "hand towel", "body towel", "velour", "jacquard"
        ],
        "dining": [
            "tablecloth", "table cloth", "napkin", "placemat", "coasters",
            "dinner plate", "dessert plate", "serving plate", "plate set",
            "napking ring", "cutlery"
        ],
        "kitchen": [
            "mug", "bowl", "cup", "tumbler", "glass", "jug", "pitcher",
            "coffee maker", "espresso", "cake cover", "serving bowl",
            "salad bowl", "pottery", "clay pot", "jar"
        ],
        "clothing": [
            "shirt", "t-shirt", "sweatshirt", "socks", "shorts", "polo",
            "sweater", "hat", "kaftan", "dress", "blouse", "pants",
            "leggings", "cardigan", "jacket", "coat", "fez", "joggers"
        ],
        "loungeware": [
            "pyjama", "pyjamas", "pijama", "sleepwear", "night dress",
            "homewear", "chemise", "underwear", "bra"
        ],
        "home_decor": [
            "candle", "rug", "mirror", "ashtray", "cushion", "throw blanket",
            "milano", "orchid", "leno", "tray", "basket", "sculpture", "vase"
        ],
        "storage": [
            "tote bag", "bag", "pouch", "bonbonniere", "organizer", "box", "holder"
        ],
    }

    multipliers = {
        "baby_kids": 100,
        "storage": 80,
        "bedding": 60,
        "bathroom": 60,
        "dining": 50,
        "kitchen": 50,
        "loungeware": 40,
        "clothing": 30,
        "home_decor": 20,
    }

    scores = {cat: 0 for cat in categories}
    triggers = {cat: [] for cat in categories}

    for cat, keywords in categories.items():
        multiplier = multipliers.get(cat, 1)

        for word in keywords:
            pattern = rf"\b{re.escape(word)}\b"

            if re.search(pattern, title):
                scores[cat] += 10 * multiplier
                triggers[cat].append(f"Title:{word}")

            elif re.search(pattern, desc):
                scores[cat] += 1 * multiplier
                triggers[cat].append(f"Desc:{word}")

    if max(scores.values()) == 0:
        return "other", ""

    best_cat = max(scores, key=scores.get)
    return best_cat, ", ".join(triggers[best_cat])


def clean_df(df):
    if df.empty:
        return df

    df = df.drop_duplicates(subset=["ID"]).copy()

    df[["Category", "Category Evidence"]] = df.apply(
        lambda row: pd.Series(assign_product_category(row)),
        axis=1
    )

    df["Canonical Text"] = (
        df["Product"].astype(str)
        + " "
        + df["Description"].fillna("").astype(str)
    )

    df["Cluster ID"] = "unmatched"

    model = load_model()
    threshold = 0.7
    k_neighbors = 3

    global_cluster_counter = 0

    for cat in df["Category"].unique():
        cat_mask = df["Category"] == cat
        df_cat = df[cat_mask].copy()

        if len(df_cat) < 2:
            continue

        embeddings = model.encode(
            list(df_cat["Canonical Text"]),
            normalize_embeddings=True
        )

        sim_matrix = util.cos_sim(embeddings, embeddings).numpy()

        graph = nx.Graph()
        graph.add_nodes_from(range(len(df_cat)))

        for i in range(len(sim_matrix)):
            indices = np.argsort(sim_matrix[i])[-(k_neighbors + 1):-1]

            for idx in indices:
                if sim_matrix[i][idx] >= threshold:
                    graph.add_edge(i, idx)

        clusters = list(nx.connected_components(graph))

        for cluster in clusters:
            if len(cluster) >= 2:
                global_cluster_counter += 1
                original_indices = df_cat.index[list(cluster)]
                df.loc[original_indices, "Cluster ID"] = f"temp_{global_cluster_counter}"

    clustered_items = df[df["Cluster ID"] != "unmatched"]

    if not clustered_items.empty:
        order = clustered_items["Cluster ID"].value_counts().index.tolist()
        rank_map = {old_id: i + 1 for i, old_id in enumerate(order)}

        df["Cluster ID"] = df["Cluster ID"].map(
            lambda x: rank_map.get(x, 0)
        )
    else:
        df["Cluster ID"] = 0

    df["Inventory Management"] = "shopify"
    df = df.drop_duplicates(subset=['ID'])

    return df[
        [
            "Product", 
            "Price", 
            "Inventory Management", 
            "SKU", 
            "Product URL", 
            "Description", 
            "ID",
            "Brand",
            "Category Evidence", 
            "Category", 
            "Cluster ID"
        ]
    ]

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
        
        all_handles.update(new_handles)
        
        results = asyncio.run(fetch_many_products(domain, new_handles))
        
        for handle, product in results:
            if product:
                product_rows = parse_product(product, domain, handle, brand)
                all_product_data.extend(product_rows)
        
        page += 1
        
    print("\n--- Scrape Process Complete ---")
    
    if all_product_data:
        df = pd.DataFrame(all_product_data)
        print(f"Total variants collected: {len(df)}")
        return df
    
    print("No data was collected.")
    return pd.DataFrame()