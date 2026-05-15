import sqlite3
import pandas as pd

DB_PATH = "st_app/products.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # REMOVED cluster_id from here
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            product TEXT,
            price REAL,
            sku TEXT,
            product_url TEXT,
            description TEXT,
            brand TEXT,
            category TEXT,
            category_evidence TEXT,
            scraped_at TEXT
        )
        """)
    conn.commit()
    conn.close()

def save_products(df):
    conn = get_connection()
    
    # REMOVED Cluster ID from the rename dictionary
    df_to_save = df.rename(columns={
        "ID": "id",
        "Product": "product",
        "Price": "price",
        "SKU": "sku",
        "Product URL": "product_url",
        "Description": "description",
        "Brand": "brand",
        "Category": "category",
        "Category Evidence": "category_evidence"
    })
    
    df_to_save["scraped_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # REMOVED cluster_id from this list AND fixed the missing comma after brand
    df_to_save[
        [
            "id",
            "product",
            "price",
            "sku",
            "product_url",
            "description",
            "brand",
            "category",
            "category_evidence",
            "scraped_at"
        ]
    ].to_sql("products", conn, if_exists="replace", index=False)
    
    conn.close()
    
def load_products():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return df