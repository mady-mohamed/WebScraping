import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import pandas as pd
import re
import networkx as nx
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer, util
import numpy as np
import streamlit as st
pattern = r"https?://([^.]+)\.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
}
# Load the model once at the top of the script to save memory
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')

def assign_product_category(row):
    # (Existing keyword logic remains the same as previous step)
    title = str(row['Product']).lower()
    desc = str(row['Description']).lower()
    categories = {
        'baby_kids': ['baby', 'newborn', 'swaddle', 'toddler', 'kids', '0-2y', '3-5y', 'romper', 'onesie', 'pacifier', 'nursery', 'bib', 'silicone', 'diaper'],
        'bedding': ['bed linen', 'duvet', 'sheet', 'pillowcase', 'fitted', 'flat', 'thread count', 'sateen', 'quilt', 'blanket', 'bedspread', 'comforter', 'mattress topper', 'percale'],
        'bathroom': ['towel', 'bath mat', 'bathmat', 'bathrobe', 'robe', 'face towel', 'hand towel', 'body towel', 'velour', 'jacquard'],
        'dining': ['tablecloth', 'table cloth', 'napkin', 'placemat', 'coasters', 'dinner plate', 'dessert plate', 'serving plate', 'plate set', 'napking ring', 'cutlery'],
        'kitchen': ['mug', 'bowl', 'cup', 'tumbler', 'glass', 'jug', 'pitcher', 'coffee maker', 'espresso', 'cake cover', 'serving bowl', 'salad bowl', 'pottery', 'clay pot', 'jar'],
        'clothing': ['shirt', 't-shirt', 'sweatshirt', 'socks', 'shorts', 'polo', 'sweater', 'hat', 'kaftan', 'dress', 'blouse', 'pants', 'leggings', 'cardigan', 'jacket', 'coat', 'fez', 'joggers'],
        'loungeware': ['pyjama', 'pyjamas', 'pijama', 'sleepwear', 'night dress', 'homewear', 'chemise', 'underwear', 'bra'],
        'home_decor': ['candle', 'rug', 'mirror', 'ashtray', 'cushion', 'throw blanket', 'milano', 'orchid', 'leno', 'tray', 'basket', 'sculpture', 'vase'],
        'storage': ['tote bag', 'bag', 'pouch', 'bonbonniere', 'organizer', 'box', 'holder']
    }
    multipliers = {'baby_kids': 100, 'storage': 80, 'bedding': 60, 'bathroom': 60, 'dining': 50, 'kitchen': 50, 'loungeware': 40, 'clothing': 30, 'home_decor': 20}
    scores = {cat: 0 for cat in categories}
    triggers = {cat: [] for cat in categories}
    for cat, keywords in categories.items():
        m = multipliers.get(cat, 1)
        for word in keywords:
            pattern = rf'\b{word}\b'
            if re.search(pattern, title):
                scores[cat] += (10 * m)
                triggers[cat].append(f"Title:{word}")
            elif re.search(pattern, desc):
                scores[cat] += (1 * m)
                triggers[cat].append(f"Desc:{word}")
    if not scores or max(scores.values()) == 0:
        return 'other', ''
    best_cat = max(scores, key=scores.get)
    return best_cat, ", ".join(triggers[best_cat])

def clean_df(df):
    if df.empty:
        return df

    # 1. Deduplicate and Categorize (Coarse)
    df = df.drop_duplicates(subset=['ID']).copy()
    df[['Category', 'Category Evidence']] = df.apply(
        lambda row: pd.Series(assign_product_category(row)), axis=1
    )
    
    # 2. Prepare for Clustering
    df['Canonical Text'] = df['Product'].astype(str) + " " + df['Description'].fillna('').astype(str)
    df['Cluster ID'] = "unmatched" # Default
    
    model = load_model()
    threshold = 0.7
    k_neighbors = 5
    
    # 3. Loop through each Category to cluster locally
    unique_categories = df['Category'].unique()
    global_cluster_counter = 0
    
    for cat in unique_categories:
        cat_mask = df['Category'] == cat
        df_cat = df[cat_mask].copy()
        
        if len(df_cat) < 2:
            continue
            
        # Semantic similarity
        embeddings = model.encode(list(df_cat["Canonical Text"]), normalize_embeddings=True)
        sim_matrix = util.cos_sim(embeddings, embeddings).numpy()
        
        # Build Graph
        G = nx.Graph()
        G.add_nodes_from(range(len(df_cat)))
        
        for i in range(len(sim_matrix)):
            # Get top K similar indices (excluding self)
            indices = np.argsort(sim_matrix[i])[-(k_neighbors+1):-1]
            for idx in indices:
                if sim_matrix[i][idx] >= threshold:
                    G.add_edge(i, idx)
        
        # Find Connected Components
        clusters = list(nx.connected_components(G))
        
        for cluster in clusters:
            if len(cluster) >= 2: # Only group if more than 1 item matches
                global_cluster_counter += 1
                # Map local cluster indices back to original DF indexes
                original_indices = df_cat.index[list(cluster)]
                df.loc[original_indices, 'Cluster ID'] = f"temp_{global_cluster_counter}"

    # 4. RE-RANK IDs by Frequency (Requested: 1 = Largest cluster)
    # Filter out 'unmatched' before ranking
    clustered_items = df[df['Cluster ID'] != "unmatched"]
    if not clustered_items.empty:
        order = clustered_items['Cluster ID'].value_counts().index.tolist()
        rank_map = {old_id: i + 1 for i, old_id in enumerate(order)}
        df['Cluster ID'] = df['Cluster ID'].map(lambda x: rank_map.get(x, 0)) # Unmatched items become 0
    else:
        df['Cluster ID'] = 0

    return df[[
        'Brand', 'Product', 'Category', 'Cluster ID', 'Price', 
        'SKU', 'Product URL', 'Description', 'Category Evidence'
    ]]

def scrape_website(website):
    all_product_data = []
    all_handles = set()
    failed_handles = []
    page = 1
    
    session = requests.Session()
    session.headers.update(HEADERS)
    
    DOMAIN = website.rstrip('/')
    base_url = f"{DOMAIN}/collections/all"
    
    while True:
        url = f"{base_url}?page={page}"
        print(f"Fetching Page {page}: {url}")
        
        try:
            response = session.get(url, timeout=15)
            if response.status_code != 200:
                print(f"Stop: Reached end or error (Status {response.status_code})")
                break
        except Exception as e:
            print(f"Request failed: {e}")
            break
        
        soup = BeautifulSoup(response.text, "html.parser")
        current_page_handles = set()
        
        for a in soup.select('a[href*="/products/"]'):
            href = a.get("href", "")
            handle = href.partition('/products/')[-1].split('?')[0].strip('/')
            if handle:
                current_page_handles.add(handle)
        
        new_handles_on_page = current_page_handles - all_handles
        if not new_handles_on_page:
            print(f"No new handles found on page {page}. Finishing...")
            break
        
        print(f"Found {len(new_handles_on_page)} new products. Scraping details...")
        
        for handle in new_handles_on_page:
            all_handles.add(handle)
            product = None
            json_url = f'{DOMAIN}/products/{handle}.js'
            
            for attempt in range(2):
                try:
                    r = session.get(json_url, timeout=20)
                    if r.status_code == 200:
                        product = r.json()
                        break
                    else:
                        time.sleep(1)
                except Exception as e:
                    if attempt == 1:
                        print(f"  FAILED {handle}: {e}")
                        failed_handles.append(handle)
                    time.sleep(2)
            
            if product:
                product_id = product.get('id')
                title = product.get('title')
                base_price = product.get('price', 0) / 100
                
                description_raw = product.get('description', "")
                description_clean = " ".join(BeautifulSoup(description_raw, "html.parser").get_text(separator=" ").split()) if description_raw else ""

                for v in product.get("variants", []):
                    match = re.search(pattern, DOMAIN)
                    domain_name = urlparse(DOMAIN).netloc.replace("www.", "")
                    brand = domain_name.split(".")[0]
                    if brand == 'me':
                        brand = 'housebabylon'
                    item = {
                        'ID': product_id,
                        'Product': title,
                        'Variant': v.get('title'),
                        'Variant ID': v.get('id'),
                        'Availability': v.get('available'),
                        'Inventory Management': v.get('inventory_management'),
                        'Handle': handle,
                        "Product URL": f"{DOMAIN}/products/{handle}",
                        'Price': v.get('price', 0) / 100,
                        'Base Price': base_price,
                        'SKU': v.get("sku"),
                        "Scraped at": datetime.now().strftime("%Y/%m/%d %I:%M:%S %p"),
                        "Description": description_clean,
                        "Brand": brand
                    }
                    all_product_data.append(item)
            
            time.sleep(0.2)
        
        page += 1
        
    print("\n--- Scrape Process Complete ---")
    
    # Create and return the DataFrame
    if all_product_data:
        df = pd.DataFrame(all_product_data)
        print(f"Total variants collected: {len(df)}")
        return df
    else:
        print("No data was collected.")
        return pd.DataFrame() # Return empty DataFrame
